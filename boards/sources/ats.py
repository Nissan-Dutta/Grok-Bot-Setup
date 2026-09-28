"""ATS Scout: reads public job boards on Greenhouse, Lever and Ashby.

All three expose unauthenticated JSON APIs. Each company in config.yaml names its ATS and
board slug; `ats: auto` probes all three with the slug candidates and keeps the first board
that returns jobs.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Callable

from ..http import FetchError, get_json
from ..models import Posting, parse_date

GREENHOUSE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
LEVER = "https://api.lever.co/v0/postings/{slug}"
ASHBY = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


@dataclass
class Company:
    name: str
    ats: str = "auto"
    slug: str | list[str] = ""
    tier: str = ""

    @property
    def slugs(self) -> list[str]:
        if isinstance(self.slug, list):
            return self.slug
        if self.slug:
            return [self.slug]
        base = re.sub(r"[^a-z0-9]", "", self.name.lower())
        dashed = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return list(dict.fromkeys([base, dashed, base.removesuffix("ai")]))


@dataclass
class ScoutResult:
    postings: list[Posting] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)      # company -> error
    resolved: dict[str, tuple[str, str]] = field(default_factory=dict)  # company -> (ats, slug)
    counts: dict[str, int] = field(default_factory=dict)


def strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def _is_remote(*texts: str) -> bool:
    return any(re.search(r"\bremote\b|\banywhere\b|distributed", t or "", re.I) for t in texts)


def parse_greenhouse(data: dict, company: Company, slug: str) -> list[Posting]:
    out = []
    for job in data.get("jobs", []):
        loc = (job.get("location") or {}).get("name", "")
        offices = ", ".join(o.get("name", "") for o in job.get("offices") or [] if o.get("name"))
        location = loc or offices
        desc = strip_html(job.get("content", ""))
        out.append(Posting(
            source="greenhouse",
            source_id=f"{slug}/{job['id']}",
            company=company.name,
            title=(job.get("title") or "").strip(),
            url=job.get("absolute_url", ""),
            location=location,
            remote=_is_remote(location),
            posted=parse_date(job.get("first_published") or job.get("updated_at")),
            deadline=parse_date(job.get("application_deadline")),
            description=desc,
            tier=company.tier,
        ))
    return out


def parse_lever(data: list, company: Company, slug: str) -> list[Posting]:
    out = []
    for job in data or []:
        cats = job.get("categories") or {}
        all_locs = cats.get("allLocations") or []
        location = ", ".join(all_locs) if all_locs else cats.get("location", "")
        workplace = job.get("workplaceType", "")
        parts = [job.get("descriptionPlain", ""), job.get("additionalPlain", "")]
        for lst in job.get("lists") or []:
            parts.append(lst.get("text", ""))
            parts.append(strip_html(lst.get("content", "")))
        out.append(Posting(
            source="lever",
            source_id=f"{slug}/{job['id']}",
            company=company.name,
            title=(job.get("text") or "").strip(),
            url=job.get("hostedUrl", ""),
            location=location,
            remote=workplace == "remote" or _is_remote(location),
            employment_type=cats.get("commitment", ""),
            posted=parse_date(job.get("createdAt")),
            description="\n".join(p for p in parts if p).strip(),
            tier=company.tier,
        ))
    return out


def parse_ashby(data: dict, company: Company, slug: str) -> list[Posting]:
    out = []
    for job in data.get("jobs", []):
        if job.get("isListed") is False:
            continue
        secondary = [s.get("location", "") for s in job.get("secondaryLocations") or []]
        location = ", ".join([job.get("location", "")] + [s for s in secondary if s])
        remote = bool(job.get("isRemote")) or job.get("workplaceType") == "Remote" or _is_remote(location)
        out.append(Posting(
            source="ashby",
            source_id=f"{slug}/{job['id']}",
            company=company.name,
            title=(job.get("title") or "").strip(),
            url=job.get("jobUrl", ""),
            location=location,
            remote=remote,
            employment_type=job.get("employmentType", ""),
            posted=parse_date(job.get("publishedAt")),
            description=job.get("descriptionPlain") or strip_html(job.get("descriptionHtml", "")),
            tier=company.tier,
        ))
    return out


def _fetch_greenhouse(slug: str):
    return get_json(GREENHOUSE.format(slug=slug), params={"content": "true"})


def _fetch_lever(slug: str):
    return get_json(LEVER.format(slug=slug), params={"mode": "json"})


def _fetch_ashby(slug: str):
    return get_json(ASHBY.format(slug=slug))


FETCHERS: dict[str, tuple[Callable, Callable]] = {
    "greenhouse": (_fetch_greenhouse, parse_greenhouse),
    "ashby": (_fetch_ashby, parse_ashby),
    "lever": (_fetch_lever, parse_lever),
}


def scout_company(company: Company, fetchers=FETCHERS) -> tuple[list[Posting], tuple[str, str] | None]:
    """Return postings and the (ats, slug) that produced them. Raises FetchError if no board works."""
    atses = list(fetchers) if company.ats == "auto" else [company.ats]
    tried = []
    for ats in atses:
        fetch, parse = fetchers[ats]
        for slug in company.slugs:
            try:
                postings = parse(fetch(slug), company, slug)
            except FetchError as exc:
                tried.append(f"{ats}/{slug}: {exc}")
                continue
            if postings or company.ats != "auto":
                return postings, (ats, slug)
            tried.append(f"{ats}/{slug}: empty")
    raise FetchError("; ".join(tried) or "no board")


def scout_all(companies: list[Company], fetchers=FETCHERS, max_workers: int = 8) -> ScoutResult:
    from concurrent.futures import ThreadPoolExecutor

    result = ScoutResult()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {c.name: pool.submit(scout_company, c, fetchers) for c in companies}
    for name, fut in futures.items():
        try:
            postings, resolved = fut.result()
        except FetchError as exc:
            result.errors[name] = str(exc)[:300]
            continue
        result.postings.extend(postings)
        result.counts[name] = len(postings)
        if resolved:
            result.resolved[name] = resolved
    return result
