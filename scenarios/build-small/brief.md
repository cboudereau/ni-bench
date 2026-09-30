# build-small — user brief (simulated user only)

## Facts
- Goal: `parse_duration` in `timefmt.py`, matching the written specification;
  whole suite green.
- Seconds are returned as a plain `int`.
- Zero counts are legal inside a valid string (`0s` is 0; `1h0m` is 3600).
- Leading/trailing whitespace is invalid — the feed is already trimmed.
- No new dependencies.

## Preferences
- Tests written before the implementation.
- Small, readable implementation over clever one-liners.

## Approval rule
Approve when the three acceptance cases are automated tests and the suite is
green. Do not add requirements beyond the facts above. When asked something not
covered here: "your call, decide and continue".
