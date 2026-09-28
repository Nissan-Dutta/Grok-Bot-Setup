from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timezone


def make_key(source: str, ident: str) -> str:
    """Stable row key: a hash of source + source-side ID, so reruns never duplicate."""
    return hashlib.sha1(f"{source}:{ident}".encode()).hexdigest()[:16]


@dataclass
class Posting:
    source: str               # "greenhouse" | "lever" | "ashby" | "simplify-internships" | ...
    source_id: str
    company: str
    title: str
    url: str
    location: str = ""
    remote: bool = False
    employment_type: str = ""  # "Intern", "FullTime", "Contract", ...
    posted: date | None = None
    deadline: date | None = None
    description: str = ""
    tier: str = ""             # config tier for target companies; "" for Simplify-only companies
    category: str = ""         # Simplify category, e.g. "AI/ML/Data"
    hints: dict = field(default_factory=dict)  # source-provided eligibility hints

    # Filled in by the pipeline
    lane: str = ""
    regions: set[str] = field(default_factory=set)
    flags: list[str] = field(default_factory=list)
    prescore: float = 0.0
    score: int | None = None
    why: str = ""
    angle: str = ""
    contacts: str = ""
    draft: str = ""
    resume_edits: str = ""

    @property
    def key(self) -> str:
        return make_key(self.source, self.source_id)

    @property
    def name(self) -> str:
        return f"{self.title} · {self.company}"

    def age_days(self, today: date) -> int | None:
        return (today - self.posted).days if self.posted else None


def parse_date(value) -> date | None:
    """Accept ISO strings, epoch seconds or epoch milliseconds."""
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 1e11 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc).date()
        text = str(value).strip()
        if text.isdigit():
            return parse_date(int(text))
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except (ValueError, OverflowError, OSError):
        return None
