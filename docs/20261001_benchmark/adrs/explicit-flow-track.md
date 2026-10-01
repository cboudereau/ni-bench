# ADR: Explicit-flow follow-up track (per-arm prompt variants)

Status: accepted (user-ordered 2026-10-01)

## Problem

Under the byte-identical one-shot prompts of the main matrix, no plugin arm
invoked its canonical workflow headless: ni never created `docs/workspace/**`,
openspec never ran an `/opsx:` command or created `openspec/changes/**`, and
superpowers wrote a root `PLAN.md` instead of following its plan convention
(headless artifact-dir finding, ANALYSIS.md disclosures). The matrix therefore
measured "plugin instructions present", not "authored workflow exercised" —
the canonical flows stayed dormant, and the comparison cannot say what the
workflows themselves are worth.

## Decision

Run a follow-up track with explicit flow invocation per arm:

- Each plugin arm gets a prompt variant `scenarios/<id>/prompt-<arm>.md`:
  the scenario prompt plus exactly one arm-specific line naming the arm's own
  canonical workflow (ni: the `ni:plan` skill workflow; openspec: the
  OpenSpec `/opsx:` workflow; superpowers: its planning skill workflow).
- Baseline keeps the plain `prompt.md` as the control — it has no canonical
  workflow to name.
- Prompt resolution in the harness prefers `prompt-<arm>.md` and falls back
  to `prompt.md` (`harness/scenarios.py::arm_prompt_path`); the judge keeps
  reading the shared `prompt.md`, so every trial is graded against the same
  task statement.
- Scope: the plan family only (`plan-easy`, `plan-complex`), where the
  canonical flows matter most. Results land under `results/explicit-v1`,
  rendered to a separate report — the frozen main REPORT.md is untouched.

## Consequence

Prompts are no longer byte-identical across arms. The instruction shape is
the same — one appended line, each naming only the arm's own tool — but the
explicit track is a different experiment from the implicit one, and the
comparability caveat is disclosed in the explicit-track report. Blinding is
unchanged: the appended line names the plugin, the existing NFR4 blocklist
redacts every identifier it can introduce, and the judge input stays clean
(verified by unit tests over the variant files and by
`scripts/check-blinding.sh` over the run's judge inputs).
