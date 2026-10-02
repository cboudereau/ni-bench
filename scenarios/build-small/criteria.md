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

Deterministic outcome comes from the post-check (visible suite plus hidden
edge-case tests); this rubric grades process and spec discipline.
