# plan-complex — private acceptance criteria (judge only)

Two hard-to-reverse decisions MUST be explicitly made, not deferred:

1. **Persistence choice for the cache** — a concrete mechanism is chosen
   (e.g. SQLite, JSON file, dbm…), with at least one alternative considered and
   a reason tied to the stated constraints (short-lived batch jobs, single
   machine, restart survival). "Use some storage" or "TBD" scores 0 on this item.
2. **Public-contract versioning** — a concrete policy is chosen (e.g. semver
   with defined breaking-change rules), including what counts as the public
   contract, how breaking changes are signalled to the three pinning teams, and
   how compatibility is tested. A bare "use semver" without rules scores low.

Then score:

3. **Completeness** — rate-limit handling (60/min and 429+Retry-After both
   addressed), retry policy with bounds (max attempts/backoff), cache
   invalidation or staleness stance, error surface of the client.
4. **Testability** — test strategy names how rate limiting and retries are
   tested without the real API (fakes/clock control), and cache persistence
   round-trip tests.
5. **Actionability** — ordered task breakdown small enough to implement from.

Penalise: implementation instead of a plan; ignoring either hard decision;
invented requirements (multi-machine cache, async rewrite) not asked for.
