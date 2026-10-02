"""Two-audience artifact classification (two-audience-quality ADR, stage 1).

Every produced markdown path is classed human (documents people read),
machine (checklists/gates the agent executes from), or excluded (tooling
scaffolding written by the plugin's init, never authored plan content).
Rules measured from run-20261001-154633.
"""

import pytest

from harness.arms import ARMS, classify_artifact

ARM_NAMES = [a.name for a in ARMS]


# --- all arms: tooling scaffolding is excluded -----------------------------


@pytest.mark.parametrize("arm", ARM_NAMES)
@pytest.mark.parametrize(
    "path",
    [
        ".claude/commands/opsx/apply.md",
        ".claude/skills/openspec-propose/SKILL.md",
        ".claude/settings.json.md",
    ],
)
def test_dot_claude_excluded_for_every_arm(arm, path):
    assert classify_artifact(arm, path) == "excluded"


# --- ni: TASKS/PREFLIGHT are the machine layer ------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "docs/workspace/json-output/TASKS.md",
        "docs/workspace/orion-client/PREFLIGHT.md",
        "docs/workspace/orion-client/PREFLIGHT-session-2.md",
    ],
)
def test_ni_machine_layer(path):
    assert classify_artifact("ni", path) == "machine"


@pytest.mark.parametrize(
    "path",
    [
        "docs/workspace/json-output/DESIGN.md",
        "docs/workspace/orion-client/DESIGN-api.md",
        "docs/workspace/orion-client/adrs/retry-policy.md",
        "CLAUDE.md",  # authored at the workspace root
        "PLAN.md",
    ],
)
def test_ni_human_layer(path):
    assert classify_artifact("ni", path) == "human"


# --- openspec: changes/**/tasks.md machine, init specs excluded -------------


def test_openspec_tasks_are_machine():
    assert (
        classify_artifact("openspec", "openspec/changes/add-json-output/tasks.md")
        == "machine"
    )


@pytest.mark.parametrize(
    "path",
    [
        "openspec/changes/add-json-output/proposal.md",
        "openspec/changes/add-json-output/design.md",
        "openspec/changes/add-json-output/specs/json-output/spec.md",
        "PLAN.md",
    ],
)
def test_openspec_human_layer(path):
    assert classify_artifact("openspec", path) == "human"


def test_openspec_init_specs_excluded():
    # top-level openspec/specs/** is written by `openspec init`, not authored
    assert classify_artifact("openspec", "openspec/specs/project/spec.md") == "excluded"


# --- superpowers / baseline: authored markdown is all human ------------------


@pytest.mark.parametrize("arm", ["superpowers", "baseline"])
@pytest.mark.parametrize(
    "path",
    [
        "docs/superpowers/plans/2026-10-01-json-output.md",
        "docs/plans/2026-10-01-json-output.md",
        "PLAN_json_flag.md",
        "TASKS.md",  # no machine convention for these arms
    ],
)
def test_authored_markdown_is_human(arm, path):
    assert classify_artifact(arm, path) == "human"
