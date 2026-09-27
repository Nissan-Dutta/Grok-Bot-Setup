from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path


def _cell(text: str, n: int = 90) -> str:
    text = (text or "").replace("|", "/").replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def jobs_markdown(*, today: date, stats, scout, simplify_counts: dict, simplify_errors: dict,
                  rows: list, sync: dict | None, usage, cost: float, mode: str) -> str:
    total_ats = sum(scout.counts.values())
    lines = [
        f"# Jobs run · {today.isoformat()} · {mode}",
        "",
        "## Funnel",
        "",
        f"**{stats.scouted:,}** postings scouted → **{stats.after_dedupe:,}** after de-duplication → "
        f"**{stats.after_lane:,}** in a lane → **{stats.after_location:,}** in a usable location → "
        f"**{stats.after_fresh:,}** fresh → **{stats.after_seen:,}** unseen → **{stats.selected}** scored",
        "",
        "| Lane | Unseen candidates |",
        "| --- | ---: |",
        *[f"| {lane} | {n} |" for lane, n in stats.lanes.most_common()],
        "",
        "Dropped: " + ", ".join(f"{k} {v:,}" for k, v in stats.dropped.most_common()) + ".",
        "",
        "## Top picks",
        "",
        "| # | Score | Lane | Role · Company | Location | Flags |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]
    for i, p in enumerate(rows, 1):
        score = p.score if p.score is not None else f"~{round(p.prescore)}"
        remote = " 🌐" if "REMOTE" in p.regions else ""
        lines.append(f"| {i} | {score} | {p.lane} | [{_cell(p.name, 70)}]({p.url}) | "
                     f"{_cell(p.location or 'unclear', 40)}{remote} | {_cell(', '.join(p.flags), 60)} |")
    lines += ["", "## Sources", "",
              f"- ATS boards: {len(scout.counts)} read, {total_ats:,} postings; "
              f"{len(scout.errors)} failed."]
    for name, n in simplify_counts.items():
        lines.append(f"- {name}: {n:,} active listings in scope.")
    if scout.errors or simplify_errors:
        lines += ["", "<details><summary>Failed sources (each fails on its own)</summary>", ""]
        lines += [f"- **{k}**: {_cell(v, 200)}" for k, v in {**scout.errors, **simplify_errors}.items()]
        lines += ["", "</details>"]
    auto = {k: v for k, v in scout.resolved.items()}
    if auto:
        lines += ["", "<details><summary>Boards read (ATS / slug)</summary>", ""]
        lines += [f"- {k}: {a}/{s} ({scout.counts.get(k, 0)})" for k, (a, s) in sorted(auto.items())]
        lines += ["", "</details>"]
    lines += ["", "## Cost", "",
              f"{usage.calls} model calls · {usage.input_tokens:,} in / {usage.output_tokens:,} out tokens"
              f" · {usage.tool_calls} search calls · **≈ ${cost:.3f}**"
              + (" (mock run: a rough estimate of what a real run would cost)" if "mock" in mode else "")]
    if sync is not None:
        lines += ["", "## Notion", "", f"Created {sync['created']} rows, filled {sync['filled']} empty fields."]
        lines += [f"- ⚠️ {e}" for e in sync.get("errors", [])]
    else:
        lines += ["", "_Dry run: Notion was not touched._"]
    return "\n".join(lines) + "\n"


def write_outputs(markdown: str, rows: list, out_dir: Path = Path("out")) -> Path:
    out_dir.mkdir(exist_ok=True)
    (out_dir / "jobs-report.md").write_text(markdown)
    payload = []
    for p in rows:
        d = asdict(p)
        d["regions"] = sorted(p.regions)
        d["key"] = p.key
        # Drafts, contacts and resume edits go to Notion only, never into Actions artifacts.
        for private in ("description", "draft", "contacts", "resume_edits"):
            d.pop(private, None)
        payload.append(d)
    (out_dir / "jobs-rows.json").write_text(json.dumps(payload, indent=2, default=str))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write(markdown)
    return out_dir / "jobs-report.md"
