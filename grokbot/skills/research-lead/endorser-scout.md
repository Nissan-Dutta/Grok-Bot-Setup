# Skill: `research-endorser-scout`

**Owner:** Research Lead · **Sub-agent:** Endorser Scout

## When to use
- When a Research row reaches **Drafting** and Nissan has no arXiv endorsement yet for the target category (cs.LG, cs.CL or stat.ML).
- Also when Nissan says "find endorsers for <row>".
- Background: since January 21, 2026, a first-time independent submitter needs a personal endorsement from an established author.

## Inputs & access
- The Notion row: the paper being reanalyzed, the Venue, and the draft abstract, if one exists.
- Public sources: arXiv listings, Semantic Scholar or OpenAlex citation graphs, and author homepages.
- arXiv's endorser rules for the category. Check the current page. Don't rely on memory.

## Steps
1. Build the candidate pool: authors who (a) have cited or published on the same benchmark or eval method, and (b) have enough recent papers in the target category to endorse under arXiv's current rules.
2. Drop the authors of the paper being reanalyzed, because of the conflict. Drop anyone with no public contact.
3. Rank by closeness: they cite the same paper, or they work on eval statistics (bootstrap, significance testing, benchmark reliability). Keep the top 5.
4. For the top 3, find one specific thing to reference: a paper of theirs and the result in it that relates to this work.
5. Draft one request per person, under 150 words. It should say who Nissan is in one line, what the paper shows in one line with the key number, why it's relevant to their work, and the ask: an endorsement for the category, with the draft attached. Make it easy to say no.
6. If an author works at a target company, also run `/handoff-to-career`.

## Validate
- Each candidate meets arXiv's current endorser threshold for the category. Link the evidence.
- Each draft names a real paper of theirs, with a working link.
- No candidate has a conflict with the paper under reanalysis.

## Return
```
Endorsers · <row> · category <cs.LG>
1. <name> · <affiliation> · eligible: <evidence link> · hook: <their paper> · draft: "<text>"
2. ...
3. ...
Backups: <names 4–5>
→ Reply with the number to send. I'll open the email draft for your click.
```

## Needs approval
- **Every email.** Drafts only.
- Sharing the manuscript with anyone.
