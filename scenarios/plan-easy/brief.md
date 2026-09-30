# plan-easy — user brief (simulated user only)

## Facts
- Goal: a plan for a `--json` flag on wordstats; implementation happens later.
- JSON output should contain, per file: name, lines, words, chars; when `--top N`
  is used, also the top words with their counts.
- Text output stays the default and must not change.
- JSON goes to stdout, one document per run (not one per file).
- Errors (missing file): keep the non-zero exit code; error text may stay on stderr.
- Standard library only — no new dependencies.

## Preferences
- Short, actionable plan; prefers a single markdown file.
- Wants test cases listed in the plan.

## Approval rule
Approve a plan (or plan proposal) once it covers the JSON shape, the default
staying text, and the test cases. Do not add requirements beyond the facts above.
When approving, say the plan is approved and the task is complete — never ask
for implementation now; it happens later, outside this session.
When asked something not covered here: "your call, decide and continue".
