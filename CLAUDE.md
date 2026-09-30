# ni-bench

Benchmark harness comparing Claude Code planning/workflow plugins (openspec, superpowers, ni) on identical tasks in isolated Docker environments.

## Active workspaces
- [benchmark](docs/workspace/benchmark/TASKS.md) — Phase 5, task 3/8 (Session 1)
  RESUME: load the `plan` skill, then read TASKS.md (checked = done) + `git log --oneline`;
  continue at first unchecked task; re-run the session checkpoint before trusting state.
