"""Task 3 scenario tests: file completeness, shipping rule, fixture baselines."""

import shutil
import subprocess
import sys

import pytest

from harness.scenarios import (
    FIXTURE_SCENARIOS,
    HIDDEN_TEST_SCENARIOS,
    PORTED_SCENARIOS,
    REPO_ROOT,
    SCENARIOS,
    arm_prompt_path,
    fixture_dir,
    scenario_arm_files,
    scenario_dir,
)

SCENARIO_IDS = tuple(s.id for s in SCENARIOS)

PRIVATE_NAMES = {"criteria.md", "brief.md", "postcheck.sh", "ORIGIN.md"}


def test_registry_lists_seven_scenarios():
    assert SCENARIO_IDS == (
        "plan-easy",
        "plan-complex",
        "debug-easy",
        "debug-complex",
        "build-small",
        "ported-debug",
        "ported-build",
    )


def test_scenario_files_complete():
    for sid in SCENARIO_IDS:
        d = scenario_dir(sid)
        for name in ("prompt.md", "criteria.md", "brief.md", "postcheck.sh"):
            path = d / name
            assert path.is_file() and path.stat().st_size > 0, f"{sid}/{name} missing or empty"
        assert (d / "postcheck.sh").stat().st_mode & 0o111, f"{sid}/postcheck.sh not executable"
    for sid in HIDDEN_TEST_SCENARIOS:
        hidden = scenario_dir(sid) / "hidden"
        assert list(hidden.glob("test_*.py")), f"{sid}/hidden has no hidden tests"
    for sid in PORTED_SCENARIOS:
        origin = scenario_dir(sid) / "ORIGIN.md"
        assert origin.is_file() and "licence" in origin.read_text(encoding="utf-8").lower(), (
            f"{sid}/ORIGIN.md missing or lacks licence finding"
        )


def test_arm_files_exclude_private_material():
    """Shipping rule: an arm sees the prompt and the fixture, nothing else."""
    for sid in SCENARIO_IDS:
        shipped = scenario_arm_files(sid)
        assert scenario_dir(sid) / "prompt.md" in shipped, f"{sid}: prompt not shipped"
        for path in shipped:
            assert path.name not in PRIVATE_NAMES, f"{sid}: private file shipped: {path}"
            assert "hidden" not in path.parts, f"{sid}: hidden test shipped: {path}"
        fixture = fixture_dir(sid)
        if sid in FIXTURE_SCENARIOS:
            assert fixture is not None and any(p.is_relative_to(fixture) for p in shipped), (
                f"{sid}: fixture files not shipped"
            )
        else:
            assert fixture is None, f"{sid}: unexpected fixture"


def _run_pytest(workdir):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=workdir,
        capture_output=True,
        text=True,
    )


def _fixture_copy(sid, tmp_path):
    dest = tmp_path / sid
    shutil.copytree(fixture_dir(sid), dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


@pytest.mark.parametrize(
    "sid", ["plan-easy", "debug-complex", "build-small", "ported-debug", "ported-build"]
)
def test_fixture_baselines_green(sid, tmp_path):
    proc = _run_pytest(_fixture_copy(sid, tmp_path))
    assert proc.returncode == 0, f"{sid} baseline red:\n{proc.stdout}\n{proc.stderr}"


def test_debug_easy_baseline_red_on_planted_test_only(tmp_path):
    proc = _run_pytest(_fixture_copy("debug-easy", tmp_path))
    assert proc.returncode != 0, "debug-easy baseline unexpectedly green"
    assert "1 failed" in proc.stdout, f"more than the planted test failed:\n{proc.stdout}"
    assert "test_apply_discount" in proc.stdout


def test_debug_complex_wrong_fix_passes_visible_fails_hidden(tmp_path):
    """A symptom-masking fix must pass the visible suite and fail the hidden tests."""
    workdir = _fixture_copy("debug-complex", tmp_path)
    patch = scenario_dir("debug-complex") / "hidden" / "wrong_fix.patch"
    applied = subprocess.run(
        ["git", "apply", str(patch)], cwd=workdir, capture_output=True, text=True
    )
    assert applied.returncode == 0, f"wrong_fix.patch does not apply:\n{applied.stderr}"

    visible = _run_pytest(workdir)
    assert visible.returncode == 0, f"wrong fix should pass visible suite:\n{visible.stdout}"

    for hidden_test in (scenario_dir("debug-complex") / "hidden").glob("test_*.py"):
        shutil.copy(hidden_test, workdir)
    hidden = _run_pytest(workdir)
    assert hidden.returncode != 0, "hidden tests failed to catch the symptom-masking fix"


def test_plan_fixture_has_no_markdown():
    """plan-easy postcheck counts any produced .md as the plan artifact."""
    assert not list(fixture_dir("plan-easy").rglob("*.md"))


# --- explicit-flow prompt variants (explicit-flow-track ADR) ---------------

PLUGIN_ARMS = ("ni", "openspec", "superpowers")


def test_arm_prompt_falls_back_to_shared_prompt():
    # baseline is the control: no variant file, ever
    for sid in SCENARIO_IDS:
        assert arm_prompt_path(sid, "baseline") == scenario_dir(sid) / "prompt.md"
    # openspec has no debug flow: debug scenarios fall back for it
    for sid in ("debug-easy", "debug-complex", "ported-debug"):
        assert arm_prompt_path(sid, "openspec") == scenario_dir(sid) / "prompt.md"


def test_arm_prompt_prefers_variant_for_debug_and_build_families():
    # explicit-flow scope extension: ni and superpowers on debug scenarios,
    # ni, superpowers, and openspec on build scenarios
    for sid in ("debug-easy", "debug-complex", "ported-debug"):
        for arm in ("ni", "superpowers"):
            assert arm_prompt_path(sid, arm) == scenario_dir(sid) / f"prompt-{arm}.md"
    for sid in ("build-small", "ported-build"):
        for arm in ("ni", "superpowers", "openspec"):
            assert arm_prompt_path(sid, arm) == scenario_dir(sid) / f"prompt-{arm}.md"


def test_arm_prompt_prefers_arm_variant_for_plan_family():
    for sid in ("plan-easy", "plan-complex"):
        base = (scenario_dir(sid) / "prompt.md").read_text(encoding="utf-8")
        for arm in PLUGIN_ARMS:
            path = arm_prompt_path(sid, arm)
            assert path == scenario_dir(sid) / f"prompt-{arm}.md", f"{sid}/{arm}"
            variant = path.read_text(encoding="utf-8")
            # same instruction shape: the control prompt plus exactly one
            # appended workflow line naming only this arm's own tool
            assert variant.startswith(base.rstrip("\n")), f"{sid}/{arm} diverges from control"
            extra = variant[len(base.rstrip("\n")):].strip()
            assert len(extra.splitlines()) == 1, f"{sid}/{arm}: more than one extra line"
            assert "workflow" in extra, f"{sid}/{arm}: extra line does not name a workflow"


def test_repo_root_points_at_worktree():
    assert (REPO_ROOT / "harness").is_dir() and (REPO_ROOT / "scenarios").is_dir()
