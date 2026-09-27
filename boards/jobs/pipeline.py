"""Jobs pipeline: ATS Scout + Simplify → Pre-filter → Fit Scorer → Referral Mapper →
Outreach Drafter → Notion."""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

from ..llm import MockLLM, XaiLLM
from ..report import jobs_markdown, write_outputs
from ..sources.ats import FETCHERS, Company, scout_all
from ..sources.simplify import fetch_simplify, parse_simplify
from .crew import draft_outreach, fit_score, map_referrals
from .prefilter import run_prefilter


def _norm(name: str) -> str:
    return re.sub(r"\b(ai|inc|labs?|technologies|corp(oration)?)\b|[^a-z0-9]", "", name.lower())


def fixture_fetchers(root: Path) -> dict:
    """Read ATS responses from <root>/<ats>/<slug>.json instead of the network (tests, demos)."""
    from ..http import FetchError

    def make(ats):
        def fetch(slug):
            f = root / ats / f"{slug}.json"
            if not f.exists():
                raise FetchError(f"404 fixture {f}")
            return json.loads(f.read_text())
        return fetch

    return {ats: (make(ats), parse) for ats, (_, parse) in FETCHERS.items()}


def run(cfg: dict, profile: dict, *, today: date | None = None, dry_run: bool = False,
        mock: bool = False, fixtures: Path | None = None, notion=None, ids: dict | None = None,
        llm=None, log=print) -> dict:
    today = today or date.today()
    jc = cfg["jobs"]
    models = cfg.get("models", {})
    lean = cfg.get("lean", False)

    # ---- scouts
    companies = [Company(**c) for c in jc["companies"]]
    fetchers = fixture_fetchers(fixtures) if fixtures else FETCHERS
    scout = scout_all(companies, fetchers)
    log(f"ATS Scout: {sum(scout.counts.values())} postings from {len(scout.counts)} boards, "
        f"{len(scout.errors)} failed")

    postings = list(scout.postings)
    simplify_counts, simplify_errors = {}, {}
    for src in jc.get("simplify", []):
        try:
            if fixtures:
                f = fixtures / "simplify" / f"{src['source']}.json"
                items = parse_simplify(json.loads(f.read_text()), src["source"],
                                       categories=src.get("categories"), terms=src.get("terms"))
            else:
                items = fetch_simplify(src["url"], src["source"], categories=src.get("categories"),
                                       terms=src.get("terms"))
        except Exception as exc:
            simplify_errors[src["name"]] = str(exc)[:300]
            continue
        simplify_counts[src["name"]] = len(items)
        postings.extend(items)
    log(f"Simplify: {sum(simplify_counts.values())} listings, {len(simplify_errors)} failed")
    tiers = {_norm(c.name): c.tier for c in companies}
    for p in postings:
        if not p.tier:
            p.tier = tiers.get(_norm(p.company), "")

    # ---- seen before (Notion is the truth)
    seen: dict = {}
    if notion is not None and ids is not None:
        from ..notion import existing_keys
        seen = existing_keys(notion, ids["Jobs"]["data_source_id"])
        log(f"Notion: {len(seen)} rows already known")

    # ---- pre-filter
    selected, stats = run_prefilter(postings, cfg=jc, profile=profile, today=today,
                                    seen_keys=set(seen))
    log(f"Pre-filter: {stats.scouted} → {stats.after_seen} unseen → {stats.selected} to score")

    # ---- crew
    llm = llm or (MockLLM() if mock else XaiLLM())
    fit_score(llm, selected, profile, models.get("bulk", "grok-4.3"))
    selected.sort(key=lambda p: -(p.score or 0))
    ref_min = jc.get("referral_min_score_lean", 75) if lean else jc.get("referral_min_score", 0)
    ref_rows = [p for p in selected if (p.score or 0) >= ref_min][: jc.get("referral_top", 5)]
    map_referrals(llm, ref_rows, models.get("search", "grok-4.7"))
    draft_rows = [p for p in selected if (p.score or 0) >= jc.get("draft_min_score", 60)][: jc.get("draft_top", 10)]
    draft_outreach(llm, draft_rows, profile, models.get("bulk", "grok-4.3"),
                   jc.get("draft_max_words", 110))
    cost = llm.usage.cost(cfg.get("prices", {}))
    log(f"Crew: {llm.usage.calls} calls, ≈ ${cost:.3f}")

    # ---- Notion
    sync = None
    if not dry_run and notion is not None:
        from ..notion import sync_jobs, update_engine_status
        sync = sync_jobs(notion, ids, selected, seen, today)
        failed = list(scout.errors) + list(simplify_errors)
        run_url = ""
        if os.environ.get("GITHUB_RUN_ID"):
            run_url = (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                       f"{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
        update_engine_status(notion, ids, "Jobs", success=not sync["errors"] or sync["created"] > 0,
                             rows_added=sync["created"], scouted=stats.scouted, failed=failed,
                             run_url=run_url)
        log(f"Notion: created {sync['created']}, filled {sync['filled']}, {len(sync['errors'])} errors")

    mode = "dry run" + (" · mock LLM" if mock else "") if dry_run else ("live" + (" · mock LLM" if mock else ""))
    md = jobs_markdown(today=today, stats=stats, scout=scout, simplify_counts=simplify_counts,
                       simplify_errors=simplify_errors, rows=selected, sync=sync,
                       usage=llm.usage, cost=cost, mode=mode)
    path = write_outputs(md, selected)
    log(f"Report: {path}")
    all_failed = not scout.counts and not simplify_counts
    return {"stats": stats, "rows": selected, "sync": sync, "cost": cost,
            "ok": not all_failed and not (sync and sync["errors"] and not sync["created"])}
