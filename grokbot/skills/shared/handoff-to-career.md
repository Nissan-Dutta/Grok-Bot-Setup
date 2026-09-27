# Skill: `handoff-to-career`

**Owner:** Hackathon Captain and Research Lead (sender) → Career Agent (receiver)

This skill puts rule 3 into practice. When a hackathon sponsor or a paper's author works at a target company, the name goes to the Career Agent.

## When to use
- The Hackathon Captain finds a host, sponsor, judge or would-be teammate who works at a target company.
- The Research Lead finds a paper author or endorser candidate who works at a target company.
- "Target company" means it appears in the Jobs database or in the target-company list in `/workspace/proof-pack/profile.md`.

## Inputs & access
- The person: name, public handle or profile URL, company, role or team.
- The source: a link to the Notion row (a Hackathons or Research row).
- The hook: one specific, recent thing of theirs. For example, the talk they're giving at the event, or the table in their paper.
- A Bot-to-Bot message to **@Career Agent**. Use the War Room group if it's open, otherwise a direct Bot message.

## Steps
1. **Check for duplicates** (sender). Search the Jobs database Contacts for the person's name or handle. If they're already there with this source, stop.
2. **Send** one message per person, in exactly this format:
   ```
   HANDOFF
   Person: <name> (<handle / URL>)
   Company: <company> · Role: <role/team>
   Source: <Hackathon: event | Paper: title> · <Notion row link>
   Hook: <one specific thing, with link>
   ```
3. **Receive** (Career Agent):
   - Find the Jobs rows for that company with Status in New, Shortlist or Drafted.
   - Append to Contacts: `<name> · <role> · via <source> · hook: <hook> · <date>`.
   - If there's no row, reply "No open row for <company>, noted" and keep the handoff for the Sunday brief's "People without a role yet" list.
   - Reply "Logged → <row link(s)>".

## Validate
- One message per person, never a batch dump.
- The hook has a working link.
- The receiver confirmed with "Logged" or "No open row".

## Return
The sender adds "Handed off: <n>" to its run report. The receiver's reply is the audit trail.

## Needs approval
- None for the handoff itself, which is internal.
- Any contact with the person goes through the usual drafting skills and Nissan's approval.
