# benchmark — Task 7 calibration record

One calibration pass, then frozen ([blind-llm-judge ADR](./adrs/blind-llm-judge.md),
[simulated-user ADR](./adrs/simulated-user.md)). Any later edit to the rubric, the
`needs_user_reply` heuristic, or the briefs reopens task 7.

Scenario: `plan-easy`, 4 arms, n=1. Three smoke runs; runs 1 and 2 are archived under
`results/calibration-run1/` and `results/calibration-run2/` (result.json, blinded judge
inputs/outputs, transcripts committed; raw HOME/workspace dirs local-only).

## Judge rubric — FROZEN, no wording change

Run 2 produced the first real judge outputs (run 1's judge calls failed on an infra
bug, see below). Evidence checked:

- Scores discriminate: plan_quality 88–92, verbosity_score 78–85 across arms, with
  the differences tracking observable content (openspec's unrequested `path` field,
  superpowers' unrequested execution-approach question).
- `outcome_notes` reference real fixture content (`build_parser`, `run`,
  `stats.summarize`, `top_words`) and real per-plan flaws — no hallucinated criteria.
- Blinding held: no arm identifier in any note; `./scripts/check-blinding.sh` clean
  over all saved judge inputs.

Verdict: rubric wording kept verbatim from task 5. Frozen.

## `needs_user_reply` heuristic — ONE fix, frozen

Run 1 evidence: the superpowers arm ended with a genuine question
("Which execution approach do you want?") heading a paragraph of option bullets,
followed by a recommendation paragraph. The v1 rule (final paragraph ends with "?")
returned False — a false continue; the simulator never answered (user_turns=0).
The ni arm's self-answered "Open question: … The plan says no." was correctly left
alone; no false stall observed on any arm.

Fix (single function, `harness/simulator.py::needs_user_reply`): approval-regex
window widened from the last 2 to the last 3 paragraphs, and question detection is
now line-level over those paragraphs (any line ending with "?"), so a question with
option bullets attached is caught while same-line rhetorical Q&A still is not.
Replayed against all four run-1 transcripts: baseline/openspec/ni False,
superpowers True. Unit tests cover both new cases. Frozen.

Known residual (observed in run 4, after the freeze — recorded, not fixed): a
question mark mid-line followed by same-line prose ("Does the plan capture what
you want? Once you've reviewed it, choose…") is not detected. The trial still
completes and grades as-is, which is the designed fallback; the limitation is
disclosed here rather than reopening the frozen heuristic.

## Simulator briefs — ONE fix, frozen

Run 2's single simulator exchange (superpowers): reply "Plan approved. your call,
decide and continue" — approval per the brief rule plus the brief-silent fallback,
no invented requirements.

Run 3 evidence: the baseline arm ended its plan with open questions; the simulator
approved but appended "go ahead with implementation" (superpowers likewise got
"Go ahead and implement it") — an invented instruction contradicting the brief
fact "implementation happens later". Both subjects then implemented
(files_changed 7) in a planning-only scenario, which the criteria penalise:
a simulator defect would have tanked those arms unfairly.

Fix (single pass, plan-family briefs): the approval rule in
`scenarios/plan-easy/brief.md` and `scenarios/plan-complex/brief.md` now states
that approval closes the task ("never ask for implementation now; it happens
later, outside this session"). Run 3 is archived under `results/calibration-run3/`.
Frozen.

## ni arm terse proof (deferred from task 2)

From the run-1 ni session log
(`calibration-run1/plan-easy/ni/…/home/.claude/projects/-workspace/*.jsonl`):
`Output Style: ni:terse` active and the per-prompt `NI TERSE full` banner injected.
Observed output is terse (compact bullet plan summary, no filler). Re-verified
in the final smoke run's ni session log (2 × `NI TERSE full`, output style
`ni:terse`; session logs live in the local, uncommitted trial HOME). Note:
`terse-activate.sh` logs a non-blocking `jq: command not found` in the arm image;
the level banner comes from the state-file hook and was injected regardless.

## Infra fixes surfaced by the smoke runs (not calibration items)

1. **Judge mount path** — `judge.sh` passed a relative results dir; docker `-v`
   rejects relative host paths, so every run-1 judge call died at container create
   (cost 0, all indeterminate). Fix: `judge_trial` resolves the trial dir.
2. **Artifact capture** — 3 of 4 arms wrote the plan at the workspace root, outside
   their conventional artifact glob: `plan_words=0` (which `min/value` scoring would
   reward with 100) and an artifact-less judge input. Fix: `artifact_metrics` unions
   the arm glob with the trial's changed `*.md` files — applied identically to every
   arm. The kpi-scoring ADR globs remain the expected locations; flagged for an ADR
   note at integration.
3. **HOME re-seed on resume** — `arm-entrypoint.sh` re-copied the template over the
   bind-mounted trial HOME on every container run; the resume turn (first exercised
   live in run 2) failed on the template's read-only git pack files. Fix: seed once,
   guarded by a `.arm-home-seeded` marker. Proven by running the superpowers
   container twice on one HOME.
4. **Judge wiring** — judging was not invoked by any script; added
   `harness.judge` CLI + `scripts/judge.sh`, called from `run.sh` after smoke and
   matrix (cost-guard partial exit still judges completed trials).

## Recorded spend (NFR2)

| Run | Purpose | Spend (USD) |
|---|---|---|
| smoke run 1 | first live run; judge infra bug found | 0.4428 |
| smoke run 2 | heuristic + judge fixes verified; first judged outputs | 0.5151 |
| smoke run 3 | resume loop proven; simulator brief defect found | 0.8667 |
| smoke run 4 | final clean smoke (results/plan-easy/) | 0.6892 |

Total task 7 spend: **2.51 USD** (cap: 50 × n = 50 USD, NFR2). All spend is
per-trial auditable in the committed `result.json` files (subject + simulator +
judge summed in `total_cost_usd`); the final run is also summed by
`./scripts/cost-check.sh`.
