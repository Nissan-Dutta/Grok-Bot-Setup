"""Simplify's community-maintained internship and new-grad lists (public JSON on GitHub).

These cover companies not on the target list, including big-tech programs on Workday and
custom career sites that have no public ATS API.
"""
from __future__ import annotations

from ..http import get_json
from ..models import Posting, parse_date


def parse_simplify(data: list, source: str, *, categories: list[str] | None = None,
                   terms: list[str] | None = None) -> list[Posting]:
    cats = {c.lower() for c in categories or []}
    wanted_terms = {t.lower() for t in terms or []}
    out = []
    for item in data or []:
        if not item.get("active") or item.get("is_visible") is False:
            continue
        if cats and (item.get("category") or "").lower() not in cats:
            continue
        item_terms = {t.lower() for t in item.get("terms") or []}
        if wanted_terms and item_terms and not (item_terms & wanted_terms):
            continue
        locations = [loc for loc in item.get("locations") or [] if loc]
        location = ", ".join(locations)
        out.append(Posting(
            source=source,
            source_id=str(item.get("id")),
            company=(item.get("company_name") or "").strip(),
            title=(item.get("title") or "").strip(),
            url=item.get("url", ""),
            location=location,
            remote=any("remote" in loc.lower() for loc in locations),
            employment_type="Intern" if "intern" in source else "",
            posted=parse_date(item.get("date_posted")),
            category=item.get("category") or "",
            hints={
                "sponsorship": item.get("sponsorship") or "",
                "degrees": item.get("degrees") or [],
                "terms": item.get("terms") or [],
            },
        ))
    return out


def fetch_simplify(url: str, source: str, **kwargs) -> list[Posting]:
    return parse_simplify(get_json(url, timeout=60), source, **kwargs)
