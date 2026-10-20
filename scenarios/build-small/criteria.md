# build-small — private acceptance criteria (judge only)

Score:
1. **Tests first** — the transcript shows behaviour tests written (and run red,
   or at least written) before or alongside the implementation, covering the
   three agreed acceptance cases as real assertions.
2. **Spec coverage** — the implementation honours the full stated spec, not
   only the three examples: single units (`2h`, `45m`), combined values,
   rejection of empty strings, unit-less numbers, unknown units, repeated
   units, and out-of-order units.
3. **Integration** — `parse_duration` lives in `timefmt.py`; existing
   `format_duration` behaviour and tests untouched and green.
4. **Code quality** — no over-engineering (no new dependencies, no parser
   framework for a three-unit grammar).
5. **Slices** — the commit log, when there is one, shows each commit making
   one behaviour of `parse_duration` work end to end with its test; a single
   commit at the end, or commits by layer, scores low on this item. No commit
   log: score this item from the transcript's stated order of work.
6. **Autonomy** — the run finishes the task on its own, commit included, with
   no step deferred to the user. A closing offer such as "say if you want me
   to commit" or "tell me if you want the tests split" is a deferred step and
   scores low on this item, the same as a mid-task question would; a genuine
   blocker named with its reason is not.

A plan, notes, or tracker file the arm wrote is a process artifact: its git
status (committed, staged, or untracked) is not scored under any item.

Deterministic outcome comes from the post-check (visible suite plus hidden
edge-case tests); this rubric grades process and spec discipline.
