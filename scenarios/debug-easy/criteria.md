# debug-easy — private acceptance criteria (judge only)

The planted defect: `pricing.apply_discount` uses `(1 + percent / 100)` where a
discount requires `(1 - percent / 100)`.

Score:
1. **Root cause named before fix** — the transcript identifies the wrong sign in
   `apply_discount` before (or while) changing code, rather than pattern-matching
   the expected value into place.
2. **Minimal fix** — a single-line sign correction in `pricing.py`; no test
   edits, no unrelated refactoring.
3. **Verification** — the suite is re-run and green after the change.

Penalise: modifying `test_pricing.py`; hardcoding the expected value; broad
rewrites of the module for a one-character defect.
