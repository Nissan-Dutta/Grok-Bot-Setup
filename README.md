# Grok-Bot-Setup

Three Grok Bots that turn hackathons, papers and job boards into interviews, publications and wins. A cheap scheduled engine does the scanning. The Bots do the judgment, the logged-in browsing and the drafting. You approve everything that leaves.

| Bot | Job |
| --- | --- |
| **Hackathon Captain** | Finds events that get you in front of people who hire, then gets you in |
| **Research Lead** | Turns papers into your own publications, without a lab |
| **Career Agent** | Finds roles you can actually get, plus a way in |

- [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md): the full design. It covers the architecture, each board's sub-agents, the Notion schema, costs and guardrails.
- [`grokbot/`](grokbot/): everything to set up the Bots. It holds the Bot descriptions to paste in (`bots/`), the skills (`skills/`) and the routines (`routines.md`).
- [`ENGINE.md`](ENGINE.md): the scheduled engine. **Jobs** is live: it scans 48 company job boards and Simplify's internship and new-grad lists every morning, scores the best 25 with Grok, and adds them to Notion. Hackathons and Research come next.

There's no Chief of Staff. The Sunday brief is a weekly routine on the Career Agent.
