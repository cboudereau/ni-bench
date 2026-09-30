"""Hidden planted-defect-style checks — never shipped to the arm workspace.

Each check pins a specification clause that rushed implementations typically
get wrong: id reuse after removal, counter loss across persistence, silent
error paths.
"""

import pytest

from tasklist import TaskList


def test_ids_never_reused_after_clear_done():
    tl = TaskList()
    first = tl.add("one")
    tl.add("two")
    tl.complete(first)
    tl.clear_done()
    assert tl.add("three") == 3


def test_complete_unknown_id_raises_keyerror():
    with pytest.raises(KeyError):
        TaskList().complete(99)


def test_complete_twice_is_noop():
    tl = TaskList()
    task_id = tl.add("one")
    tl.complete(task_id)
    tl.complete(task_id)
    assert [t["done"] for t in tl.items()] == [True]


def test_blank_title_rejected():
    with pytest.raises(ValueError):
        TaskList().add("   ")


def test_clear_done_returns_removed_count():
    tl = TaskList()
    a = tl.add("a")
    b = tl.add("b")
    tl.add("c")
    tl.complete(a)
    tl.complete(b)
    assert tl.clear_done() == 2
    assert [t["title"] for t in tl.items()] == ["c"]


def test_id_counter_survives_save_load(tmp_path):
    path = tmp_path / "tasks.json"
    tl = TaskList()
    first = tl.add("one")
    tl.add("two")
    tl.complete(first)
    tl.clear_done()
    tl.save(path)

    loaded = TaskList.load(path)
    assert [t["title"] for t in loaded.items()] == ["two"]
    assert loaded.add("three") == 3


def test_round_trip_preserves_order_and_done_state(tmp_path):
    path = tmp_path / "tasks.json"
    tl = TaskList()
    tl.add("one")
    second = tl.add("two")
    tl.complete(second)
    tl.save(path)

    loaded = TaskList.load(path)
    assert loaded.items() == [
        {"id": 1, "title": "one", "done": False},
        {"id": 2, "title": "two", "done": True},
    ]
