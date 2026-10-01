---
status: accepted
---
# Scenario matrix

Addresses: [FR2](../designs/benchmark.md#fr2), [FR9](../designs/benchmark.md#fr9), [NFR2](../designs/benchmark.md#nfr2)

## Problem

Scenarios must exercise what the three plugins claim to improve (planning, debugging, disciplined build), span easy to complex, stay affordable (NFR2 caps the matrix at 50 × n USD), and give the judge and post-checks something objective to grade. A fully home-grown suite has no external anchor; a fully ported suite inherits another project's bias.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. 5 home-grown scenarios: 2 plan (easy/complex), 2 debug (easy/complex), 1 build | Covers both requested families plus an end-to-end outcome anchor; neutral wording under our control | No external comparability; plan/debug families mirror ni's own skill names — a structural bias toward ni that must be disclosed |
| B. Port superpowers-evals `conversation-*`/`sdd-*` scenarios only | Proven scenarios, external anchor; multi-turn is no longer a blocker — the [FR8 simulated user](../designs/benchmark.md#fr8) handles it | Written to trigger superpowers skills — vocabulary and structure favour one arm; whole suite would carry that bias |
| C. Hybrid: the 5 home-grown scenarios plus 2 adapted superpowers-evals scenarios, labelled by origin | External anchor and neutral core; bias measured in both directions instead of avoided | +8 trials per n; porting effort; adapted scenarios lose exact comparability with published superpowers-evals numbers |
| D. 10+ scenarios incl. review, refactor | Broader | Blows NFR2 at n=3; more fixtures to maintain |

## Decision

Option C. The five home-grown scenarios from [FR2](../designs/benchmark.md#fr2), difficulty encoded structurally:

- `plan-easy`: single-file CLI fixture (~150 LOC), one FR, no design decision needed.
- `plan-complex`: forces at least two hard-to-reverse decisions (persistence choice, public-contract versioning) — plans that skip them lose completeness points.
- `debug-easy`: failing test names the broken function; planted single-line operator bug.
- `debug-complex`: bug report describes the symptom only ("totals drift after 100 items"); planted off-by-one crosses two modules; a symptom-masking fix passes the visible test but fails a hidden post-check test, so root-cause discipline is measurable.
- `build-small`: feature with 3 acceptance tests provided as prose; post-check runs the fixture suite plus hidden edge-case tests.

Plus two scenarios adapted from [superpowers-evals](https://github.com/prime-radiant-inc/superpowers-evals), tagged `origin: superpowers-evals` in the report:

- `ported-debug`: adapted from the `conversation-debugging` family — user-like conversation pressing for a quick fix; grading rewards root-cause discipline under pressure. Runs through the FR8 simulator.
- `ported-build`: adapted from the `sdd-*` build family (svelte-todo/fractals pattern, scaled down) — small end-to-end build with planted-defect-style hidden checks.

Adaptation rules: prompts rewritten to neutral vocabulary where wording names superpowers concepts (skill names, "brainstorm", "worktree") unless the wording is the test itself; acceptance criteria and check structure preserved; superpowers-evals licence verified before any content reuse — if incompatible, the scenarios are re-authored from the published descriptions, keeping only the behavioural shape.

Fixtures are small Python projects (pytest — no build step, fast in-container checks; `ported-build` may keep its original stack if the adaptation needs it). One fixture repo per scenario under `fixtures/`, committed with a green baseline (except `debug-easy`'s intended red test).

Bias handling per [FR9](../designs/benchmark.md#fr9): the analysis lists, per scenario, the expected bias direction (home-grown plan/debug → structurally ni-shaped; ported → superpowers-shaped) and reads results against it — an arm winning only where the structure favours it is a weaker signal than an arm winning against the grain.

## Consequences

Easier: each scenario keeps a deterministic anchor (hidden tests); the matrix gains an external reference point; bias becomes an analysed variable in both directions instead of a silent threat. Harder: matrix grows 5 → 7 scenarios (28 trials per n), cost cap raised 35 → 50 × n; two fixtures require adaptation work and a licence check; exact number-for-number comparison with published superpowers-evals results is still out of scope (different harness, judge, and models).
