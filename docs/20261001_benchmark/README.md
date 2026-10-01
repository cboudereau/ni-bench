# benchmark

Benchmark comparing Claude Code plugins (baseline, openspec, superpowers, ni) on 7 scenarios in isolated Docker arms, with a blind LLM judge, a simulated user, and deterministic post-checks. Integrated 2026-10-01.

Deliverables at repo root: [REPORT.md](../../REPORT.md) (generated KPI tables, matrix n=3) and [ANALYSIS.md](../../ANALYSIS.md) (bias table, baseline comparison, recommendations, disclosures). Setup: [SETUP.md](../../SETUP.md).

## Design

- [benchmark design](designs/benchmark.md) — context, FR1–FR9, NFR1–NFR4, failure modes, architecture

## ADRs (accepted)

- [Isolation: docker compose with throwaway HOME](adrs/isolation-docker-compose.md)
- [Blind LLM judge plus deterministic checks](adrs/blind-llm-judge.md)
- [Scenario matrix](adrs/scenario-matrix.md)
- [KPI set and scoring normalisation](adrs/kpi-scoring.md)
- [Per-plugin verbosity policy](adrs/verbosity-policy.md)
- [Simulated user for multi-turn interaction](adrs/simulated-user.md)

## Audit

- [CALIBRATION.md](CALIBRATION.md) — frozen rubric, question-detection heuristic, brief fixes, infra bugs found during smoke
- Reported run: `results/matrix-v2/` (84 trials, 0 indeterminate, 10.81 USD); discarded pre-fix run kept locally, see ANALYSIS.md disclosures
