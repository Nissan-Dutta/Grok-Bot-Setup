# Skill: `handoff-to-career`

**Owner:** Hackathon Captain and Research Lead (sender) → Career Agent (receiver)

This skill puts rule 3 into practice. When a hackathon sponsor or a paper's author works at a target company, the name goes to the Career Agent. Every handoff is recorded in the Notion **People** database, so it survives without a matching job and without anyone's chat history.

## When to use
- The Hackathon Captain finds a host, sponsor, judge or would-be teammate who works at a target company.
- The Research Lead finds a paper author or endorser candidate who works at a target company.
- "Target company" means the company appears in the Jobs database or in the target-company list in `/workspace/proof-pack/profile.md`.

## Inputs & access
- The person: name, public handle or profile URL, company, and role or team.
- The source: a link to the Notion row (a Hackathons or Research row).
- The hook: one specific, recent thing of theirs, such as the talk they're giving at the event or the table in their paper.
- Notion **People** database (read and write). Its properties are Name, Handle/URL, Company, Role, Source, Source row, Hook, Handed off (date), Linked jobs (relation to Jobs) and Key (company + handle).
- A Bot-to-Bot message to **@Career Agent**. Use the War Room group if it's open, otherwise a direct Bot message.

## Steps
1. **Check for duplicates (sender).** Search People for the same Key (company + handle). If the person is already there, add the new Source to their row if it's different, and stop. Don't send a message.
2. **Record (sender).** Create the People row. Leave Linked jobs empty.
3. **Send (sender).** Send one message per person, in exactly this format:
   ```
   HANDOFF
   Person: <name> (<handle / URL>) · <People row link>
   Company: <company> · Role: <role/team>
   Source: <Hackathon: event | Paper: title> · <Notion row link>
   Hook: <one specific thing, with link>
   ```
4. **Link (Career Agent).**
   - Find the Jobs rows for that company whose Status is New, Shortlist or Drafted.
   - Set the People row's Linked jobs to those rows, and append `<name> · <role> · via <source> · hook: <hook>` to each Jobs row's Contacts.
   - If there's no matching Jobs row, leave Linked jobs empty and reply "No open row for <company>. Kept in People."
   - Otherwise reply "Logged → <row link(s)>".
5. **Re-link later (Career Agent).** In each weekday routine, when a new Jobs row's Company matches a People row with empty Linked jobs, link the two and add the person to Contacts.

## Validate
- There's one People row per person, keyed on company + handle.
- One message per person, never a batch dump.
- The hook has a working link.
- The receiver confirmed with "Logged" or "Kept in People".

## Return
The sender adds "Handed off: <n>" to its run report. The People row and the receiver's reply are the audit trail.

## Needs approval
- None for the handoff itself, which is internal.
- Any contact with the person goes through the usual drafting skills and Nissan's approval.
