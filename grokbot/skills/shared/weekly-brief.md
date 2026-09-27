# Skill: `weekly-brief`

**Owner:** Career Agent. The brief can move to any one Bot, but only one Bot should own it.

This is the Sunday brief. It replaces the old Chief of Staff Bot.

## When to use
- The Sunday 7:00 PM routine.
- Also when Nissan says "brief me".

## Inputs & access
- Notion: the **Hackathons**, **Research** and **Jobs** databases (read), and the **Briefs** database (create one page).
- The last 7 days of handoff messages to the Career Agent.
- Last week's Briefs page, for what was planned versus what happened.

## Steps
1. **Moves.** For each board, pick the top 3 next actions for this week. Rank by Score × urgency, where urgency is days to the deadline. Each move is one verb and one row.
   Example: "Pack Grokathon application (due Thu)."
2. **Deadlines.** List every row across the 3 databases with a Deadline in the next 14 days whose Status is not final (Submitted, Skipped, Parked, Applied, Offer or Closed). Sort by date.
3. **Stale.** List rows whose Status hasn't changed in 7 days or more while in Shortlist, Applying, Building, Pursuing, Drafting or Drafted. Suggest "push" or "park" for each.
4. **Acted-on.** Count the rows Nissan moved past Shortlist this week, per board, and give their average engine Score against the board average. If the acted-on rows don't score higher, say the rubric weights in `config.yaml` need retuning, and name the factor that looks off.
5. **People without a role yet.** List this week's handoffs that had no open Jobs row.
6. **Last week's plan.** Say which of last week's 9 moves happened.
7. Create the Briefs page `Weekly brief · <YYYY-MM-DD>` with sections 1–6. Post the top of it to the War Room, or to this chat if there's no War Room.

## Validate
- Every item links to its Notion row.
- The deadlines include timezones and none are in the past.
- The counts come from Notion queries, not memory.

## Return
Post in the War Room (or this chat):
```
Sunday brief · <date> · <Notion link>
This week: <3 moves per board, 9 lines>
Due ≤14 days: <n> · Stale: <n> · Acted on: <n> (<rubric note>)
```

## Needs approval
- None. The brief is read-only on the three databases and creates one Briefs page.
- The brief never changes Status. It only suggests.
