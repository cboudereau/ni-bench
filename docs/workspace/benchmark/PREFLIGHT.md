# benchmark — Pre-flight gate

**Per task**:
- [x] Types it creates or modifies reference the domain model
- [x] Constraints are extracted from ADRs, invariants, and transformation rules
- [x] Tests are defined — named, with expected behavior described (these become the failing tests)
- [x] Verify command is copy-pasteable and exits 0 on success
- [x] Acceptance criteria are pass/fail with no subjective language
- [x] Time-box is set (task 3 pre-split home-grown/ported; task 8 wall-clock excluded, active time boxed)
- [x] Dependencies on other tasks are declared
- [x] Every planned domain type appears in the requirement traceability table
- [x] Task is `downhill` — no uncertainty remains (plugin-install and openspec-headless risks carry documented fallbacks with time caps)

**Constitution completeness**:
- [x] Domain model covers every planned domain type in diagram and traceability table
- [x] Every type in the traceability table maps to at least one FR or NFR
- [x] Every traceability row has a stability value; the single `published` row (REPORT.md format) has a compatibility rule (additive only)
- [x] Every NFR has a measure and a verify command
- [x] Transformations table covers every function that enforces a domain rule
- [x] Every failure-modes row that yields a rule appears as an error-path invariant in the transformations table
- [x] Every DESIGN.md section is filled or marked `N/A: <reason>`
- [x] No constraint is ambiguous enough that two reasonable agents would interpret it differently
- [x] Link lint green — verified 2026-09-30

**Autopilot readiness**:
- [x] Build, test, and lint commands pass — greenfield repo: commands are created by task 1 and enforced from the Session 1 checkpoint onward; nothing pre-exists to run
- [x] Known-failing tests explicitly listed (`fixtures/debug-easy` intended red)
- [x] Every session has a `Skills` field — `software-engineer`, `tdd`, `debug`, `bias-analysis` all exist in the ni plugin
- [x] Session checkpoints are defined and ordered
- [x] Total estimated time fits session windows (S1 ~3H, S2 ~3H, S3 ~2.5H active)

Gate passed 2026-09-30. ADRs ratified (6/6 accepted). Plan committed before implementation.
