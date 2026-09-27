# Skill: `career-linkedin-mapper`

**Owner:** Career Agent · **Sub-agent:** LinkedIn Mapper

## When to use
- On a Jobs row with Status = **Drafted** or **Shortlist** and Score ≥ 70, when the X contacts are thin (fewer than 2 people) or Nissan asks for "a warm route".
- Also when Nissan says "map <company>".
- At most one session per day, covering up to 5 companies.

## Inputs & access
- The Notion row: Company, the team named in the posting, and existing Contacts.
- **Nissan's LinkedIn login, through Grok Bot's secure browser handoff.** Nissan types the password and completes 2FA. The Bot never sees, stores or reuses the credential.
- `/workspace/proof-pack/profile.md`, for schools (UWC, Goucher) and past orgs.

## Steps
1. Ask Nissan to start the secure handoff and log in. Wait for confirmation.
2. For each company, run at human speed: pause at least 5 seconds between page loads, and view at most 40 profiles per session.
   - Alumni: search people at <company> who went to UWC or Goucher.
   - Mutuals: search people at <company> who are 2nd-degree connections, then note the shared connection.
   - Team: prefer people whose headline or experience matches the posting's team.
3. For each strong route, record the name, title, the route ("UWC alum", "mutual: <name>") and the profile URL.
4. Pick the best route per company. Prefer, in order: a mutual who knows Nissan well, then an alum on the team, then an alum at the company, then a 2nd-degree connection on the team.
5. Append the routes to the row's Contacts, tagged "LinkedIn · <date>". Don't overwrite X contacts.
6. Log out when finished.

## Validate
- **Read-only held.** No connection requests, messages, likes, follows, endorsements, settings changes or profile edits. Check the activity log before logging out.
- The profile limit and the delays were respected.
- Every contact has a profile URL.

## Return
```
LinkedIn map · <date> · <n> companies · <m> profiles viewed
<company>: best route: <name>, <title>, via <route> · <n> others added to Contacts
...
→ Want an intro-request draft to <mutual> for any of these?
```

## Needs approval
- Starting the login handoff, every time.
- **Any write on LinkedIn.** This skill never does one. An intro request is drafted here, and Nissan sends it.
