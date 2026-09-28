"""The Jobs crew: Fit Scorer → Referral Mapper → Outreach Drafter.

Each agent is one structured model call per posting. They run in sequence on the pre-filter's
top picks, so the expensive live-search step only ever sees the best few.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import yaml

from ..models import Posting

FIT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["fit", "why", "angle", "flags", "confirmed_lane"],
    "properties": {
        "fit": {"type": "integer", "description": "0-100: odds this person gets an interview"},
        "why": {"type": "string", "description": "<= 40 words, specific, no fluff"},
        "angle": {"type": "string", "description": "which proof point to lead with, and why"},
        "flags": {"type": "array", "items": {"type": "string"},
                  "description": "eligibility problems found in the posting text"},
        "confirmed_lane": {"type": "string", "enum": ["keep", "wrong-level", "not-a-fit"]},
    },
}

DRAFT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["draft", "resume_edits"],
    "properties": {
        "draft": {"type": "string", "description": "cold DM or email, under 110 words"},
        "resume_edits": {"type": "array", "items": {"type": "string"}},
    },
}

FIT_SYSTEM = """You are the Fit Scorer for a job-search engine. Judge one posting against one
candidate profile. Score the realistic odds of getting an interview (0-100), not how exciting
the job is. Reward: early-career or program roles, remote-compatible roles, work that matches the
candidate's proof (evals, statistics, inference, agents). Penalize: seniority the candidate lacks,
hard eligibility blockers (citizenship, clearance, PhD-only, graduation windows the candidate
misses). Never invent facts about the candidate. Flags must quote the posting's requirement."""

DRAFT_SYSTEM = """You are the Outreach Drafter. Write one cold message from the candidate to the
named contact (or to the hiring team if there is none). Rules: under 110 words; exactly one
specific hook about the contact's own recent work; one proof link from the candidate's profile;
one small ask (a 15-minute call, or who the right person is). No flattery, no buzzwords, no
claims the profile does not support. Also suggest up to 3 resume bullet swaps for this role."""


def _profile_text(profile: dict) -> str:
    keep = {k: v for k, v in profile.items() if k not in ("contract_keywords",)}
    return yaml.safe_dump(keep, sort_keys=False, allow_unicode=True)


def _posting_text(p: Posting, limit: int = 6000) -> str:
    return (f"Title: {p.title}\nCompany: {p.company}\nLane: {p.lane}\nLocation: {p.location or 'n/a'}"
            f"\nRemote-compatible: {'REMOTE' in p.regions}\nPosted: {p.posted or 'n/a'}"
            f"\nDeadline: {p.deadline or 'n/a'}\nEngine flags: {', '.join(p.flags) or 'none'}"
            f"\nURL: {p.url}\n\nDescription:\n{(p.description or '(no description; Simplify listing)')[:limit]}")


def fit_score(llm, postings: list[Posting], profile: dict, model: str, workers: int = 5) -> None:
    prof = _profile_text(profile)

    def one(p: Posting):
        try:
            r = llm.json(model, FIT_SYSTEM, f"PROFILE:\n{prof}\n\nPOSTING:\n{_posting_text(p)}",
                         FIT_SCHEMA, name="fit")
        except Exception as exc:  # one bad reply must not sink the run
            p.why = f"Fit Scorer failed: {exc}"[:200]
            p.score = round(p.prescore)
            return
        fit = int(r["fit"])
        # A negative fit means "no judgment" (mock runs): keep the heuristic, clipped to 0-100.
        p.score = max(0, min(100, fit if fit >= 0 else round(p.prescore)))
        if r.get("confirmed_lane") in ("wrong-level", "not-a-fit"):
            p.score = min(p.score, 35)
        p.why = r.get("why", "")
        p.angle = r.get("angle", "")
        for f in r.get("flags") or []:
            f = f.strip()[:90]
            if f and f not in p.flags:
                p.flags.append(f)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, postings))


def map_referrals(llm, postings: list[Posting], model: str) -> None:
    for p in postings:
        prompt = (
            f"Find 2-3 engineers or researchers who work on the team behind this opening and who "
            f"post publicly on X. Opening: {p.title} at {p.company} ({p.url}).\n"
            "For each person give their name, X handle, role, and one specific thing they posted "
            "or shipped in the last 60 days that the candidate could mention, with its link. Only "
            "include people you verified work at the company now. Reply as JSON: "
            '{"contacts": [{"name": "", "handle": "", "role": "", "hook": "", "hook_url": ""}]}'
        )
        try:
            r = llm.research(model, prompt)
        except Exception as exc:
            p.contacts = f"Referral Mapper failed: {exc}"[:200]
            continue
        lines = [f"{c.get('name')} ({c.get('handle')}) · {c.get('role')} · hook: {c.get('hook')} "
                 f"{c.get('hook_url', '')}".strip() for c in (r.get("contacts") or [])[:3]]
        p.contacts = "\n".join(lines)


def draft_outreach(llm, postings: list[Posting], profile: dict, model: str, max_words: int = 110) -> None:
    prof = _profile_text(profile)
    for p in postings:
        user = (f"PROFILE:\n{prof}\n\nPOSTING:\n{_posting_text(p, 3000)}\n\nANGLE: {p.angle}"
                f"\n\nCONTACTS:\n{p.contacts or 'none found: address the hiring team'}")
        try:
            r = llm.json(model, DRAFT_SYSTEM, user, DRAFT_SCHEMA, name="draft")
            if len(r["draft"].split()) > max_words:
                r = llm.json(model, DRAFT_SYSTEM,
                             user + f"\n\nYour last draft was over {max_words} words. Cut it.",
                             DRAFT_SCHEMA, name="draft")
        except Exception as exc:
            p.draft = f"Outreach Drafter failed: {exc}"[:200]
            continue
        p.draft = r["draft"].strip()
        p.resume_edits = "\n".join(f"- {e}" for e in r.get("resume_edits") or [])
        if len(p.draft.split()) > max_words:
            p.flags.append(f"Draft over {max_words} words")
