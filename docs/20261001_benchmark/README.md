# benchmark

Benchmark comparing Claude Code plugins (baseline, openspec, superpowers, ni, mattpocock) on 7 scenarios in isolated Docker arms, with a blind LLM judge, a simulated user, and deterministic post-checks. Integrated 2026-10-01.

Deliverables are per-run local artifacts (git-excluded): each run folder under .reports/ holds its trials, REPORT.md, and ANALYSIS.md. Setup and usage: [README.md](../../README.md).

## Design

- [benchmark design](designs/benchmark.md) — context, FR1–FR9, NFR1–NFR4, failure modes, architecture
- [mattpocock arm design](designs/mattpocock-arm.md) — fifth arm (added 2026-10-16): skill mapping, headless tracker seed, artifact classification, blinding

## ADRs (accepted)

- [Isolation: docker compose with throwaway HOME](adrs/isolation-docker-compose.md)
- [Blind LLM judge plus deterministic checks](adrs/blind-llm-judge.md)
- [Scenario matrix](adrs/scenario-matrix.md)
- [KPI set and scoring normalisation](adrs/kpi-scoring.md)
- [Per-plugin verbosity policy](adrs/verbosity-policy.md)
- [Simulated user for multi-turn interaction](adrs/simulated-user.md)
- [Explicit-flow follow-up track (per-arm prompt variants)](adrs/explicit-flow-track.md)
- [Two-audience quality: split KPIs, dual judge scores, resumability](adrs/two-audience-quality.md) — proposed
- [Fifth arm: mattpocock-skills skill mapping and install source](adrs/mattpocock-skill-mapping.md)
- [Fifth arm: headless tracker seed in the throwaway HOME](adrs/mattpocock-tracker-seed.md)

## Audit

- [CALIBRATION.md](CALIBRATION.md) — frozen rubric, question-detection heuristic, brief fixes, infra bugs found during smoke
- Reported run: `.reports/matrix-v2/` (84 trials, 0 indeterminate, 10.81 USD) — local only, like all run artifacts; discarded pre-fix run kept locally, see the run ANALYSIS.md disclosures
- Fifth-arm smoke runs (2026-10-16, plan-easy, n=1, local only): `run-20261016-134506` (prose-named skills, mattpocock reported them "not installed", 0.88 USD) and `run-20261016-135318` (slash-command entry, grilling round answered by the simulator in 1 user turn, spec plus 3 tickets under `.scratch/`, 0.92 USD); both 5/5 pass, 0 indeterminate, blinding ALL CLEAN; `run-20261016-135819` (4/5: mattpocock fail, grilling round missed by the frozen question heuristic, user_turns 0, see CALIBRATION second fix, 0.67 USD); `run-20261016-140243` after the fix (5/5 pass, mattpocock 2 user turns, human_readability 88, 1.07 USD)
