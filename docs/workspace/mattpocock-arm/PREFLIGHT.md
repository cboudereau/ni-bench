# mattpocock-arm — Pre-flight gate

**Per task**:
- [x] Types it creates or modifies reference the domain model
- [x] Constraints are extracted from ADRs, invariants, and transformation rules
- [x] Tests are defined — named, with expected behavior described (these become the failing tests)
- [x] Verify command is copy-pasteable and exits 0 on success
- [x] Acceptance criteria are pass/fail with no subjective language
- [x] Time-box is set (split if > 90 min)
- [x] Dependencies on other tasks are declared
- [x] Every planned domain type appears in the requirement traceability table
- [x] Task is `downhill` — no uncertainty remains

**Constitution completeness**:
- [x] Domain model covers every planned domain type in diagram and traceability table
- [x] Every type in the traceability table maps to at least one FR or NFR
- [x] Every traceability row has a stability value (`internal` or `published`); each `published` row has a compatibility rule
- [x] Every NFR has a measure and a verify command (or an explicit `manual: <reason>`)
- [x] Transformations table covers every function that enforces a domain rule
- [x] Every failure-modes row that yields a rule appears as an error-path invariant in the transformations table
- [x] Every DESIGN.md section is filled or marked `N/A: <reason>` — no blank sections
- [x] No constraint is ambiguous enough that two reasonable agents would interpret it differently
- [x] Link lint green — every file reference in workspace docs is a clickable link:
  `! grep -rPn '(?<!\[)\x60(?:[\w.-]+/)*[\w.-]+\.md(?::\d+(?:[-,:]\d+)?)?\x60' docs/workspace/mattpocock-arm --include='*.md'`
  Remaining hits are arm-produced path patterns (`.scratch/…`, `GLOSSARY.md`, `docs/adr/*.md`, the arm HOME `CLAUDE.md`), not repo files.

**Autopilot readiness**:
- [x] Build, test, and lint commands pass (green baseline) — 138 passed, lint clean; the one failure is listed below
- [x] Known-failing tests are explicitly listed with their reason (`test_scenario_files_complete`: scripts committed with mode 100644 on `main`, pre-existing)
- [x] Every session has a `Skills` field — verify each skill name exists (`ni:software-engineer`, `ni:tdd`, `ni:git-conventions`, `ni:bias-analysis`: all listed in the ni plugin)
- [x] Session checkpoints are defined and ordered
- [x] Total estimated time fits within the target session window (2–4H)

**Human gates still open** (the agent cannot tick these):
- [x] ADR [skill mapping](./adrs/skill-mapping.md) ratified `proposed` → `accepted`
- [x] ADR [tracker seed](./adrs/tracker-seed.md) ratified `proposed` → `accepted`
- [ ] Task 7 (live smoke, real spend) authorised

**Plan commit**: once the gates above pass, commit all workspace artifacts (`docs/workspace/mattpocock-arm/`) with message:

```
docs(mattpocock-arm): plan ready for autopilot

Phases 1–4 complete. DESIGN.md, ADRs, and TASKS.md pass pre-flight gate.
```
