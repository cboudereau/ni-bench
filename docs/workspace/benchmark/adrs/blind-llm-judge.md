---
status: accepted
---
# Blind LLM judge plus deterministic checks

Addresses: [FR5](../DESIGN.md#fr5), [NFR4](../DESIGN.md#nfr4)

## Problem

Plan quality and verbosity are subjective; test outcomes are not. The grader must not favour a plugin by recognising its artifact style, and self-grading (subject model grading its own run) is a known bias source the superpowers-evals design explicitly avoids by separating Gauntlet-Agent from Coding-Agent.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. Blind LLM judge (fixed model, arm identifiers stripped) + deterministic post-checks | Quality scored on content, not brand; checks catch judge hallucination; matches Quorum design | Blinding is imperfect — artifact structure (e.g. `openspec/changes/` paths) can reveal the arm; rubric drift between runs |
| B. Deterministic checks only | Fully objective | Cannot score plan quality or verbosity at all — kills the two KPIs the user asked for |
| C. Human grading | Best judgment | Does not scale to 4 arms × 7 scenarios × n trials; not repeatable |

## Bias note (external evidence)

The only published plugin-benchmark numbers are sponsor-reported (superpowers author benchmarking superpowers). This ADR adopts their *method* (separate judge, withheld criteria, three-valued verdicts), none of their *results*. Structure blinding is best-effort: paths and tool names are rewritten to `ARM_WORKSPACE/` before judging, and the residual risk is stated in REPORT.md.

## Decision

Option A. Judge = `claude -p` in the dedicated plugin-free `harness` compose service (shared with the simulated user — see [simulated-user ADR](./simulated-user.md)) with a fixed model (`claude-sonnet-5-5`; settings pinned in the script) — never the arm container, and never the host CLI, whose `~/.claude` carries the operator's own plugins (ni terse would style the judge's reasoning). Input: scenario prompt, private acceptance criteria, blinded transcript and artifacts (arm names, plugin names, plugin-specific paths rewritten). Output: strict JSON `{plan_quality, verbosity_score, outcome_notes}` on 0–100 scales, one retry on parse failure. Deterministic post-checks (fixture test suite, expected-file existence) run in-container and override the judge on outcome KPIs: a `fail` on post-checks is a fail regardless of judge score. Rubric frozen after one smoke-run calibration pass.

## Consequences

Easier: repeatable scoring, NFR4 verifiable by grep, judge cost visible per trial. Harder: sonnet-level judgment on complex plans (accepted for cost; the model id is a single variable in `judge.sh` if the human prefers opus); blinding must be re-verified whenever a plugin changes its artifact layout.
