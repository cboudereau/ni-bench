# plan-complex — user brief (simulated user only)

## Facts
- Goal: an implementable plan for the Orion pricing API client; no code yet.
- Team: two developers, Python 3.11, standard library plus small well-known
  dependencies are acceptable.
- Cache: must survive process restarts; single machine; quotes may be served up
  to 15 minutes stale; roughly 50k quotes at peak.
- Rate limit: hard 60 requests/minute per credential; 429 carries Retry-After.
- Consumers: three internal teams install from the internal package index and
  pin exact versions; they need advance notice of breaking changes.
- No async requirement; batch jobs are sequential.

## Preferences
- Boring, proven technology over clever solutions.
- Wants the plan to state the trade-offs it rejected.

## Approval rule
Approve a plan (or plan proposal) once it makes the persistence decision and the
contract-versioning decision explicitly and covers rate-limit/retry handling.
Do not add requirements beyond the facts above. When approving, say the plan is
approved and the task is complete — never ask for implementation now; it happens
later, outside this session. When asked something not covered
here: "your call, decide and continue".
