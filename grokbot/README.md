# grokbot/: the Grok Bot layer

Three Bots, each with its own Notion database. The engine (GitHub Actions) scans and scores. The Bots do the work that needs a browser, your logins or your approval.

| Bot | Job | Notion database | Skills |
| --- | --- | --- | --- |
| [Hackathon Captain](bots/hackathon-captain.md) | Finds events that get you in front of people who hire, then gets you in | Hackathons | triage · application-packer · team-up-scout |
| [Research Lead](bots/research-lead.md) | Turns papers into your own publications, without a lab | Research | experiment-runner · endorser-scout |
| [Career Agent](bots/career-agent.md) | Finds roles you can actually get, plus a way in | Jobs, People (+ Briefs) | deep-dive · linkedin-mapper · application-filler · weekly-brief |

Two skills are shared: [`handoff-to-career`](skills/shared/handoff-to-career.md) and [`weekly-brief`](skills/shared/weekly-brief.md).

## Three rules

1. **Start sub-agents as skills.** Only promote one to its own Bot when it has a steady job of its own. The likely first is an Outreach Writer shared by all three Bots, once you know your voice.
2. **One Notion database per Bot, and Notion is the truth.** The engine only adds new rows. The Bots own the Status column. Shared records sit next to the three boards: **People** holds handoffs, **Briefs** holds the Sunday pages, and **Engine status** shows when each pipeline last ran.
3. **Handoffs between Bots.** If a hackathon sponsor or a paper's author works at one of your target companies, the Captain or the Research Lead passes the name to the Career Agent, using [`handoff-to-career`](skills/shared/handoff-to-career.md).

## Setup (about 20 minutes)

1. **Create the 3 Bots.** Name each one exactly as above, then paste the fenced block from its `bots/*.md` into the Bot's description.
2. **Build Notion and start the engine** by following [ENGINE.md](../ENGINE.md) (about 15 minutes).
3. **Install the Notion connector** from Marketplace, and give it the "Agent Boards" page. If Marketplace has no Notion connector for your account, the Bots can use Notion in the shared browser instead. Log in once by taking control of the Agent Computer.
4. **Fill the proof pack** on the Bot computer (the Bots share one computer): `/workspace/proof-pack/` with `resume.pdf`, `bio.md`, `answers.md`, `links.md`, `profile.md` and `headshot.jpg`.
5. **Save the skills.** For each file in `skills/`, open any Bot and say: *"Save this as a skill called `<name>`"*, then paste the file. Private skills are one library shared by all Bots, which is why the names carry a prefix. Check that they appear under Marketplace → Your plugins → Manage plugins and skills → Private skills.
6. **Set the Auto-Review rules** listed at the bottom of [routines.md](routines.md).
7. **Create the routines** from [routines.md](routines.md). Test run each one, then enable it.
8. **Open the War Room.** Create a group chat with the 3 Bots. The cap is 6, which leaves room for the Outreach Writer later.

## Engine status

The **Jobs** pipeline is built (see [ENGINE.md](../ENGINE.md)): it fills the Jobs database every morning and updates its row in the "Engine status" table. The Hackathons and Research pipelines aren't built yet. Until they are:

- The Hackathon Captain's and Research Lead's routines open with an "engine hasn't run" warning and work on the rows already in Notion.
- **Seed rows yourself.** Paste a Devpost link or an arXiv ID into the Bot's chat and say "add this as a New row, then triage it". The Bot uses its own judgment and fills in Score and Why.
- **Run the skills on demand** (`/captain-triage`, `/research-experiment-runner` and so on).

### Skill files → skill names

| File | Skill name |
| --- | --- |
| `skills/hackathon-captain/triage.md` | `captain-triage` |
| `skills/hackathon-captain/application-packer.md` | `captain-application-packer` |
| `skills/hackathon-captain/team-up-scout.md` | `captain-team-up-scout` |
| `skills/research-lead/experiment-runner.md` | `research-experiment-runner` |
| `skills/research-lead/endorser-scout.md` | `research-endorser-scout` |
| `skills/career-agent/deep-dive.md` | `career-deep-dive` |
| `skills/career-agent/linkedin-mapper.md` | `career-linkedin-mapper` |
| `skills/career-agent/application-filler.md` | `career-application-filler` |
| `skills/shared/handoff-to-career.md` | `handoff-to-career` |
| `skills/shared/weekly-brief.md` | `weekly-brief` |

Every skill follows xAI's template: When to use · Inputs & access · Steps · Validate · Return · Needs approval.
