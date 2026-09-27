# The engine

Scheduled Python on GitHub Actions. It scans job boards every morning, keeps only openings you could realistically get, scores the best 25 with Grok, and adds them to Notion as new rows for the Career Agent. **Jobs is built; Hackathons and Research come next.**

```
ATS Scout (48 company boards) ─┐
Simplify internships + new grad ┴→ Pre-filter → Fit Scorer → Referral Mapper → Outreach Drafter → Notion
     ~7,000 postings                ~25 picks    grok-4.3      grok-4.7 + X       grok-4.3         new rows only
```

## What it looks for

Every posting gets a **lane**. Anything without one is dropped.

| Lane | Examples | Where it comes from |
| --- | --- | --- |
| `internship` | ML Intern, Research Engineer Intern – Inference, Co-op | Simplify's lists + company boards |
| `residency` | AI Infra Resident (1-year), Anthropic Fellows, AI Resident | both |
| `open-application` | "Open Application for Unconventional Talent", "Exceptional Generalist" | company boards |
| `applied-ai` | Applied AI Engineer, Member of Technical Staff, Forward Deployed Engineer: **remote-compatible, or in Japan/Singapore** | company boards |
| `new-grad` | New Grad SWE, Early Career ML | both |
| `ai-contract` | Paid remote AI tutor / trainer / evaluator work in coding, math or statistics | company boards (xAI, Mercor, Handshake, Surge…) |

The Pre-filter then works through these steps:
1. It drops senior roles and roles outside engineering (sales, legal and so on).
2. It keeps only roles in the US, Japan, Singapore, or remote.
3. It drops stale postings and passed deadlines.
4. It skips rows already in Notion.
5. It attaches **eligibility flags**: needs enrollment, no sponsorship, sponsors visa, US citizenship or clearance, PhD required, Master's required, and graduation window. Flags are shown, never used to drop a row. You decide.

Ranking rewards the lane, your target companies, well-known employers, AI-relevant titles, remote work, profile keywords and freshness. Seats are reserved for each lane (`lane_min`), so internships can't crowd out the remote applied-AI roles, or the reverse. There's also a cap of 3 rows per company.

A real sample from 27 Sep 2026, run on Simplify data only: Together AI *Research Intern – Inference*, Cohere *ML Intern/Co-op*, ByteDance *Agent Evaluation ML Engineer Intern*, Toyota Research *AI Resident*, NVIDIA *Deep Learning Intern*.

## Setup (about 15 minutes, browser only)

1. **xAI key.** Create one at console.x.ai and add $10 of credit.
2. **Notion.** Create an internal integration and copy its token. Make an empty page called "Agent Boards" and share it with the integration (••• → Connections).
3. **Secrets.** In the repo, go to Settings → Secrets and variables → Actions and add:
   - `XAI_API_KEY`
   - `NOTION_TOKEN`
   - `PROFILE_PRIVATE` (optional, recommended): YAML holding the private half of your profile. For example:
     ```yaml
     enrolled: true
     graduation: "2027-05"
     work_authorization: {us_citizen_or_pr: false, needs_us_sponsorship: true}
     ```
4. **Build Notion.** Go to Actions → **Setup Notion** → Run workflow, and paste the page URL. It creates Hackathons, Research, Jobs, People, Briefs and Engine status, then commits `notion_ids.json`. IDs aren't secrets.
5. **Profile.** Edit the public parts of `profile.yaml`: your proof links, target roles and keywords.
6. **Dry run.** Go to Actions → **Jobs** → Run workflow, with *dry run* ticked. It writes the report to the run summary and never touches Notion. Tick *mock* too for a $0 run with no xAI key.
7. **Go live.** The Jobs workflow then runs every day at 10:17 UTC (6:17 AM New York). The Career Agent's 8:00 AM routine picks up the new rows.
8. **Probe boards.** Once, go to Actions → **Probe boards**. It checks all 48 company boards from GitHub's network and prints a `config.yaml` snippet that pins the companies still set to `ats: auto`.

> **Privacy.** This repo is public, and so are its Actions summaries. The engine never writes drafts, contacts or résumé edits to logs or artifacts; those go only to Notion. Keep private profile answers in the `PROFILE_PRIVATE` secret. The blueprint recommends a private repo. If you make it private, Actions stays within the free 2,000 minutes a month.

## Run it locally

```bash
pip install -r requirements.txt
python -m boards run jobs --dry-run --mock                             # live data, fake model calls, $0
python -m boards run jobs --dry-run --mock --fixtures tests/fixtures   # fully offline
python -m boards run jobs --dry-run                                    # real Grok calls, no Notion writes
python -m boards probe                                                 # check every company board
python -m pytest -q
```

Reports go to `out/jobs-report.md` and `out/jobs-rows.json`.

## Tuning

Everything is in `config.yaml`:
- `companies`: add or remove companies. Use `ats: auto` if you don't know the ATS.
- `weights`: how much each lane, tier and signal counts.
- `title_relevance`: which title words count as AI-relevant, and which as analyst or business roles.
- `notable_companies`: well-known employers outside your target list.
- `lane_min`, `top_n`, `per_company_cap`: the shape of the daily 25.
- `lean: true` (or tick *lean* on a manual run): runs the Referral Mapper only on scores of 75 or more, which is where most of the cost goes.

After a week, compare the rows you actually moved past Shortlist with their scores. The Sunday brief does this for you. Then retune `weights`.

## Cost

About 25 Fit Scorer calls + 5 Referral Mapper calls (with live X and web search) + up to 10 drafts a day. That's roughly **$0.30–0.40 a day**. Each run's summary shows the actual token count and cost.

## Rules the code keeps

- **New rows only.** A row is created once, with Status `New`. After that, the engine only fills fields that are empty (for example, a Deadline it learns later). It never writes Status or Status changed; those belong to you and your Bots.
- **Every row has a Key** (a hash of source + posting ID), so reruns never duplicate a row.
- **Sources fail one at a time.** A dead board shows up under *Failed sources* in the run summary and in the Engine status table. The rest of the run carries on.
- **No sending code.** The engine has no code for email, DMs or applications. Drafts are starting points for the Career Agent's Deep Dive.
- **Plain API calls, not CrewAI.** Each crew member is one structured call per posting, run in sequence. CrewAI would add prompt overhead and a heavy dependency without changing the result.
