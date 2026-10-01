# Task

Build the task-list module of this project end to end: implement the
specification below in `tasklist.py` as a `TaskList` class, with automated
tests in the suite.

Specification:
- `add(title)` creates a task and returns its integer id. Ids start at 1 and
  increase by 1 per added task. Ids are **never reused**, even after tasks are
  removed. An empty or whitespace-only title raises `ValueError`.
- `complete(task_id)` marks the task done. An unknown id raises `KeyError`.
  Completing an already-done task is a no-op.
- `items()` returns the current tasks as a list of dicts
  `{"id": int, "title": str, "done": bool}` in insertion order.
- `clear_done()` removes all completed tasks and returns how many it removed.
- `save(path)` / `load(path)`: JSON persistence. `load` is a classmethod (or
  equivalent) returning a `TaskList`; a save/load round trip preserves tasks,
  their order, their done state, **and the id counter** — ids must not restart
  or collide after loading.

The whole test suite must pass when you are done.

Use your superpowers planning skill workflow to drive this implementation.
