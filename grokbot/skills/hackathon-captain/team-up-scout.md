# Skill: `captain-team-up-scout`

**Owner:** Hackathon Captain · **Sub-agent:** Team-up Scout

## When to use
- On a Hackathons row with Status = Applying or Building, when the event allows teams and Nissan hasn't marked "Team: solo" in Flags.
- Also when Nissan says "find a team for <event>".

## Inputs & access
- The Notion row: URL and Plan. The Plan's 48-hour plan says which skills the build needs.
- `/workspace/proof-pack/profile.md`, for Nissan's skills. The gaps are what the Plan needs minus what the profile covers. Typical gaps are frontend, design, hardware or domain data.
- Public sources only: the event's X posts and their replies, the Devpost "participants" or "looking for team" pages, and the event's public Discord channels. Read Discord only if Nissan is already a member.

## Steps
1. Write down the gap list, 2–4 skills at most.
2. Find people who have publicly said they're joining or looking for a team at this event.
3. For each person, check public work: GitHub, a past Devpost project, X posts. Keep a person only if they have shipped something that covers a gap.
4. Rank them by gap coverage, then by overlap with target companies. Someone who works at a target company is a bonus: run `/handoff-to-career`.
5. Draft one intro per person, under 70 words. It must mention one thing they built, name the gap they'd fill, and link EvalCI.

## Validate
- 2–3 people, no more.
- Each person has a public link that shows the gap skill.
- No private data. Only what the person posted publicly.

## Return
```
Team-up · <event>
Gaps: <list>
1. <name / handle> · covers <gap> · proof: <link> · draft: "<intro>"
2. ...
→ Reply with the numbers to send. I'll open each DM and wait for your click.
```

## Needs approval
- **Every message.** The skill drafts and never sends.
- Joining a Discord server or a team on Devpost.
