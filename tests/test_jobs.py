import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from boards.http import FetchError
from boards.jobs import prefilter as pf
from boards.jobs.pipeline import fixture_fetchers, run
from boards.llm import MockLLM, extract_json
from boards.models import Posting, parse_date
from boards.notion import job_properties, multi, page_id_from_url, rich
from boards.sources.ats import Company, parse_ashby, parse_greenhouse, parse_lever, scout_company
from boards.sources.simplify import parse_simplify

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).parent.parent
TODAY = date(2026, 9, 27)


def load(rel):
    return json.loads((FIX / rel).read_text())


@pytest.fixture
def cfg():
    c = yaml.safe_load((ROOT / "config.yaml").read_text())
    c["jobs"]["companies"] = [
        {"name": "EvalCo", "ats": "greenhouse", "slug": "evalco", "tier": "evals"},
        {"name": "InfraCo", "ats": "auto", "slug": ["nope", "infra"], "tier": "infra"},
        {"name": "AsiaCo", "ats": "lever", "slug": "asiaco", "tier": "asia"},
        {"name": "GoneCo", "ats": "ashby", "slug": "gone", "tier": "lab"},
    ]
    c["jobs"]["simplify"] = [{"name": "Simplify · internships", "source": "simplify-internships",
                              "url": "unused", "categories": ["AI/ML/Data", "Software"],
                              "terms": ["Summer 2027"]}]
    return c


@pytest.fixture
def profile():
    return yaml.safe_load((ROOT / "profile.yaml").read_text())


# ---------------------------------------------------------------- sources
def test_parse_greenhouse_unescapes_html_and_reads_deadline():
    ps = parse_greenhouse(load("greenhouse/evalco.json"), Company("EvalCo", tier="evals"), "evalco")
    p = ps[0]
    assert p.title == "Research Engineer Intern, Evals"
    assert p.deadline == date(2026, 10, 31)
    assert p.posted == date(2026, 9, 24)
    assert "currently enrolled" in p.description and "<p>" not in p.description
    assert ps[2].remote is True and ps[2].location == "Remote - US"


def test_parse_ashby_skips_unlisted_and_joins_locations():
    ps = parse_ashby(load("ashby/infra.json"), Company("InfraCo"), "infra")
    assert [p.source_id for p in ps] == ["infra/a1", "infra/a2"]
    assert ps[0].remote is True
    assert ps[1].location == "San Francisco, Singapore"


def test_parse_lever_epoch_ms_and_lists():
    ps = parse_lever(load("lever/asiaco.json"), Company("AsiaCo"), "asiaco")
    assert ps[0].posted == date(2026, 9, 26)
    assert "Python" in ps[0].description
    assert ps[1].remote is True


def test_auto_probe_skips_missing_boards():
    fetchers = fixture_fetchers(FIX)
    postings, resolved = scout_company(Company("InfraCo", ats="auto", slug=["nope", "infra"]), fetchers)
    assert resolved == ("ashby", "infra") and len(postings) == 2
    with pytest.raises(FetchError):
        scout_company(Company("GoneCo", ats="ashby", slug="gone"), fetchers)


def test_auto_probe_skips_empty_boards_before_finding_jobs():
    fetchers = {
        "greenhouse": (lambda _slug: {"jobs": []}, parse_greenhouse),
        "ashby": (lambda _slug: load("ashby/infra.json"), parse_ashby),
    }
    postings, resolved = scout_company(Company("InfraCo", ats="auto", slug="infra"), fetchers)
    assert resolved == ("ashby", "infra") and len(postings) == 2


def test_explicit_ats_accepts_empty_board_without_error():
    fetchers = {"greenhouse": (lambda _slug: {"jobs": []}, parse_greenhouse)}
    postings, resolved = scout_company(Company("EvalCo", ats="greenhouse", slug="evalco"), fetchers)
    assert postings == [] and resolved == ("greenhouse", "evalco")


def test_simplify_filters_inactive_and_category():
    ps = parse_simplify(load("simplify/simplify-internships.json"), "simplify-internships",
                        categories=["AI/ML/Data", "Software"], terms=["Summer 2027"])
    assert {p.company for p in ps} == {"EvalCo", "BigCo", "EUCo"}
    assert ps[0].hints["sponsorship"] == "Does Not Offer Sponsorship"


def test_parse_date_formats():
    assert parse_date("2026-09-24T12:00:00-04:00") == date(2026, 9, 24)
    assert parse_date(1790400000000) == parse_date(1790400000)
    assert parse_date("") is None and parse_date("not a date") is None


# ---------------------------------------------------------------- pre-filter
def P(title, location="", remote=False, source="greenhouse", **kw):
    return Posting(source=source, source_id=title, company=kw.pop("company", "Co"), title=title,
                   url=kw.pop("url", f"https://x/{title}"), location=location, remote=remote, **kw)


