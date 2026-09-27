# Skill: `weekly-brief`

**Owner:** Career Agent. The brief can move to any one Bot, but only one Bot should own it.

This is the Sunday brief. It replaces the old Chief of Staff Bot.

## When to use
- The Sunday 7:00 PM routine.
- Also when Nissan says "brief me".

## Inputs & access
- Notion: read the **Hackathons**, **Research**, **Jobs** and **People** databases, and create one page in **Briefs**.
- Each row's **Status**, **Status changed** (date), **Score**, **Deadline** and **Found**. Jobs rows have a Deadline only when the posting states one.
- **Last week's Briefs page**, especially its "Status snapshot" table. This is how the brief knows what moved this week.

## Steps
1. **Snapshot and diff.** Record every non-final row's key, board, Status and Score. Final statuses are Submitted, Skipped, Parked, Offer and Closed. Compare this with last week's "Status snapshot" to get the list of rows whose Status moved this week. If there's no snapshot from last week, as in the first week, say "No baseline yet" and skip steps 5 and 7.
2. **Moves.** Pick the top 3 next actions for this week on each board. Rank by **Score × urgency**:

   | Deadline | Urgency |
   | --- | --- |
   | Due in 0–3 days | 4 |
   | Due in 4–7 days | 3 |
   | Due in 8–14 days | 2 |
   | Due in more than 14 days, or no Deadline | 1 |
   | Past deadline | Excluded |

   Each move is one verb and one row, for example "Pack Grokathon application (due Thu)".
3. **Deadlines.** List every non-final row with a Deadline in the next 14 days, on any board, sorted by date and with timezones. Jobs rows without a Deadline aren't listed here. Step 4 covers them.
4. **Stale.** List rows in Shortlist, Applying, Building, Reading, Pursuing, Drafting or Drafted where **Status changed** (or **Found**, if Status changed is empty) is 7 or more days old. Suggest "push" or "park" for each.
5. **What Nissan acted on.** Count only the moves that need Nissan, taken from the step 1 diff:
   - Hackathons → Submitted
   - Research → Pursuing or Drafting
   - Jobs → Applied, Interview or Offer
   - Any board → Skipped, Closed or Parked from Shortlist or later

   Moves the Bots make on their own don't count: New→Shortlist, Shortlist→Drafted, Shortlist→Applying and New→Reading.

   For each board, compare the average engine Score of the rows Nissan advanced with the average Score of the rows the Bots put in front of Nissan that week but Nissan passed on. If the advanced rows don't score higher, say the rubric weights in `config.yaml` need retuning, and name the factor where the two groups differ most.
6. **People without a role yet.** List the People rows with an empty Linked jobs field. Flag any whose company now has an open Jobs row.
7. **Last week's plan.** Say which of last week's 9 moves happened.
8. **Write the page.** Create the Briefs page `Weekly brief · <YYYY-MM-DD>` with sections 2–7, and put the step 1 snapshot at the end as a table titled "Status snapshot". Post the top of the page to the War Room, or to this chat if there's no War Room.

## Validate
- Every item links to its Notion row.
- No listed deadline is in the past, and every deadline has a timezone.
- Counts and movements come from Notion (Status changed plus the snapshot diff), not from memory or chat history.
- The snapshot table has one row for every non-final row.

## Return
Post in the War Room (or this chat):
```
Sunday brief · <date> · <Notion link>
This week: <3 moves per board, 9 lines>
Due ≤14 days: <n> · Stale: <n> · You advanced: <n> (<rubric note>)
People without a role: <n>
```

## Needs approval
- None. The brief is read-only on the boards and creates one Briefs page.
- The brief never changes Status. It only suggests.
