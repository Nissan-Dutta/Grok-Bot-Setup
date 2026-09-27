"""Command line.

    python -m boards run jobs [--dry-run] [--mock] [--fixtures DIR]
    python -m boards probe
    python -m boards setup-notion --page <Notion page URL>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def load_profile(path: str) -> dict:
    """profile.yaml, overlaid with the PROFILE_PRIVATE secret (YAML) if it is set.

    Keep sensitive answers (work authorization, graduation date) in the secret, not in the
    committed file: this repo's Actions logs are public when the repo is public.
    """
    import os

    profile = load_yaml(path)
    private = yaml.safe_load(os.environ.get("PROFILE_PRIVATE") or "") or {}
    for key, value in private.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            profile[key] = {**profile[key], **value}
        else:
            profile[key] = value
    return profile


def cmd_run(args) -> int:
    cfg = load_yaml(args.config)
    profile = load_profile(args.profile)
    if args.lean:
        cfg["lean"] = True
    if args.board != "jobs":
        print(f"The {args.board} pipeline isn't built yet. Only 'jobs' is.", file=sys.stderr)
        return 2
    notion = ids = None
    if not args.dry_run or args.read_notion:
        from .notion import Notion, load_ids
        notion, ids = Notion(), load_ids()
    from .jobs.pipeline import run
    result = run(cfg, profile, dry_run=args.dry_run, mock=args.mock,
                 fixtures=Path(args.fixtures) if args.fixtures else None, notion=notion, ids=ids)
    return 0 if result["ok"] else 1


def cmd_probe(args) -> int:
    """Check every configured company board and print a corrected companies block."""
    from .sources.ats import Company, scout_all

    cfg = load_yaml(args.config)
    companies = [Company(**c) for c in cfg["jobs"]["companies"]]
    res = scout_all(companies)
    lines = ["# Board probe", "", "| Company | ATS / slug | Postings |", "| --- | --- | ---: |"]
    for c in companies:
        if c.name in res.resolved:
            ats, slug = res.resolved[c.name]
            lines.append(f"| {c.name} | {ats}/{slug} | {res.counts.get(c.name, 0)} |")
        else:
            lines.append(f"| {c.name} | ❌ {res.errors.get(c.name, '')[:120]} | 0 |")
    lines += ["", "Pin auto-detected boards in config.yaml:", "", "```yaml"]
    for c in companies:
        if c.ats == "auto" and c.name in res.resolved:
            ats, slug = res.resolved[c.name]
            lines.append(f"    - {{name: {json.dumps(c.name)}, ats: {ats}, slug: {json.dumps(slug)}, tier: {c.tier}}}")
    lines.append("```")
    md = "\n".join(lines) + "\n"
    print(md)
    import os
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write(md)
    return 0


def cmd_setup_notion(args) -> int:
    from .notion import IDS_FILE, Notion

    ids = Notion().setup(args.page)
    IDS_FILE.write_text(json.dumps(ids, indent=2) + "\n")
    print(f"Created {len(ids)} databases. IDs saved to {IDS_FILE}.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="boards")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--profile", default="profile.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run one pipeline")
    r.add_argument("board", choices=["jobs", "hackathons", "research"])
    r.add_argument("--dry-run", action="store_true", help="write the report only; never touch Notion")
    r.add_argument("--mock", action="store_true", help="fake LLM calls: $0, no XAI_API_KEY needed")
    r.add_argument("--lean", action="store_true", help="cheaper settings (see config.yaml)")
    r.add_argument("--fixtures", help="read ATS/Simplify JSON from this folder instead of the network")
    r.add_argument("--read-notion", action="store_true",
                   help="in a dry run, still read Notion to skip rows you've already seen")
    r.set_defaults(func=cmd_run)

    sub.add_parser("probe", help="check every configured job board").set_defaults(func=cmd_probe)

    s = sub.add_parser("setup-notion", help="build the databases under a shared page")
    s.add_argument("--page", required=True, help="URL or ID of the empty 'Agent Boards' page")
    s.set_defaults(func=cmd_setup_notion)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
