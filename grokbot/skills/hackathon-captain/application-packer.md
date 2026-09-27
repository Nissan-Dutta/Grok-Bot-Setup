# Skill: `captain-application-packer`

**Owner:** Hackathon Captain · **Sub-agent:** Application Packer

## When to use
- On a Hackathons row with Status = Shortlist whose event needs an application: a form, an essay, a video or a portfolio link.
- Also when Nissan says "pack <event>".

## Inputs & access
- The Notion row: URL, Plan (the Strategist's pitch and 48-hour plan) and Why.
- `/workspace/proof-pack/`: `resume.pdf`, `bio.md` (3 lines), `answers.md` (standard answers), `links.md` (EvalCI, agent-eval-harness, GitHub, X, demo video) and `headshot.jpg`.
- The Bot browser. If the form needs an account, use secure handoff so Nissan logs in. Never create an account yourself.

## Steps
1. Set the row's Status to **Applying**.
2. Open the application form and list every field, including optional ones, before filling anything in.
3. Fill each field from the proof pack. For open questions, write from the row's Plan:
   - "What will you build?" → the Strategist's pitch, tied to EvalCI or agent-eval-harness.
   - "Why you?" → one concrete shipped thing with a link, not adjectives.
   - Keep each answer within the form's limit. Where no limit is given, aim for about 120 words.
4. If a field asks for something that isn't in the proof pack, leave it empty and list it. Examples: a new video, a reference, or a claim about the future.
5. Scroll to the end. **Stop before Submit.** Don't click Submit, Next-to-review-and-submit or Accept terms.
6. Save a copy of every answer to the Notion row as a "Draft application" toggle, so the answers survive if the form times out.

## Validate
- Every required field is either filled in or listed as missing.
- No answer claims a result, award or affiliation that isn't in the proof pack.
- The form is still open and not submitted. Take a screenshot to show this.

## Return
```
Packed · <event> · deadline <date, tz>
Filled: <n>/<total> fields · Missing: <list>
Answers to review: <the 2–3 long answers, quoted>
Form: <URL>, left open on the Bot computer · Screenshot attached
→ Reply "submit" to approve, or edit the answers first.
```

## Needs approval
- **Submit.** Always. Only an explicit "submit" from Nissan in this chat approves it.
- Accepting terms, uploading anything outside the proof pack, and creating accounts.
