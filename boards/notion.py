"""Notion sync (API version 2025-09-03: pages live in data sources).

Rules: the engine only creates rows and fills in empty fields. It never writes Status after a
row exists, and never writes Status changed. Every row carries a Key, so reruns never duplicate.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
IDS_FILE = Path("notion_ids.json")

STATUS = {
    "Hackathons": ["New", "Shortlist", "Applying", "Building", "Submitted", "Skipped"],
    "Research": ["New", "Reading", "Pursuing", "Drafting", "Submitted", "Parked"],
    "Jobs": ["New", "Shortlist", "Drafted", "Applied", "Interview", "Offer", "Closed"],
}


def _select(options):
    return {"select": {"options": [{"name": o} for o in options]}}


def _common(board: str) -> dict:
    return {
        "Status": _select(STATUS[board]),
        "Status changed": {"date": {}},
        "Score": {"number": {}},
        "URL": {"url": {}},
        "Flags": {"multi_select": {}},
        "Found": {"date": {}},
        "Key": {"rich_text": {}},
    }


def schemas() -> dict[str, dict]:
    """Database name -> properties. Title property is always "Name"."""
    return {
        "Hackathons": {"Name": {"title": {}}, **_common("Hackathons"),
                       "Deadline": {"date": {}}, "Dates": {"date": {}},
                       "Format": _select(["Online", "In person", "Hybrid"]),
                       "Host": {"rich_text": {}}, "Source": {"select": {}},
                       "Why": {"rich_text": {}}, "Plan": {"rich_text": {}}},
        "Research": {"Name": {"title": {}}, **_common("Research"),
                     "Type": _select(["Paper", "Idea", "CFP"]), "Deadline": {"date": {}},
                     "Venue": {"rich_text": {}}, "Summary": {"rich_text": {}},
                     "Verdict": _select(["Go", "Fix", "Kill"])},
        "Jobs": {"Name": {"title": {}}, **_common("Jobs"),
                 "Company": {"rich_text": {}}, "Location": {"rich_text": {}},
                 "Remote": {"checkbox": {}},
                 "Lane": _select(["internship", "residency", "open-application", "applied-ai",
                                  "new-grad", "ai-contract"]),
                 "Why": {"rich_text": {}}, "Contacts": {"rich_text": {}},
                 "Draft": {"rich_text": {}}, "Resume edits": {"rich_text": {}},
                 "Source": {"select": {}}, "Posted": {"date": {}}, "Deadline": {"date": {}}},
        "People": {"Name": {"title": {}}, "Handle/URL": {"url": {}}, "Company": {"rich_text": {}},
                   "Role": {"rich_text": {}}, "Source": {"rich_text": {}},
                   "Source row": {"url": {}}, "Hook": {"rich_text": {}},
                   "Handed off": {"date": {}}, "Key": {"rich_text": {}}},
        "Briefs": {"Name": {"title": {}}, "Week of": {"date": {}}},
        "Engine status": {"Pipeline": {"title": {}}, "Last success": {"date": {}},
                          "Last run": {"date": {}}, "Rows added": {"number": {}},
                          "Scouted": {"number": {}}, "Failed sources": {"rich_text": {}},
                          "Run": {"url": {}}},
    }


# ---------------------------------------------------------------- property builders
def _chunks(text: str, size: int = 1900) -> list[dict]:
    text = text or ""
    return [{"text": {"content": text[i:i + size]}} for i in range(0, min(len(text), size * 50), size)]


def title(text: str) -> dict:
    return {"title": _chunks(text[:1900])}


def rich(text: str) -> dict:
    return {"rich_text": _chunks(text)}


def select(name: str) -> dict:
    return {"select": {"name": name.replace(",", ";")[:100]}} if name else {"select": None}


def multi(names: list[str]) -> dict:
    clean = list(dict.fromkeys(n.replace(",", ";").strip()[:100] for n in names if n and n.strip()))
    return {"multi_select": [{"name": n} for n in clean]}


def day(d: date | None) -> dict:
    return {"date": {"start": d.isoformat()} if d else None}


def page_id_from_url(url_or_id: str) -> str:
    m = re.findall(r"[0-9a-f]{32}", url_or_id.replace("-", ""))
    if not m:
        raise ValueError(f"no Notion page ID in {url_or_id!r}")
    raw = m[-1]
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"


# ---------------------------------------------------------------- client
class Notion:
    def __init__(self, token: str | None = None):
        token = token or os.environ.get("NOTION_TOKEN")
        if not token:
            raise RuntimeError("NOTION_TOKEN is not set")
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}", "Notion-Version": VERSION,
                               "Content-Type": "application/json"})

    def req(self, method: str, path: str, body: dict | None = None) -> dict:
        for attempt in range(4):
            r = self.s.request(method, f"{API}/{path}", json=body, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"Notion {method} {path}: {r.status_code} {r.text[:300]}")
            return r.json()
        raise RuntimeError(f"Notion {method} {path}: gave up after retries")

    def query_all(self, data_source_id: str, body: dict | None = None):
        body = dict(body or {}, page_size=100)
        while True:
            res = self.req("POST", f"data_sources/{data_source_id}/query", body)
            yield from res.get("results", [])
            if not res.get("has_more"):
                return
            body["start_cursor"] = res["next_cursor"]

    def create_page(self, data_source_id: str, properties: dict) -> dict:
        return self.req("POST", "pages", {"parent": {"type": "data_source_id",
                                                     "data_source_id": data_source_id},
                                          "properties": properties})

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self.req("PATCH", f"pages/{page_id}", {"properties": properties})

    # ------------------------------------------------------------ setup
    def setup(self, parent_page: str) -> dict:
        parent = page_id_from_url(parent_page)
        ids: dict[str, dict] = {}
        for name, props in schemas().items():
            db = self.req("POST", "databases", {
                "parent": {"type": "page_id", "page_id": parent},
                "title": [{"text": {"content": name}}],
                "initial_data_source": {"properties": props},
            })
            sources = db.get("data_sources") or self.req("GET", f"databases/{db['id']}")["data_sources"]
            ids[name] = {"database_id": db["id"], "data_source_id": sources[0]["id"]}
        # People.Linked jobs is a relation, so it needs the Jobs data source to exist first.
        self.req("PATCH", f"data_sources/{ids['People']['data_source_id']}", {"properties": {
            "Linked jobs": {"relation": {"data_source_id": ids["Jobs"]["data_source_id"],
                                         "type": "single_property", "single_property": {}}}}})
        return ids


def load_ids(path: Path = IDS_FILE) -> dict:
    if not path.exists():
        raise RuntimeError(f"{path} not found: run the 'Setup Notion' workflow first")
    return json.loads(path.read_text())


def _plain(prop: dict) -> str:
    kind = prop.get("type")
    items = prop.get(kind) if kind in ("rich_text", "title") else None
    return "".join(i.get("plain_text", "") for i in items or [])


def existing_keys(notion: Notion, data_source_id: str) -> dict[str, dict]:
    """Key -> page, for every row already in the database."""
    out = {}
    for page in notion.query_all(data_source_id):
        key = _plain(page.get("properties", {}).get("Key", {}))
        if key:
            out[key] = page
    return out


def job_properties(p, today: date) -> dict:
    props = {
        "Name": title(p.name),
        "Company": rich(p.company),
        "Score": {"number": p.score if p.score is not None else round(p.prescore)},
        "Location": rich(p.location or "unclear"),
        "Remote": {"checkbox": "REMOTE" in p.regions},
        "Lane": select(p.lane),
        "Flags": multi(p.flags),
        "URL": {"url": p.url or None},
        "Why": rich(" · ".join(x for x in [p.why, f"Angle: {p.angle}" if p.angle else ""] if x)),
        "Contacts": rich(p.contacts),
        "Draft": rich(p.draft),
        "Resume edits": rich(p.resume_edits),
        "Source": select(p.source),
        "Posted": day(p.posted),
        "Deadline": day(p.deadline),
        "Found": day(today),
        "Key": rich(p.key),
        "Status": select("New"),  # initial value only; the Bots own it from here on
    }
    return props


def fill_empty(notion: Notion, page: dict, p) -> bool:
    """For a row that already exists, fill Deadline if the engine now knows it and it's empty."""
    current = page.get("properties", {}).get("Deadline", {}).get("date")
    if p.deadline and not current:
        notion.update_page(page["id"], {"Deadline": day(p.deadline)})
        return True
    return False


