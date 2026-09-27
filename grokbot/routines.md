# Routines

There are four routines across three Bots. Each engine pipeline runs before its Bot routine, so every Bot wakes up to fresh rows. Times are New York; the engine crons are in UTC.

| Routine | Owner | When (America/New_York) | Engine run before it |
| --- | --- | --- | --- |
| [Career triage + drafts](#career-agent--weekday-triage--drafts) | Career Agent | Weekdays 8:00 AM | Jobs, daily 6:17 AM |
| [Hackathon deadlines + prep](#hackathon-captain--daily-deadlines--prep) | Hackathon Captain | Daily 8:30 AM | Hackathons, daily 6:37 AM |
| [Research: push one idea](#research-lead--monday-push-one-idea) | Research Lead | Mondays 9:00 AM | Research, Mondays 7:07 AM |
| [Sunday brief](#career-agent--sunday-brief) | Career Agent | Sundays 7:00 PM | Weekly brief, Sundays 6:07 PM |

**There's no Chief of Staff.** The Sunday brief is one weekly routine on the Career Agent. The Career Agent runs most often and receives every handoff, so it already has the context. To move the brief, delete the routine here and paste it into any one other Bot.

## How to create each one

Open a one-to-one chat with the owning Bot and paste the prompt. Grok Bot will confirm the owner, schedule, input, result, approval boundary and what to do when a source is missing. Use **Test run** once, then enable the routine. Set your time zone in Settings first.

Every routine follows the same stale-data rule: **if Notion is unreachable, or the engine added no row in the last 36 hours, report that and stop. Don't work from old data.** A missing engine run usually means a failed GitHub Action. Check the Actions tab.

---

### Career Agent · Weekday triage + drafts

```text
Every weekday at 8:00 AM America/New_York:
1. In the Notion Jobs database, read rows with Status = New added since the last run.
   Move rows with Score ≥ 70 and no hard-gate flag to Shortlist. Leave the rest at New.
   Never delete a row, and never hide a row because of a flag.
2. Run /career-deep-dive on up to 5 Shortlist rows, highest Score first.
3. Log any handoffs received since the last run (see /handoff-to-career).
4. Post one summary here: new rows, shortlisted, drafts ready (with Notion links), and any
   flags I need to decide on.
Approval boundary: do not send any message and do not submit any application. Drafts only.
If Notion is unreachable, or no Jobs row was added in the last 36 hours, report that and stop.
```

### Hackathon Captain · Daily deadlines & prep

```text
Every day at 8:30 AM America/New_York:
1. Run /captain-triage on Hackathons rows with Status = New and Score ≥ 50, up to 10.
2. For each Shortlist or Applying row with a deadline in the next 7 days: if it needs an
   application and isn't packed yet, run /captain-application-packer and stop before Submit.
3. For Applying or Building rows that allow teams and have no team yet, run
   /captain-team-up-scout.
4. Post one summary here: deadlines in the next 7 days (with timezone), forms waiting for my
   "submit", teammate drafts, and handoffs sent.
Approval boundary: never submit, register, RSVP, join a server or message anyone.
If Notion is unreachable, or no Hackathons row was added in the last 36 hours, report that and stop.
```

### Research Lead · Monday push one idea

```text
Every Monday at 9:00 AM America/New_York:
1. In the Notion Research database, list new CFP rows with deadlines, and new Idea rows with
   Reviewer 2's Verdict.
2. Pick ONE Idea to push one stage: New → Reading → Pursuing → Drafting. Prefer Verdict = Go
   with the nearest matched venue deadline. If it's Pursuing, run /research-experiment-runner.
   If it's Drafting and I have no arXiv endorsement, run /research-endorser-scout.
3. Post one summary here: the idea picked and why, what moved, open CFPs due in the next
   30 days, and anything that needs my decision (a Kill, a compute cost, an author email).
Approval boundary: never submit to arXiv, OpenReview or TMLR, never email anyone, and never
spend money on compute. Record only numbers produced by code that ran.
If Notion is unreachable, or no Research row was added in the last 8 days, report that and stop.
```

### Career Agent · Sunday brief

```text
Every Sunday at 7:00 PM America/New_York, run /weekly-brief across the Hackathons, Research
and Jobs databases. Create this week's page in the Notion Briefs database, then post its
summary in the War Room group chat (or here, if there's no War Room).
Approval boundary: read-only on the three boards. Create one Briefs page and never change Status.
If any database is unreachable, write the brief from the ones that work and name the one
that is missing at the top.
```

---

## Auto-Review rules (set once, in Settings → Approvals)

Set these to **Ask first**. Per xAI's docs, "Ask first" wins when two rules conflict.
- Sending email, DMs or messages, and connection requests
- Submitting any web form
- Publishing or posting
- Accepting terms, creating accounts, and payments
