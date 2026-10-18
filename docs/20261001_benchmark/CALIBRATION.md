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

Second fix (2026-10-16, fifth arm, reopened on new evidence): the mattpocock arm's
grilling round numbers every question under the "❓" marker, answers each with a
"➡️" recommendation, and closes with a sentence ("Once you've answered, I'll
check…"). No line in the last three paragraphs ends with "?", so run-20261016-135819
scored user_turns=0, no artifact, a harness-caused fail; run-20261016-135318 passed
only because its last question happened to sit inside the window. Rule added in
`needs_user_reply`: a line headed by "❓" anywhere in the message counts as awaiting
the user. Replayed over all 15 first turns of the three fifth-arm smoke runs: the
only verdict that changes is 135819/mattpocock (False → True); every other arm and
run keeps its verdict. Two unit tests cover the round-with-closing-line case and a
"❓" inside prose (no reply). Frozen again.

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
later, outside this session"). Run 3 is archived under `.reports/calibration-run3/`.
Frozen.

Second fix (2026-10-18, reopened on new evidence): run-20261018-070444
plan-complex/superpowers. The subject ended turn 1 with its execution-approach
gate; the simulator approved per the brief, answered the uncovered questions with
the fallback, then appended "Start with Task 1." Turn 2 became a subagent-driven
implementation (16 Agent launches, a `.worktrees/` checkout) and was killed at the
1200 s trial budget: indeterminate, and the killed turn's spend is not in the
total. The brief fix closed "go ahead with implementation" but not "start with
task N". Rule added to `STANDING_RULES` in `harness/simulator.py`: never tell the
assistant to start, implement, execute, or proceed with any task or step unless
the brief explicitly says so; when the brief says the work happens later, approve
and stop. Replayed the saved gate message through the simulator three times with
the new rule (haiku-4-5, 0.006 to 0.013 USD each): replies approve, answer the
TTL and per-credential facts from the brief, send the fallback for the uncovered
questions and for the execution approach, and none instructs the assistant to
start or implement anything ("Task is complete" in one). Frozen again.

Third fix (2026-10-18, same run, trial 3 of the same cell): the simulator gave
no "Start with" instruction but answered the superpowers execution gate
("subagent-driven or native?") with the fallback "your call, decide and
continue" and omitted "task is complete"; superpowers then built the whole
library natively (36 files) and was killed at 1200 s. Trial 2 of the cell got
"Task is complete" and the arm stopped: that phrase is what closes the gate.
Rule added to `STANDING_RULES`: when the brief says the work happens later, an
execution question is not a brief gap; answer that implementation is outside
this session and the task ends with the approved plan; never pick an approach.
Replay of the trial-3 gate, Haiku 4.5 with the new rule: 3/3 say "Task is
complete", 2/3 still add "execution approach: your call". Same prompt on
`claude-haiku-5-5`: 3/3 decline execution explicitly ("no execution approach is
needed here", "Don't start any tasks") and keep the fallback for the brief gaps;
0.016 USD per reply after the first (0.13 USD, cache creation). Simulator model
switched to `claude-haiku-5-5`; the 2.1.285 CLI logs `unrecognized_model` on
stderr and serves it. Frozen again.

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
| smoke run 4 | final clean smoke (.reports/plan-easy/) | 0.6892 |

Total task 7 spend: **2.51 USD** (cap: 50 × n = 50 USD, NFR2). All spend is
per-trial auditable in the committed `result.json` files (subject + simulator +
judge summed in `total_cost_usd`); the final run is also summed by
`./scripts/cost-check.sh`.
