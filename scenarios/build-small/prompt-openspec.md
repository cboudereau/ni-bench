# Task

Add a `parse_duration(text)` function to `timefmt.py` in this project — the
inverse of the existing `format_duration`.

Specification:
- Input is a compact duration string using the units `h`, `m`, `s`, each with a
  non-negative integer count, each unit at most once, in `h` then `m` then `s`
  order. At least one unit must be present.
- Returns the total number of seconds as an `int`.
- Anything else is invalid — an empty string, a number without a unit, an
  unknown unit, repeated units, or units out of order — and raises `ValueError`.

Acceptance tests (as agreed with the team):
1. `parse_duration("90s")` returns `90`.
2. `parse_duration("1h30m")` returns `5400`.
3. `parse_duration("blah")` raises `ValueError`.

Work test-first: add automated tests for the behaviour to the suite alongside
the implementation. The whole suite must pass when you are done.

Use the OpenSpec workflow (/opsx:) to drive this implementation.
