# Task

Bug report from the finance team about this ledger reporting project:

> Our reconciliation keeps failing on large ledgers. For ledgers with more than
> 100 entries, the grand total in the report comes out lower than the bank
> statement — and the gap grows as the ledger gets bigger. Ledgers under 100
> entries reconcile fine. Nothing in our data changed.

The test suite is currently green. Investigate, find the cause, and fix it.
The batched processing must stay: downstream export consumes the per-batch
subtotals.

Use your superpowers systematic-debugging skill workflow for this investigation.
