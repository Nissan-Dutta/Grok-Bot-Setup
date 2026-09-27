# Skill: `career-deep-dive`

**Owner:** Career Agent · **Sub-agent:** Deep Dive

## When to use
- On every Jobs row with Status = **Shortlist** that has no "Deep-dived" mark in Flags, during the weekday routine. Take the highest Score first, up to 5 per run.
- Also when Nissan says "deep dive <role>".

## Inputs & access
- The Notion row: URL, Score, Why (the Fit Scorer's angle), Flags, Contacts (from the Referral Mapper) and Draft (from the Outreach Drafter).
- The Bot browser, for the live posting and the team's public pages.
- `/workspace/proof-pack/profile.md` and `resume.pdf`.

## Steps
1. Open the live posting. If it's gone, set Status to **Closed** with the reason "posting removed" and move on.
2. Read the full description. Pull out the must-haves, the nice-to-haves, the team, location and remote rules, the visa and sponsorship language, and any enrollment or graduation-date requirement.
3. **Check the flags.** Confirm or correct each engine flag against the real text, and add any it missed. Never remove a row because of a flag. Flags are for Nissan to judge.
4. **Check the angle.** Is the Fit Scorer's "angle to lead with" the strongest match to the must-haves? If not, pick a better one and say why.
5. **Check the contacts.** For each Referral Mapper contact, confirm they're still on the team (X bio or recent posts) and that the hook is real and under 60 days old.
6. **Rewrite the draft,** following these rules:
   - Under 110 words, with one specific hook about their work.
   - One proof link: EvalCI, or the project that matches the angle.
   - A clear, small ask: a 15-minute call, or "who's the right person for X".
   - Start the first line with `[REWRITE: …]` and a suggestion. The first line is always Nissan's to write.
7. List 2–3 résumé bullet swaps that line up with the must-haves.
8. Update the row: Flags (add "Deep-dived <date>"), Why, Contacts and Draft. Then set Status to **Drafted**.

## Validate
- Every must-have from the posting either has a matching résumé bullet or is listed as a gap.
- The draft is under 110 words (count them), and its hook links to a real post or commit.
- Status is Drafted only if the posting is live.

## Return
```
Deep dive · <role> · <company> · Score <n>
Flags: <confirmed / corrected / new>
Angle: <angle> (<kept | changed: why>)
Contact: <name> · hook: <link>
Draft (<n> words): "<text>"
Résumé swaps: <1–3>
Gaps: <must-haves with no evidence>
```

## Needs approval
- Sending anything. Drafts only.
- Moving the row to Applied or Closed for any reason except "posting removed".