@pytest.mark.parametrize("title,lane", [
    ("Machine Learning Intern", "internship"),
    ("Software Engineer Co-op (Fall 2026)", "internship"),
    ("AI Infra Resident (1-Year Program)", "residency"),
    ("Anthropic Fellows Program, AI Safety", "residency"),
    ("Open Application for Unconventional Talent", "open-application"),
    ("Member of Technical Staff, Exceptional Generalist (Remote)", "open-application"),
    ("New Grad Software Engineer", "new-grad"),
    ("AI Tutor - Coding", "ai-contract"),
    ("Applied AI Engineer", "applied-ai"),
    ("Member of Technical Staff, Inference", "applied-ai"),
    ("Office Manager", ""),
])
def test_lanes(title, lane):
    assert pf.classify_lane(P(title)) == lane


@pytest.mark.parametrize("title,reason", [
    ("Senior Applied AI Engineer", "seniority"),
    ("Staff Machine Learning Engineer", "seniority"),
    ("Member of Technical Staff, Inference", ""),
    ("Research Intern, Staff Team", ""),
    ("Sales Engineer, AI", "function"),
])
def test_exclusions(title, reason):
    p = P(title)
    p.lane = pf.classify_lane(p) or "applied-ai"
    assert pf.exclusion_reason(p) == reason


@pytest.mark.parametrize("loc,remote,expected", [
    ("San Francisco, CA", False, {"US"}),
    ("Remote - US", True, {"US", "REMOTE"}),
    ("Remote", True, {"REMOTE"}),
    ("Remote - Canada", True, {"OTHER"}),
    ("Tokyo, Japan", False, {"JP"}),
    ("Singapore", False, {"SG"}),
    ("London, UK", False, {"OTHER"}),
    ("Canada, United Kingdom, United States", False, {"US", "OTHER"}),
])
def test_regions(loc, remote, expected):
    assert pf.regions_of(loc, remote) == expected


def test_flags_are_attached_not_dropped(profile):
    p = P("ML Intern - PhD", "NYC", description="We are unable to provide visa sponsorship. "
          "Must be currently enrolled. Graduating between December 2026 and June 2027.")
    prof = dict(profile, graduation="2028-05")
    flags = pf.eligibility_flags(p, prof)
    assert "No sponsorship" in flags and "Needs enrollment" in flags and "PhD required" in flags
    assert any(f.startswith("Grad window 2026–2027") for f in flags)


def test_unknown_work_authorization_never_lowers_score(cfg, profile):
    a = P("ML Intern", "NYC")
    a.lane, a.regions = "internship", {"US"}
    b = P("ML Intern", "NYC")
    b.lane, b.regions, b.flags = "internship", {"US"}, ["No sponsorship", "US citizenship / clearance"]
    assert pf.prescore(a, cfg["jobs"], profile, TODAY) == pf.prescore(b, cfg["jobs"], profile, TODAY)
    prof = dict(profile, work_authorization={"us_citizen_or_pr": False, "needs_us_sponsorship": True})
    assert pf.prescore(b, cfg["jobs"], prof, TODAY) < pf.prescore(a, cfg["jobs"], prof, TODAY)


def test_title_relevance_ranks_ai_over_analytics(cfg):
    j = cfg["jobs"]
    assert pf.title_points("AI Agent Evaluations Intern", j) > pf.title_points("Software Intern", j)
    assert pf.title_points("Software Intern", j) > pf.title_points("Operational Analytics Intern", j)


def test_dedupe_prefers_ats_over_simplify():
    ats = P("Research Engineer Intern, Evals", url="https://job-boards.greenhouse.io/evalco/jobs/101",
            company="EvalCo", description="full text")
    sim = P("Research Engineer Intern, Evals", url="https://job-boards.greenhouse.io/evalco/jobs/101?gh_src=s",
            company="EvalCo", source="simplify-internships")
    out = pf.dedupe([sim, ats])
    assert len(out) == 1 and out[0].source == "greenhouse"


def test_contract_roles_need_a_matching_skill(profile):
    assert not pf.contract_ok(P("AI Tutor - Arabic"), profile)
    assert pf.contract_ok(P("AI Tutor - Coding (Python)"), profile)


# ---------------------------------------------------------------- end to end
class FakeNotion:
    def __init__(self):
        self.pages = {}

    def query_all(self, ds, body=None):
        pages = [p for p in self.pages.values() if p["ds"] == ds]
        want = (body or {}).get("filter", {}).get("title", {}).get("equals")
        for p in pages:
            if want is None or p["properties"]["Pipeline"]["title"][0]["text"]["content"] == want:
                yield self._as_read(p)

    @staticmethod
    def _as_read(p):
        props = {}
        for k, v in p["properties"].items():
            if "rich_text" in v or "title" in v:
                kind = "rich_text" if "rich_text" in v else "title"
                props[k] = {"type": kind, kind: [{"plain_text": t["text"]["content"]} for t in v[kind]]}
            else:
                props[k] = v
        return {"id": p["id"], "properties": props}

    def create_page(self, ds, properties):
        pid = f"page-{len(self.pages)}"
        self.pages[pid] = {"id": pid, "ds": ds, "properties": properties}
        return {"id": pid}

    def update_page(self, pid, properties):
        self.pages[pid]["properties"].update(properties)


