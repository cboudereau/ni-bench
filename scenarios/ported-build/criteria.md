# ported-build — private acceptance criteria (judge only)

Origin: superpowers-evals `sdd-*` build family, scaled down and re-authored
(see ORIGIN.md). The scenario measures disciplined end-to-end building against
a written specification; the hidden checks probe the spots where rushed builds
typically plant defects.

Score:
1. **Spec fidelity** — every clause implemented as written: id monotonicity
   across removals, `ValueError` on blank titles, `KeyError` on unknown ids,
   no-op re-completion, insertion order, `clear_done` return count, counter
   surviving persistence.
2. **Test discipline** — the agent writes its own behaviour tests beyond the
   shipped smoke test, covering the specified behaviours as real assertions,
   ideally before the code they test.
3. **Persistence quality** — the JSON format stores the counter explicitly (or
   derives it safely as max-id, stated deliberately); load failures are not
   silently swallowed.
4. **Scope discipline** — no CLI, no extra features, no new dependencies; the
   deliverable is the specified module plus tests.

Deterministic outcome comes from the post-check (visible suite plus hidden
planted-defect checks); this rubric grades process and spec discipline.
