# debug-complex — user brief (simulated user only)

## Facts
- Goal: large-ledger grand totals must match the true sum; reconciliation green.
- Symptom: only ledgers over 100 entries drift, always lower, gap grows with
  size; small ledgers are exact.
- Batched processing must stay — downstream export consumes per-batch subtotals.
- Existing tests are trusted and must keep passing; adding tests is welcome.
- No data or infrastructure changed recently.

## Preferences
- Wants the actual defect fixed, not a workaround in reporting.
- Wants a regression test for the failure mode.

## Approval rule
Approve a fix once the cause is identified and corrected where it lives and a
regression test exists. Do not reveal file names or the defect location — the
facts above are all you know. When asked something not covered here: "your
call, decide and continue".
