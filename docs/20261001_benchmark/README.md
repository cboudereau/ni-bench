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

## Open enhancements

- **Two-stage execution scenario.** Every build scenario plans and executes in one session with one model, so a plugin's claim that its task list carries a weaker executor is never tested. Stage 1: the arm plans with the run's `ANTHROPIC_MODEL`. Stage 2: a fresh session, no `--resume`, executes from the workspace artifacts alone with `claude-haiku-5-5`. KPIs: postcheck pass, commits per task, `user_turns` in stage 2. Needs a per-stage model in the runner (the compose pass-through of `ANTHROPIC_MODEL` already exists) and a scenario field naming the stage-2 prompt. Until then the proxy is `ANTHROPIC_MODEL=claude-haiku-5-5 BENCH_SCENARIOS=build-small,ported-build ./scripts/bench.sh` against the sonnet run of the same scenarios.
- **Build-row trophy threshold.** The replication pair run-20261018-181207 / run-20261019-095458 (same ni skills, same rubric) moved build-scenario `agent_executability` by 10 (ni) and 15 (mattpocock) points with no skill change; plan and debug rows moved 0 to 3. The README promotion rule (gap over 5 on a judge row) should require a gap over 10 on build rows.
- **Tool-call capture.** The judge reads the subject's final message plus the commit log and workspace diff; `claude -p --output-format json` keeps no tool calls, so red and green runs are claims in every arm. `--output-format stream-json` would let the judge verify them.

## Audit

- [CALIBRATION.md](CALIBRATION.md) — frozen rubric, question-detection heuristic, brief fixes, infra bugs found during smoke
- Reported run: `.reports/matrix-v2/` (84 trials, 0 indeterminate, 10.81 USD) — local only, like all run artifacts; discarded pre-fix run kept locally, see the run ANALYSIS.md disclosures
- Current reference run: `.reports/run-20261020-110011/` (105 trials, 0 indeterminate, rubric v2.2, ni 2.2.0+local.e472763) — local only; its ANALYSIS.md carries the bias table, the affiliation disclosure, and the ni version table across nine runs. Promoted to the ni README on 2026-10-20; the build gain reproduces in run-20261019-193123, run-20261020-092358, and this run.
- Fifth-arm smoke runs (2026-10-16, plan-easy, n=1, local only): `run-20261016-134506` (prose-named skills, mattpocock reported them "not installed", 0.88 USD) and `run-20261016-135318` (slash-command entry, grilling round answered by the simulator in 1 user turn, spec plus 3 tickets under `.scratch/`, 0.92 USD); both 5/5 pass, 0 indeterminate, blinding ALL CLEAN; `run-20261016-135819` (4/5: mattpocock fail, grilling round missed by the frozen question heuristic, user_turns 0, see CALIBRATION second fix, 0.67 USD); `run-20261016-140243` after the fix (5/5 pass, mattpocock 2 user turns, human_readability 88, 1.07 USD)
