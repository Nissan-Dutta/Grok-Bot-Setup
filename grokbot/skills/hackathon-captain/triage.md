# Skill: `captain-triage`

**Owner:** Hackathon Captain · **Sub-agent:** Triage

## When to use
- On every Hackathons row with Status = New and Score ≥ 50, during the daily routine. Skip rows whose Flags already start with "Unclear": they wait for Nissan, so they can't fill the 10-row limit every day.
- Also when Nissan says "triage <event>".
- Work through rows highest Score first, up to 10 rows per run.

## Inputs & access
- The Notion **Hackathons** row: Event name, URL, Score, Why, Plan, Flags, Deadline, Dates, Format, Host.
- The Bot browser, for the real event page. No login is needed; if a page needs one, stop and flag it.
- `/workspace/proof-pack/profile.md`, for age, location, student status, visa and travel limits.

## Steps
1. Open the row's URL. If it redirects or returns a 404, search for the event name and host. Use the official page only: Devpost, the host's domain, lablab.ai or Luma.
2. Pull the real facts from the page: registration deadline (with timezone), event dates, format and location, eligibility (age, country, student-only, team size), cost, travel support, sponsors, judges and prize.
3. Compare them with the row. Correct Deadline, Dates and Format when the page disagrees, and add "Corrected: <field>" to Flags.
4. Check each hard gate:
   - In person with no travel support, outside a city Nissan can reach → **Skipped**.
   - Country or age eligibility fails → **Skipped**.
   - Deadline is less than 48 hours away and it's a gated application → **Skipped**, unless Score ≥ 85. Then ask Nissan.
5. If a fact needed for a gate is missing or ambiguous on the page, write `Unclear <date>: <what>` at the start of Flags, leave the row at New, and move on. Nissan resolves it by answering the question or editing the row. After that, remove the flag and triage the row again.
6. If every gate passes, set Status to **Shortlist** and write a one-line reason in Why.
   Example: "Shortlist: Anthropic judges, online, 12 days runway."
7. For each host, sponsor or judge who works at a target company, run `/handoff-to-career`.

## Validate
- The row's Deadline matches the page, timezone included.
- Every Skipped has a reason that names the gate that failed.
- No row went from New to Applying. Triage only sets Shortlist or Skipped, and it sets **Status changed** to today whenever it changes Status.
- Rows flagged Unclear were not triaged again.

## Return
Post one message in the Bot's chat:
```
Triage · <date>
Shortlisted (n): <event> · <deadline> · <one-line why> · <Notion link>
Skipped (n): <event> · <gate that failed>
Unclear (n, waiting on you): <event> · <what's unclear> · since <date>
Handoffs sent: <n>
```

## Needs approval
- Skipping a row with Score ≥ 85.
- Anything that registers, RSVPs, joins a server or accepts terms. This skill never does these.
