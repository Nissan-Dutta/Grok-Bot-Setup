# Skill: `career-application-filler`

**Owner:** Career Agent · **Sub-agent:** Application Filler

## When to use
- When Nissan says "apply to <role>" on a Jobs row with Status = **Drafted**.
- Never on a schedule. Applications are Nissan's decision, one at a time.

## Inputs & access
- The Notion row: URL, the résumé swaps from the Deep Dive, and Flags.
- `/workspace/proof-pack/`: `resume.pdf` (or the tailored version Nissan names), `answers.md` (work authorization, start date, links, EEO preferences, salary stance) and `links.md`.
- The Bot browser, on the company's ATS (Greenhouse, Lever, Ashby, Workday). If an account is needed, the Bot hands Nissan control of the Agent Computer to log in.

## Steps
1. Open the posting's Apply page and list every field before filling anything in.
2. Fill the standard fields from `answers.md` exactly. Never guess work authorization, sponsorship, graduation date or salary. If `answers.md` has no answer, leave the field empty and list it.
3. Upload the résumé Nissan named, or `resume.pdf` by default.
4. For free-text questions ("Why <company>?"), draft from the row's Why and the Deep Dive angle, within the field's limit. Mark each one in the report so Nissan reads it.
5. Handle EEO and voluntary questions only as `answers.md` says. The default is "Decline to self-identify".
6. Go to the final review screen. **Stop before Submit.**
7. Save every answer to the Notion row as an "Application draft" toggle.

## Validate
- No field contradicts `answers.md` or the Flags. For example, a posting that refuses sponsorship must not get a "needs sponsorship: no" unless that's true.
- Every required field is filled in or listed.
- The form is on the review step and not submitted. Take a screenshot to show this.

## Return
```
Application · <role> · <company>
Filled <n>/<total> · Missing: <list>
Free-text answers to read: <quoted>
Résumé: <file>
Form: <URL>, left open on the review step · Screenshot attached
→ Reply "submit" to approve. After you submit, I'll set Status to Applied.
```

## Needs approval
- **Submit.** Always. Only an explicit "submit" from Nissan in this chat approves it.
- Creating an ATS account, accepting terms, and uploading any file outside the proof pack.
