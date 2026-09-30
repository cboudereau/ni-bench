"""Scenario registry and arm-shipping rule (FR2).

An arm container receives the scenario prompt and the fixture project, nothing
else: criteria, briefs, postchecks, hidden tests, and origin notes stay on the
harness side (scenario-matrix and simulated-user ADRs).
"""

from pathlib import Path

from harness.models import Scenario

REPO_ROOT = Path(__file__).resolve().parent.parent


def _scenario(sid: str, family: str) -> Scenario:
    return Scenario(
        id=sid,
        family=family,
        prompt_path=f"scenarios/{sid}/prompt.md",
        criteria_path=f"scenarios/{sid}/criteria.md",
        post_checks=(f"scenarios/{sid}/postcheck.sh",),
    )


SCENARIOS: tuple[Scenario, ...] = (
    _scenario("plan-easy", "plan"),
    _scenario("plan-complex", "plan"),
    _scenario("debug-easy", "debug"),
    _scenario("debug-complex", "debug"),
    _scenario("build-small", "build"),
    _scenario("ported-debug", "debug"),
    _scenario("ported-build", "build"),
)

# plan-complex is a greenfield planning exercise: the arm starts in an empty workspace
FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    s.id for s in SCENARIOS if s.id != "plan-complex"
)

# postchecks for these run hidden tests kept out of the arm workspace
HIDDEN_TEST_SCENARIOS: tuple[str, ...] = ("debug-complex", "build-small", "ported-build")

PORTED_SCENARIOS: tuple[str, ...] = ("ported-debug", "ported-build")


def scenario_dir(scenario_id: str) -> Path:
    return REPO_ROOT / "scenarios" / scenario_id


def fixture_dir(scenario_id: str) -> Path | None:
    if scenario_id not in FIXTURE_SCENARIOS:
        return None
    return REPO_ROOT / "fixtures" / scenario_id


def scenario_arm_files(scenario_id: str) -> list[Path]:
    """Files shipped into the arm container: the prompt and the fixture, nothing else."""
    shipped = [scenario_dir(scenario_id) / "prompt.md"]
    fixture = fixture_dir(scenario_id)
    if fixture is not None:
        shipped.extend(
            p
            for p in sorted(fixture.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        )
    return shipped