def sync_jobs(notion: Notion, ids: dict, postings, seen: dict[str, dict], today: date) -> dict:
    ds = ids["Jobs"]["data_source_id"]
    created = filled = 0
    errors = []
    for p in postings:
        try:
            if p.key in seen:
                filled += fill_empty(notion, seen[p.key], p)
                continue
            notion.create_page(ds, job_properties(p, today))
            created += 1
        except RuntimeError as exc:
            errors.append(f"{p.name}: {exc}"[:300])
    return {"created": created, "filled": filled, "errors": errors}


def update_engine_status(notion: Notion, ids: dict, pipeline: str, *, success: bool,
                         rows_added: int, scouted: int, failed: list[str], run_url: str = "") -> None:
    ds = ids["Engine status"]["data_source_id"]
    now = datetime.now(timezone.utc)
    props = {
        "Pipeline": title(pipeline),
        "Last run": {"date": {"start": now.isoformat(timespec="minutes")}},
        "Rows added": {"number": rows_added},
        "Scouted": {"number": scouted},
        "Failed sources": rich(", ".join(failed) or "none"),
        "Run": {"url": run_url or None},
    }
    if success:
        props["Last success"] = {"date": {"start": now.isoformat(timespec="minutes")}}
    rows = list(notion.query_all(ds, {"filter": {"property": "Pipeline",
                                                 "title": {"equals": pipeline}}}))
    if rows:
        notion.update_page(rows[0]["id"], props)
    else:
        notion.create_page(ds, props)
