---
status: proposed
---
# Two-audience quality: split artifact KPIs, dual judge scores, resumability

Addresses: [FR5](../designs/benchmark.md#fr5), [FR6](../designs/benchmark.md#fr6) — amends [kpi-scoring](./kpi-scoring.md) and [blind-llm-judge](./blind-llm-judge.md)

## Problem

Planning plugins produce artifacts for two audiences: documents humans read (design docs, ADRs, proposals) and documents for the agent (task checklists, preflight gates) whose purpose is crash-, compaction-, and rate-limit-proof execution. The current KPIs collapse them: `plan_quality` grades one document for one reader, `plan_words` sums every produced markdown file. Run-20261001-154633 measured the consequence: arms shipping a machine layer (ni 785–2 927 words, openspec 200–713) are billed for it as verbosity while no KPI measures the resumability it buys; arms shipping none (baseline, superpowers) are flattered. A second defect surfaced: the artifact glob counted `openspec init` tooling scaffolding (`.claude/commands/`, `.claude/skills/`, ~27k words) as plan content, corrupting openspec's `plan_words` cells.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. Split artifact classification + dual judge scores + deterministic resume KPI | Measures both the cost and the return of the machine layer, symmetrically for every arm | Rubric change (re-judge needed); resume KPI needs new runner machinery |
| B. Exclude machine-layer files from all KPIs | Cheap | Hides the cost instead of weighing it; still no return measured |
| C. Keep as-is, disclose | No work | Structurally blind to a design dimension two of four arms invest in |

## Decision

Option A, in two stages.

**Stage 1 — measurement and judging (re-judge of existing runs allowed):**
- Per-arm artifact classification in `harness/arms.py`: every produced markdown path classed `human` (design docs, ADRs, proposals, plans), `machine` (task checklists, preflight files), or `excluded` (tooling scaffolding: `.claude/**`, generated command/skill files, anything the plugin's init writes unprompted).
- KPIs: `plan_words` becomes the human-layer count (lower better, unchanged formula); new raw column `machine_words` (reported, not scored — its value is scored through resumability, not word count).
- Judge rubric v2: two scores for every arm — `human_readability` (is the human layer complete, correct, and brief for its decisions) and `agent_executability` (could a fresh agent execute from the machine+human layers alone: self-contained tasks, verify commands, progress tracking). Replaces the single `plan_quality` in the quality-floor rule with `human_readability`; `verbosity_score` unchanged. Rubric re-frozen after one calibration pass.

**Stage 2 — resumability KPI (next benchmark iteration):**
- Deterministic kill-and-resume postcheck for plan/build scenarios: run the subject, kill it at a fixed budget mid-implementation, start a fresh session with only the disk artifacts and a neutral "continue" prompt, measure completion without re-asking the user. Pass/fail enters `outcome`-style scoring; applies identically to all arms. (Equivalent in intent to superpowers-evals' plan-resume and compaction-survival scenarios.)

## Consequences

Easier: the machine layer's cost and return are both measured, for every arm; openspec's corrupted `plan_words` cells are fixed by the `excluded` class; the quality floor stops double-counting narration brevity against process documentation. Harder: one paid re-judge per existing run to compare (~84 sonnet calls, a few USD); stage 2 adds runner machinery (budgeted kill, second session) and lengthens build scenarios; classification lists need maintenance when plugins change their layouts.
