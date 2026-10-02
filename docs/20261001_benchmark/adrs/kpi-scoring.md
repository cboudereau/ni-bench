---
status: accepted
---
# KPI set and scoring normalisation

Addresses: [FR4](../designs/benchmark.md#fr4), [FR6](../designs/benchmark.md#fr6), [FR7](../designs/benchmark.md#fr7), [NFR3](../designs/benchmark.md#nfr3)

## Problem

The report shows, per scenario, a percent score and the raw value for every KPI. Percent needs a fixed formula; mixing "lower is better" (tokens) and "higher is better" (quality) invites ad-hoc math that changes between runs and breaks NFR3's determinism in spirit.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. Best-arm ratio for resource KPIs, absolute rubric for quality KPIs, pass-rate for outcomes | Simple, explainable in one line per KPI; best arm always 100% | Resource scores are relative — a new arm changes other arms' percents |
| B. Min-max normalisation across arms | Uses full 0–100 range | Worst arm always 0% even when close; unstable with 4 arms |
| C. Absolute budgets per KPI (e.g. 50k tokens = 100%) | Arm-independent | Budgets are arbitrary; wrong per scenario difficulty |

## Decision

Option A. KPI set and formula per scenario table:

| KPI | Raw source | Direction | Score formula |
|---|---|---|---|
| `tokens_total` | subject `claude -p` JSON usage (input+output, cache reads counted; simulator excluded) | lower better | `min(arms)/value × 100` |
| `cost_usd` | `total_cost_usd` | lower better | `min(arms)/value × 100` |
| `duration_s` | `duration_ms / 1000` | lower better | `min(arms)/value × 100` |
| `turns` | `num_turns` | lower better | `min(arms)/value × 100` |
| `user_turns` | simulated-user replies consumed ([simulated-user ADR](./simulated-user.md)) | lower better | `min(arms)/value × 100`; value 0 scores 100 |
| `plan_words` | `wc -w` over the arm's plan artifact glob (plan scenarios only) | lower better | `min(arms)/value × 100` |
| `plan_quality` | blind judge rubric | higher better | judge value (already 0–100) |
| `verbosity_score` | blind judge: signal density — facts kept per word spent | higher better | judge value |
| `outcome` | deterministic post-checks (hidden tests, root-cause named) | higher better | pass-rate over n trials × 100 |

Aggregation over n trials: median for raw resource KPIs and judge scores, pass-rate for `outcome`. Indeterminate trials excluded from medians, counted in an `indeterminate` footnote row. `plan_words` scores only among arms whose `plan_quality ≥ 50` — a one-word plan must not win the verbosity KPI. Arm artifact globs: ni `docs/workspace/**/*.md`, openspec `openspec/changes/**/*.md`, superpowers its plan file convention (fixed during implementation), baseline any `*.md`/plan text the run produced.

## Consequences

Easier: every cell in REPORT.md is `score% (raw)` with one formula lookup; report generation is pure arithmetic over `result.json`, satisfying NFR3. Harder: resource percents are relative to this arm set — stated in the report header; the quality-floor rule for `plan_words` needs one extra join in the aggregator.
