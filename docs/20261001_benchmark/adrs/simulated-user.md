---
status: accepted
---
# Simulated user for multi-turn interaction

Addresses: [FR8](../designs/benchmark.md#fr8), [NFR2](../designs/benchmark.md#nfr2), [NFR4](../designs/benchmark.md#nfr4)

## Problem

Plan-family plugins are interactive by design: Claude Code plan mode asks for approval, OpenSpec `/opsx:propose` asks clarifying questions, ni expects ADR ratification. A single-shot `claude -p` run either stalls on these gates or forces the agent to self-answer, biasing the benchmark against interaction-driven workflows. The subject needs a counterpart that answers questions the way a consistent, minimal user would — identically across arms.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. LLM simulated user fed a per-scenario user brief, multi-turn via `claude -p --resume` | Arms get identical user behaviour; handles free-form questions; Quorum-proven pattern (Gauntlet-Agent) | Second LLM per turn adds cost; simulator could leak invented facts |
| B. Canned scripted answers keyed by question pattern | Deterministic, free | Free-form questions never match; brittle across four different plugin phrasings |
| C. Auto-approve everything ("yes, proceed") | Trivial | Cannot answer content questions; rewards plugins that ask nothing |
| D. Stay single-shot, prompt says "do not ask questions" | No new code | Suppresses the differentiator under test; measures prompt compliance, not plugin workflow |

## Decision

Option A. The `simulated_user` step runs in a dedicated `harness` compose service — the plugin-free base image, its own throwaway `$HOME` — never in an arm container and never on the host: the host `claude` CLI loads the operator's real `~/.claude` (including the ni plugin and its terse output style), which would pollute the simulator with one of the arms under test. Fixed cheap model (`claude-haiku-4-5-20251001`) and a per-scenario **user brief**: the facts a real user would know (goal, constraints, preferences), plus standing rules — answer only from the brief; when the brief is silent, reply "your call, decide and continue"; approve plan/proposal gates when the plan addresses the brief's goal; never introduce new requirements. Loop: subject runs `claude -p --output-format json`; while the final message asks a question or awaits approval and the artifact/post-check target is not met, the simulator produces the next user message and the subject resumes via `claude -p --resume <session-id>`; cap 6 user turns, then the trial is graded as-is. The same brief text serves all arms verbatim.

Accounting: simulator tokens/cost are tracked per trial and count toward the [NFR2](../designs/benchmark.md#nfr2) total spend, but are excluded from the subject's `tokens_total`/`cost_usd` KPIs. New KPI `user_turns` (raw count, lower better, `min/value` scoring) enters the [kpi-scoring ADR](./kpi-scoring.md) table. Simulator transcripts are stored in the trial dir and pass through the same blinding before judging ([NFR4](../designs/benchmark.md#nfr4)).

## Consequences

Easier: interactive plugins measured on their intended workflow; question economy becomes a visible KPI; identical user behaviour across arms. Harder: runner becomes a loop with turn detection (heuristic: unanswered question or explicit approval request in the final message — calibrated on the smoke run and frozen with the rubric); simulator spend and extra subject turns are absorbed by the NFR2 cap (now 50 × n USD with the 7-scenario matrix — see [scenario-matrix ADR](./scenario-matrix.md)).
