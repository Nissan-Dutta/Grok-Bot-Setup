# Skill: `research-experiment-runner`

**Owner:** Research Lead · **Sub-agent:** Experiment Runner

## When to use
- On a Research row of Type = Idea with Verdict = **Go** (or **Fix**, once the fix is noted), when Nissan moves it to Pursuing.
- Also when Nissan says "run <idea>".
- Run one idea at a time. Compute and attention are the bottleneck.

## Inputs & access
- The Notion row: the Paper URL, Summary (the Gap Hunter's claim and why it's weak) and the Reviewer 2 notes (the experiment that could kill the idea).
- The Bot computer: terminal, Python, and `/workspace/evalci` (EvalCI, cloned from Nissan's repo).
- Public artifacts only: the paper's released predictions, per-item outputs, code and data (GitHub, Hugging Face, the paper's supplementary files).

## Steps
1. Create `/workspace/experiments/<row-key>/` containing `README.md`, `repro/` and `reanalysis/`.
2. **Find the data.** Locate the per-item results the paper's claim depends on. If there's no per-item data, stop here. Set Verdict to **Kill** with the reason "no per-item data released" and report.
3. **Reproduce.** Recompute the paper's headline numbers from the released data. Record paper number, your number and the difference in `repro/table.csv`. If the difference is more than 0.5 points, stop and report it. That mismatch may be a finding in itself.
4. **Reanalyze with EvalCI.**
   - 95% bootstrap CIs, with at least 10,000 resamples, for each system's score.
   - McNemar's test on paired per-item correctness for each claimed improvement.
   - Seed variance, if multiple seeds were released.
   - Record every command in `reanalysis/commands.sh`, and record the EvalCI commit hash and the seed.
5. **Decide.** For each claimed gain, label it holds (the CI excludes 0 and p < 0.05 after Holm correction), fragile, or does not hold. Don't round in the paper's favor.
6. Write the results to the Notion row: a Summary line, a link to the experiment folder, and the Verdict. Leave it at Go if the result is worth a paper. Change it to Kill if every gain holds and there's nothing to report.

## Validate
- Every number in Notion appears in a file under `/workspace/experiments/<row-key>/` that code produced.
- `commands.sh` reruns end-to-end and gives the same numbers, because the seed is fixed.
- The reproduction difference is recorded, even when it's 0.

## Return
```
Experiment · <paper short title>
Repro: <k>/<n> headline numbers match (max diff <x>)
Reanalysis: <n> claimed gains → <a> hold · <b> fragile · <c> don't hold
Most interesting: "<claim>": <CI>, McNemar p=<p>
Folder: /workspace/experiments/<row-key>/ · EvalCI @ <commit>
Suggested next: <Drafting | park | extend to <paper B>>
```

## Needs approval
- Spending money on compute, such as a GPU rental or paid API calls.
- Emailing the paper's authors, including to ask for missing data.
- Moving the row to Drafting. Nissan does that.
- **Never:** writing prose claims for a paper, or recording any number that code didn't produce.
