# Task

Plan a Python client library for the internal "Orion" pricing API. Requirements:

- The API allows 60 requests per minute and answers `429` with a `Retry-After`
  header when the limit is hit. The client must respect both.
- Transient failures (`5xx`, timeouts) need a retry policy.
- Price quotes must be cached locally and the cache must survive process
  restarts (the tool runs as short-lived batch jobs on one machine).
- The library is consumed by three downstream teams that pin released versions:
  its public contract must be versioned, with a stated compatibility policy.

Produce a written plan document (markdown file in the workspace) that a developer
could implement from: architecture, the persistence choice for the cache, the
rate-limit and retry handling, the public-contract versioning strategy, a test
strategy, and an ordered task breakdown. Do not implement — planning only.

Use your superpowers planning skill workflow for this plan.
