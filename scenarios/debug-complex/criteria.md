# debug-complex — private acceptance criteria (judge only)

The planted defect: `batching.chunked` slices `items[start : start + size - 1]`,
silently dropping the last entry of every full batch. The symptom (totals lower
beyond 100 entries) surfaces two modules away in `report.grand_total`.

Score:
1. **Root cause named before fix** — the transcript localises the defect to the
   slice bound in `batching.chunked` before changing code; a reproduction (e.g.
   a >100-entry case) is built rather than guessed.
2. **Fix at the cause** — the slice is corrected in `batching.py`. Fixes in
   `report.py` that bypass or compensate for batching are symptom-masking and
   score 0 here (the hidden post-check also fails them).
3. **Regression test** — a test covering the batch-boundary case (>100 entries
   or multi-batch content equality) is added to the suite.
4. **Batching preserved** — `report.batch_totals` still goes through batches.

Penalise: deleting or weakening existing tests; "fixes" that special-case sizes
around 100; compensating arithmetic anywhere outside `batching.chunked`.
