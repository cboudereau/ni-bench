# plan-easy — private acceptance criteria (judge only)

Score the produced plan document on:

1. **Completeness** — covers: flag wiring in the argument parser; the JSON output
   shape (per-file summary; how `--top` word lists appear in JSON); error handling
   in JSON mode (missing files, exit code); text output unchanged as default.
2. **Testability** — names concrete test cases (JSON shape assertion, default
   unchanged, error path) that could be written before the implementation.
3. **Traceability** — plan items reference the actual files/functions of the
   fixture (`cli.py`, `run`, `build_parser`, `stats.summarize`), not invented ones.
4. **Actionability** — steps are small, ordered, and implementable without
   further decisions; no vague "handle output" items.
5. **Scope discipline** — no implementation code beyond illustrative snippets;
   no unrequested features (config files, new dependencies, other formats).

Penalise: plans that implement the change instead of planning it; plans that
invent requirements the user never gave; plans that ignore the `--top` interaction.
