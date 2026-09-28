"""Pre-filter: plain code that takes ~8,000 postings down to the ~25 worth an LLM call.

Stages: lane (what kind of opening) → exclusions (seniority, non-engineering functions) →
location (US, Japan, Singapore, remote) → freshness → seen-before → eligibility flags →
heuristic pre-score → diversified top N.

Eligibility flags are attached to the row, never used to drop it: Nissan decides.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date

from ..models import Posting

# ---------------------------------------------------------------- lanes
# Order matters: the first matching lane wins.
LANES: list[tuple[str, re.Pattern]] = [
    ("internship", re.compile(
        r"\bintern(ship)?s?\b|\bco-?op\b|\b(summer|fall|spring|winter|autumn) 20\d\d\b|"
        r"\bstudent (researcher|engineer|developer)\b|\bplacement\b|\bwerkstudent\b", re.I)),
    ("residency", re.compile(
        r"\bresiden(t|cy)\b|\bfellow(ship)?s?\b|\bapprentice(ship)?\b|\bscholars? program\b", re.I)),
    ("open-application", re.compile(
        r"open application|general application|exceptional (talent|generalist|engineer)|"
        r"unconventional talent|don.?t see (a|your) role|future opportunit|talent (pool|community)", re.I)),
    ("new-grad", re.compile(
        r"new ?grad|university grad|recent grad|graduate (engineer|program|software|research)|"
        r"entry[- ]level|early[- ]career|\bjunior\b|\bassociate (software|ml|machine|ai|research)", re.I)),
    ("ai-contract", re.compile(
        r"\bai (tutor|trainer)\b|data annotat|annotation (expert|specialist)|\brlhf\b|"
        r"model (evaluator|trainer)|\bai (writing|coding|math|stem) (expert|specialist|evaluator)|"
        r"(coding|stem|math|software) expert\b.*\b(ai|model|llm)", re.I)),
    ("applied-ai", re.compile(
        r"applied (ai|ml|research|scientist)|\bai engineer|\bml engineer|machine learning engineer|"
        r"research engineer|forward[- ]deployed|member of (the )?technical staff|\bmts\b|"
        r"\bevals?\b|evaluation|\binference\b|\bllm\b|\bagents?\b|\bgenai\b|generative ai|"
        r"solutions (engineer|architect)|developer (relations|advocate)|ai (research|product)", re.I)),
]

EXCLUDE_SENIORITY = re.compile(
    r"\bsenior\b|\bsr\.?\b|^staff\b|\bstaff (software|machine|ml|research|engineer|scientist|data|product)|"
    r"\bprincipal\b|\bdistinguished\b|\blead\b|\bhead of\b|\bdirector\b|\bmanager\b|\bvp\b|"
    r"vice president|\bchief\b|\bfounding\b|\bexecutive\b|\biii\b|\biv\b|\bl[5-9]\b", re.I)

EXCLUDE_FUNCTION = re.compile(
    r"\bsales\b|account (executive|manager)|business development|\brecruit|talent (acquisition|operations|partner)|"
    r"\blegal\b|counsel|paralegal|marketing|communications|\bpr\b|finance|accountant|accounting|"
    r"\btax\b|payroll|\bhr\b|people (ops|operations|partner|lead)|\bdesigner\b|\bartist\b|"
    r"facilities|office (manager|coordinator)|executive assistant|\bit (support|systems|operations)\b|"
    r"customer success|\bsupport (specialist|agent|representative)\b|procurement|real estate|"
    r"\bnurse\b|clinical|mechanical|electrical engineer|technician|warehouse|\bdriver\b|"
    r"physical security|security guard|social media|video (editor|producer)|copywriter", re.I)

# ---------------------------------------------------------------- locations
US_STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH "
             "NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split()
US_WORDS = re.compile(
    r"united states|\busa?\b|\bu\.s\.|america|\bnyc?\b|new york|\bsf\b|san francisco|bay area|"
    r"palo alto|mountain view|menlo park|sunnyvale|san jose|san mateo|redwood city|cupertino|"
    r"santa clara|berkeley|oakland|seattle|bellevue|redmond|boston|cambridge, ma|austin|"
    r"los angeles|san diego|chicago|denver|boulder|atlanta|pittsburgh|philadelphia|"
    r"washington|miami|dallas|houston|salt lake|portland|raleigh|durham|baltimore|princeton", re.I)
US_STATE_PAT = re.compile(r"(?:,|\b)\s*(" + "|".join(US_STATES) + r")\b(?!-)")
JP_WORDS = re.compile(r"japan|tokyo|osaka|kyoto|yokohama|fukuoka", re.I)
SG_WORDS = re.compile(r"singapore", re.I)
REMOTE_WORDS = re.compile(r"\bremote\b|\banywhere\b|distributed|work from home|\bwfh\b", re.I)
OTHER_REGION = re.compile(
    r"canada|toronto|vancouver|montreal|united kingdom|\buk\b|london|england|ireland|dublin|"
    r"europe|\bemea\b|\beu\b|germany|berlin|munich|france|paris|netherlands|amsterdam|spain|"
    r"madrid|barcelona|italy|poland|warsaw|switzerland|zurich|sweden|stockholm|denmark|"
    r"india|bangalore|bengaluru|hyderabad|pune|mumbai|delhi|gurgaon|china|beijing|shanghai|"
    r"shenzhen|hong kong|taiwan|taipei|korea|seoul|australia|sydney|melbourne|brazil|"
    r"latam|latin america|mexico|argentina|israel|tel aviv|dubai|uae|philippines|vietnam|"
    r"indonesia|jakarta|malaysia|kuala lumpur|thailand|bangkok|nigeria|kenya|south africa", re.I)


def regions_of(location: str, remote: bool) -> set[str]:
    """Classify a free-text location into {US, JP, SG, REMOTE, OTHER}."""
    text = location or ""
    found = set()
    if US_WORDS.search(text) or US_STATE_PAT.search(text):
        found.add("US")
    if JP_WORDS.search(text):
        found.add("JP")
    if SG_WORDS.search(text):
        found.add("SG")
    if OTHER_REGION.search(text):
        found.add("OTHER")
    if remote or REMOTE_WORDS.search(text):
        # "Remote - Canada" is remote somewhere else; plain "Remote" or "Remote (US)" is usable.
        if "OTHER" not in found or found & {"US", "JP", "SG"}:
            found.add("REMOTE")
    return found


def location_ok(regions: set[str], allowed: set[str]) -> bool:
    if not regions:            # blank location: keep, flag later
        return True
    return bool(regions & allowed)


# ---------------------------------------------------------------- eligibility flags
PATTERNS = {
    "Needs enrollment": re.compile(
        r"(currently|actively) (enrolled|pursuing)|must be (a )?(current(ly)?|enrolled|returning) (student|enrolled)|"
        r"returning to (school|university|your studies)|enrolled in (a|an) (bachelor|master|ph\.?d|degree|undergraduate|graduate)", re.I),
    "No sponsorship": re.compile(
        r"(not|unable to|cannot|can.?t|won.?t|will not|does not|do not) (be able to )?(provide|offer|sponsor|support)[^.]{0,40}(sponsor|visa)|"
        r"without (the need for )?(current or future |now or in the future |future )?(visa |employment )?sponsorship|"
        r"no (visa )?sponsorship", re.I),
    "Sponsors visa": re.compile(
        r"(visa|immigration) sponsorship (is )?(available|offered|provided)|we (will |can )?sponsor|"
        r"sponsorship (is )?available|open to sponsoring", re.I),
    "US citizenship / clearance": re.compile(
        r"u\.?s\.? citizen(ship)? (is )?required|must be a u\.?s\.? citizen|security clearance|\bts/sci\b|"
        r"\bitar\b|export control|us persons? only", re.I),
    "PhD required": re.compile(
        r"(currently )?(pursuing|enrolled in) a ph\.?d|ph\.?d\.? (student|candidate)s? (only|required)|"
        r"ph\.?d\.? (is )?required|doctoral (student|candidate)", re.I),
    "Master's required": re.compile(r"master.?s (degree )?(is )?required|pursuing a master.?s", re.I),
}
GRAD_YEAR = re.compile(r"graduat\w*[^.]{0,60}?\b(20\d\d)\b(?:[^.]{0,20}?\b(20\d\d)\b)?", re.I)


def eligibility_flags(p: Posting, profile: dict) -> list[str]:
    text = f"{p.title}\n{p.description}"
    flags = [name for name, pat in PATTERNS.items() if pat.search(text)]
    sponsorship = (p.hints.get("sponsorship") or "").lower()
    if "does not offer" in sponsorship and "No sponsorship" not in flags:
        flags.append("No sponsorship")
    if "citizenship" in sponsorship and "US citizenship / clearance" not in flags:
        flags.append("US citizenship / clearance")
    if "offers sponsorship" in sponsorship and "Sponsors visa" not in flags:
        flags.append("Sponsors visa")
    if re.search(r"\bph\.?d\b|doctoral", p.title, re.I) and "PhD required" not in flags:
        flags.append("PhD required")
    elif re.search(r"\bmaster.?s\b|\bm\.?s\.? (student|only)\b", p.title, re.I) and "Master's required" not in flags:
        flags.append("Master's required")
    degrees = [d.lower() for d in p.hints.get("degrees") or []]
    if degrees and all("phd" in d for d in degrees) and "PhD required" not in flags:
        flags.append("PhD required")

    grad = str(profile.get("graduation") or "")[:4]
    m = GRAD_YEAR.search(p.description or "")
    if grad.isdigit() and m:
        years = sorted({int(y) for y in m.groups() if y})
        if years and not (years[0] <= int(grad) <= years[-1]):
            window = "–".join(str(y) for y in dict.fromkeys([years[0], years[-1]]))
            flags.append(f"Grad window {window} (you: {grad})")
    if not p.location:
        flags.append("Location unclear")
    return flags


# ---------------------------------------------------------------- scoring
@dataclass
class FilterStats:
    scouted: int = 0
    after_dedupe: int = 0
    after_lane: int = 0
    after_location: int = 0
    after_fresh: int = 0
    after_seen: int = 0
    selected: int = 0
    lanes: Counter = field(default_factory=Counter)
    dropped: Counter = field(default_factory=Counter)


def normalize_url(url: str) -> str:
    url = (url or "").split("?")[0].split("#")[0].rstrip("/").lower()
    return re.sub(r"/(application|apply)$", "", url)


def dedupe(postings: list[Posting]) -> list[Posting]:
    """Collapse the same opening seen via an ATS and via Simplify. ATS rows win (they carry
    the full description)."""
    def rank(p: Posting) -> int:
        return 0 if p.source in ("greenhouse", "lever", "ashby") else 1

    seen_urls: set[str] = set()
    seen_names: set[tuple[str, str]] = set()
    out = []
    for p in sorted(postings, key=rank):
        u = normalize_url(p.url)
        n = (re.sub(r"\W", "", p.company.lower()), re.sub(r"\W", "", p.title.lower()))
        if (u and u in seen_urls) or n in seen_names:
            continue
        seen_urls.add(u)
        seen_names.add(n)
        out.append(p)
    return out


def classify_lane(p: Posting) -> str:
    lanes = dict(LANES)
    if p.source.startswith("simplify"):
        # Simplify lists are already internships or new-grad roles; only programs stand apart.
        if lanes["residency"].search(p.title):
            return "residency"
        return "internship" if "intern" in p.source else "new-grad"
    for lane, pat in LANES:
        if pat.search(p.title):
            return lane
    if (p.employment_type or "").lower() in ("intern", "internship"):
        return "internship"
    return ""


def exclusion_reason(p: Posting) -> str:
    if p.lane in ("internship", "residency") and not EXCLUDE_FUNCTION.search(p.title):
        return ""  # "Research Intern, Staff Team" etc. are still internships
    if EXCLUDE_SENIORITY.search(p.title):
        return "seniority"
    if EXCLUDE_FUNCTION.search(p.title):
        return "function"
    return ""


def contract_ok(p: Posting, profile: dict) -> bool:
    words = [w.lower() for w in profile.get("contract_keywords") or []]
    langs = [w.lower() for w in profile.get("languages") or ["english"]]
    title = p.title.lower()
    if re.search(r"ai tutor\s*[-–:]\s*(\w+)", title):  # "AI Tutor - Arabic": language-specific
        lang = re.search(r"ai tutor\s*[-–:]\s*(\w+)", title).group(1)
        return lang in langs or lang in words
    return any(w in title for w in words) if words else True


def _compile(words: list[str]) -> re.Pattern | None:
    return re.compile("|".join(f"(?:{w})" for w in words), re.I) if words else None


_title_cache: dict[int, list] = {}


def title_points(title: str, cfg: dict) -> int:
    """How well the title itself matches applied-AI / research engineering work."""
    rules = cfg.get("title_relevance") or []
    key = id(rules)
    if key not in _title_cache:
        _title_cache[key] = [(_compile(r.get("words", [])), r.get("points", 0)) for r in rules]
    # Best positive match plus worst negative match: "AI Consulting Intern" nets 20 - 12.
    hits = [points for pat, points in _title_cache[key] if pat and pat.search(title)]
    return max([h for h in hits if h > 0], default=0) + min([h for h in hits if h < 0], default=0)


def is_notable(company: str, cfg: dict) -> bool:
    names = cfg.get("notable_companies") or []
    c = company.lower()
    return any(re.search(rf"\b{re.escape(n.lower())}\b", c) for n in names)


def prescore(p: Posting, cfg: dict, profile: dict, today: date) -> float:
    weights = cfg.get("weights", {})
    score = weights.get("lane", {}).get(p.lane, 10)
    score += weights.get("tier", {}).get(p.tier, 0)
    score += title_points(p.title, cfg)
    if not p.tier and is_notable(p.company, cfg):
        score += weights.get("notable", 12)
    if not p.tier and (p.category or "").lower().startswith(("ai", "data science")):
        score += weights.get("simplify_ai_category", 5)
    if "REMOTE" in p.regions:
        score += weights.get("remote", 10)
    text = f"{p.title}\n{p.description}".lower()
    hits = sum(1 for k in profile.get("keywords") or [] if k.lower() in text)
    score += min(hits * 2, weights.get("keyword_cap", 14))
    age = p.age_days(today)
    if age is not None:
        score += 8 if age <= 3 else 5 if age <= 7 else 2 if age <= 14 else 0
    auth = profile.get("work_authorization") or {}
    penalties = weights.get("flag_penalty", {})
    for f in p.flags:
        if f == "US citizenship / clearance" and auth.get("us_citizen_or_pr") is False:
            score -= penalties.get("citizenship", 25)
        elif f == "No sponsorship" and auth.get("needs_us_sponsorship") is True:
            score -= penalties.get("no_sponsorship", 15)
        elif f == "PhD required" and (profile.get("degree") or "").lower() != "phd":
            score -= penalties.get("phd", 15)
        elif f == "Master's required" and (profile.get("degree") or "").lower() not in ("masters", "phd"):
            score -= penalties.get("masters", 10)
        elif f.startswith("Grad window"):
            score -= penalties.get("grad_window", 10)
        elif f == "Needs enrollment" and profile.get("enrolled") is False:
            score -= penalties.get("enrollment", 20)
    return round(score, 1)


def run_prefilter(postings: list[Posting], *, cfg: dict, profile: dict, today: date,
                  seen_keys: set[str] | frozenset = frozenset()) -> tuple[list[Posting], FilterStats]:
    stats = FilterStats(scouted=len(postings))
    allowed = set(cfg.get("regions", ["US", "JP", "SG", "REMOTE"]))
    max_age = cfg.get("max_age_days", 45)
    top_n = cfg.get("top_n", 25)
    per_company = cfg.get("per_company_cap", 3)

    pool = dedupe(postings)
    stats.after_dedupe = len(pool)

    kept = []
    for p in pool:
        p.lane = classify_lane(p)
        if not p.lane:
            stats.dropped["no lane"] += 1
            continue
        reason = exclusion_reason(p)
        if reason:
            stats.dropped[reason] += 1
            continue
        if p.lane == "ai-contract" and not contract_ok(p, profile):
            stats.dropped["contract mismatch"] += 1
            continue
        kept.append(p)
    stats.after_lane = len(kept)

    located = []
    for p in kept:
        p.regions = regions_of(p.location, p.remote)
        # Full-time applied-AI roles at target companies only count when remote-compatible,
        # unless they are in Japan or Singapore; internships and programs may be on-site.
        if p.lane == "applied-ai" and not (p.regions & {"REMOTE", "JP", "SG"}):
            stats.dropped["applied-ai not remote"] += 1
            continue
        if not location_ok(p.regions, allowed):
            stats.dropped["location"] += 1
            continue
        located.append(p)
    stats.after_location = len(located)

    fresh = []
    for p in located:
        age = p.age_days(today)
        # Simplify only lists roles that are still open, so it gets a longer window.
        limit = cfg.get("max_age_days_simplify", 150) if p.source.startswith("simplify") else max_age
        if age is not None and age > limit and p.lane not in ("open-application", "residency"):
            stats.dropped["stale"] += 1
            continue
        if p.deadline and p.deadline < today:
            stats.dropped["deadline passed"] += 1
            continue
        fresh.append(p)
    stats.after_fresh = len(fresh)

    unseen = [p for p in fresh if p.key not in seen_keys]
    stats.dropped["seen before"] += len(fresh) - len(unseen)
    stats.after_seen = len(unseen)

    for p in unseen:
        p.flags = eligibility_flags(p, profile)
        p.prescore = prescore(p, cfg, profile, today)
        stats.lanes[p.lane] += 1

    ranked = sorted(unseen, key=lambda p: (-p.prescore, p.company, p.title))
    per: dict[str, int] = defaultdict(int)
    lane_min = cfg.get("lane_min", {})
    selected: list[Posting] = []
    # Guarantee each lane a few seats so internships don't crowd out remote roles, or vice versa.
    for lane, seats in lane_min.items():
        for p in [q for q in ranked if q.lane == lane]:
            if sum(1 for s in selected if s.lane == lane) >= seats or len(selected) >= top_n:
                break
            if per[p.company] < per_company and p not in selected:
                selected.append(p)
                per[p.company] += 1
    for p in ranked:
        if len(selected) >= top_n:
            break
        if p not in selected and per[p.company] < per_company:
            selected.append(p)
            per[p.company] += 1
    selected.sort(key=lambda p: -p.prescore)
    stats.selected = len(selected)
    return selected, stats
