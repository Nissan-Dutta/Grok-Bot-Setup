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

## Rules every routine follows

- **Notion unreachable → report and stop.** Don't work from memory.
- **Check whether the engine ran.** Read the Notion page "Engine status". The engine updates it on every run with the time and row counts for each pipeline. Get the time of this Bot's pipeline's last successful run:
  - 36 hours or more ago (8 days for Research): **put a warning at the top of the summary** ("Engine hasn't run since <time>. Check the GitHub Actions tab"), then **carry on with the rows already in Notion**.
  - A successful run that added 0 rows is a quiet day. Keep working.
  - Deadlines on existing rows never wait for the engine.
- **Status changes carry a date.** Whenever a Bot changes Status, it also sets **Status changed** to today. The Sunday brief uses this date to find stale rows.

---

### Career Agent · Weekday triage + drafts

```text
Every weekday at 8:00 AM America/New_York:
1. In the Notion Jobs database, read every row with Status = New and Score ≥ 70, not only
   rows added since the last run. Move each one to Shortlist and set Status changed to today.
   Flags never block this step. Rows with flags go to Shortlist too, and are listed in the
   summary for me to judge. Leave rows under 70 at New and report how many there are.
   Never delete a row, and never hide a row because of a flag.
2. Run /career-deep-dive on up to 5 Shortlist rows, highest Score first.
3. Log any handoffs received since the last run (see /handoff-to-career). Then link People
   rows with an empty Linked jobs field to any new Jobs row for the same company.
4. Post one summary here: new rows, rows shortlisted (flagged ones first, with their
   flags), drafts ready (with Notion links), and the count of rows left at New.
Approval boundary: do not send any message and do not submit any application. Drafts only.
If Notion is unreachable, report that and stop. If the "Engine status" page shows no
successful Jobs run in 36 hours, put a warning at the top of the summary and continue with
the rows already in Notion.
```

### Hackathon Captain · Daily deadlines & prep

```text
Every day at 8:30 AM America/New_York:
1. Run /captain-triage on up to 10 Hackathons rows with Status = New and Score ≥ 50. Skip rows
   already flagged "Unclear". Those wait for my answer and are listed in the summary.
2. For each Shortlist or Applying row with a deadline in the next 7 days: if it needs an
   application and isn't packed yet, run /captain-application-packer and stop before Submit.
3. For Applying or Building rows that allow teams and have no team yet, run
   /captain-team-up-scout.
4. Post one summary here: deadlines in the next 7 days (with timezone), forms waiting for my
   "submit", teammate drafts, rows waiting on me (Unclear), and handoffs sent.
Approval boundary: never submit, register, RSVP, join a server or message anyone.
If Notion is unreachable, report that and stop. If the "Engine status" page shows no
successful Hackathons run in 36 hours, put a warning at the top of the summary and still do
steps 1–4 on the existing rows. Deadlines don't wait for the engine.
```

### Research Lead · Monday push one idea

```text
Every Monday at 9:00 AM America/New_York:
1. In the Notion Research database, list new CFP rows with deadlines, and new Idea rows with
   Reviewer 2's Verdict.
2. Move new Idea rows with Verdict = Go from New to Reading, and set Status changed. This is
   the only Status move you make on your own.
3. Pick ONE Idea and do the next step for its stage. Prefer Verdict = Go with the nearest
   matched venue deadline.
   - Reading: recommend whether to pursue it, with reasons. Moving it to Pursuing is my call.
   - Pursuing: run /research-experiment-runner.
   - Drafting, and I have no arXiv endorsement yet: run /research-endorser-scout.
4. Post one summary here: the idea picked and why, what moved, open CFPs due in the next
   30 days, and anything that needs my decision (moving a row to Pursuing or Drafting, a
   proposed Kill, a compute cost, an author email).
Approval boundary: only I move an Idea to Pursuing, Drafting, Submitted or Parked, and only I
set Verdict to Kill. Never submit to arXiv, OpenReview or TMLR, never email anyone, and never
spend money on compute. Record only numbers produced by code that ran.
If Notion is unreachable, report that and stop. If the "Engine status" page shows no
successful Research run in 8 days, put a warning at the top of the summary and continue.
```

### Career Agent · Sunday brief

```text
Every Sunday at 7:00 PM America/New_York, run /weekly-brief across the Hackathons, Research,
Jobs and People databases. Create this week's page in the Notion Briefs database, then post
its summary in the War Room group chat (or here, if there's no War Room).
Approval boundary: read-only on the boards. Create one Briefs page and never change Status.
If any database is unreachable, write the brief from the ones that work and name the one
that is missing at the top.
```

---

## Auto-Review rules (set once)

Open **Settings → General → Bot → Auto-review** and add these as **Ask first** rules. Per xAI's docs, "Ask first" wins when two rules conflict. Keep them narrow. A rule like "any web form" would also stop the Bots at every search box.
- Sending any email, DM, message or connection request
- Submitting an application, registration or sign-up form
- Publishing or posting anywhere, including X, Discord and LinkedIn
- Accepting terms, creating accounts, and any payment