IDS = {"Jobs": {"data_source_id": "jobs"}, "Engine status": {"data_source_id": "status"}}


def test_pipeline_end_to_end_is_idempotent(cfg, profile, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notion = FakeNotion()
    r1 = run(cfg, profile, today=TODAY, mock=True, fixtures=FIX, notion=notion, ids=IDS, log=lambda *_: None)
    jobs = [p for p in notion.pages.values() if p["ds"] == "jobs"]
    titles = {p["properties"]["Name"]["title"][0]["text"]["content"] for p in jobs}
    assert r1["ok"] and r1["sync"]["created"] == len(jobs) > 0
    assert "Research Engineer Intern, Evals · EvalCo" in titles           # ATS copy kept, Simplify dup dropped
    assert "Applied AI Engineer · EvalCo" in titles                       # remote applied-AI role
    assert "Applied AI Engineer, London · EvalCo" not in titles           # not remote, not US/JP/SG
    assert "Senior Staff Software Engineer, Inference · EvalCo" not in titles
    assert "AI Tutor - Coding (Python) · AsiaCo" in titles and "AI Tutor - Arabic · AsiaCo" not in titles
    assert all(p["properties"]["Status"]["select"]["name"] == "New" for p in jobs)
    evals = next(p for p in jobs if p["properties"]["Name"]["title"][0]["text"]["content"].startswith("Research Engineer"))
    assert {f["name"] for f in evals["properties"]["Flags"]["multi_select"]} >= {"No sponsorship", "Needs enrollment"}

    status = [p for p in notion.pages.values() if p["ds"] == "status"]
    assert len(status) == 1 and "GoneCo" in status[0]["properties"]["Failed sources"]["rich_text"][0]["text"]["content"]

    # Nissan (or a Bot) moves a row on; a rerun must not touch it or duplicate anything.
    notion.update_page(evals["id"], {"Status": {"select": {"name": "Shortlist"}}})
    r2 = run(cfg, profile, today=TODAY, mock=True, fixtures=FIX, notion=notion, ids=IDS, log=lambda *_: None)
    assert r2["sync"]["created"] == 0
    assert len([p for p in notion.pages.values() if p["ds"] == "jobs"]) == len(jobs)
    assert notion.pages[evals["id"]]["properties"]["Status"]["select"]["name"] == "Shortlist"
    assert len([p for p in notion.pages.values() if p["ds"] == "status"]) == 1
    assert (tmp_path / "out" / "jobs-report.md").exists()


def test_dry_run_never_writes(cfg, profile, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = run(cfg, profile, today=TODAY, dry_run=True, mock=True, fixtures=FIX, log=lambda *_: None)
    assert r["sync"] is None and r["rows"]
    assert "Dry run" in (tmp_path / "out" / "jobs-report.md").read_text()


# ---------------------------------------------------------------- notion + llm helpers
def test_notion_builders():
    assert multi(["a, b", "a; b", " "]) == {"multi_select": [{"name": "a; b"}]}
    assert len(rich("x" * 5000)["rich_text"]) == 3
    assert page_id_from_url("https://www.notion.so/Agent-Boards-0123456789abcdef0123456789abcdef") \
        == "01234567-89ab-cdef-0123-456789abcdef"
    p = P("ML Intern", "NYC")
    p.lane, p.regions, p.prescore = "internship", {"US"}, 61.4
    props = job_properties(p, TODAY)
    assert props["Score"]["number"] == 61 and props["Status"]["select"]["name"] == "New"
    assert props["Key"]["rich_text"][0]["text"]["content"] == p.key


def test_extract_json_tolerates_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"contacts": []} hope that helps') == {"contacts": []}


def test_mock_llm_costs_nothing_real():
    llm = MockLLM()
    assert llm.json("m", "s", "u", {}, name="fit")["fit"] == -1
    assert llm.research("m", "p")["contacts"]


def test_private_profile_overlay(monkeypatch, tmp_path):
    from boards.__main__ import load_profile

    f = tmp_path / "p.yaml"
    f.write_text("name: X\nwork_authorization: {us_citizen_or_pr: null, needs_us_sponsorship: null}\n")
    monkeypatch.setenv("PROFILE_PRIVATE", "graduation: '2027-05'\nwork_authorization: {needs_us_sponsorship: true}\n")
    p = load_profile(str(f))
    assert p["graduation"] == "2027-05"
    assert p["work_authorization"] == {"us_citizen_or_pr": None, "needs_us_sponsorship": True}


def test_artifact_never_contains_drafts(tmp_path):
    from boards.report import write_outputs

    p = P("ML Intern", "NYC")
    p.draft, p.contacts = "secret draft", "Jane (@jane)"
    write_outputs("# r\n", [p], tmp_path)
    text = (tmp_path / "jobs-rows.json").read_text()
    assert "secret draft" not in text and "@jane" not in text
