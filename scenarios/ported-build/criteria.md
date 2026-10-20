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
5. **Slices** — the commit log, when there is one, shows each commit making
   one `TaskList` behaviour work end to end with its test, the first commit
   being the thinnest path (add and items); a single commit at the end, or
   commits by layer, scores low on this item. No commit log: score this item
   from the transcript's stated order of work.
6. **Autonomy** — the run finishes the task on its own, commit included, with
   no step deferred to the user. A closing offer such as "say if you want me
   to commit" or "tell me if you want the tests split" is a deferred step and
   scores low on this item, the same as a mid-task question would; a genuine
   blocker named with its reason is not.

A plan, notes, or tracker file the arm wrote is a process artifact: its git
status (committed, staged, or untracked) is not scored under any item.

Deterministic outcome comes from the post-check (visible suite plus hidden
planted-defect checks); this rubric grades process and spec discipline.
