# Origin: superpowers-evals, sdd build family (scaled down)

- Origin repo: https://github.com/prime-radiant-inc/superpowers-evals (Quorum)
- Family: `sdd-*` end-to-end builds (svelte-todo / fractals pattern), scaled
  down to a single-module Python build per the scenario-matrix ADR.

## Licence finding (checked 2026-09-30)

- No LICENSE / LICENSE.md / LICENSE.txt file exists in the repository root
  (verified via raw.githubusercontent.com — 404 — and the GitHub contents API).
- The GitHub API reports `"license": null` for the repository.
- No licence grant means all rights reserved: content reuse, even with
  attribution, is not permitted.

## Adaptation route taken

Per the scenario-matrix ADR rule for an absent/incompatible licence, this
scenario was **re-authored from the behavioural shape only**, as published in
the repository's public description and README overview (spec-driven
end-to-end build graded against acceptance criteria plus deterministic,
planted-defect-style hidden checks). The todo-list subject matter follows the
published `sdd` fixture naming (svelte-todo) as behavioural shape; no prompt
text, fixture code, criteria, or check content was copied. The stack is
Python per the ADR — the adaptation does not require the original stack.
Prompt vocabulary is neutral per the ADR (no plugin concept names). The
report tags this scenario `origin: superpowers-evals` for the behavioural
anchor, not for shared content.
