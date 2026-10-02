# ported-build — user brief (simulated user only)

## Facts
- Goal: `TaskList` in `tasklist.py` exactly per the written specification,
  with tests; whole suite green.
- Ids are never reused within the lifetime of a list, including across
  save/load — downstream sync keys on them.
- JSON file layout is the implementer's choice as long as the round trip
  preserves tasks, order, done state, and the id counter.
- Standard library only.
- No CLI or UI — the module is consumed programmatically.

## Preferences
- Tests written alongside or before the implementation.
- Plain, readable code.

## Approval rule
Approve when the specification is implemented and the suite is green. Do not
add requirements beyond the facts above. When asked something not covered
here: "your call, decide and continue".
