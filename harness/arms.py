"""Subject arm registry (FR1, FR3).

The compose `harness` service (simulator + judge) is infrastructure, not a subject arm.
Artifact globs from the kpi-scoring ADR; verbosity settings from the verbosity-policy ADR.
Artifact classification from the two-audience-quality ADR (stage 1), rules
measured from run-20261001-154633.
"""

from pathlib import PurePosixPath

from harness.models import Arm

ARMS: tuple[Arm, ...] = (
    Arm(
        name="baseline",
        dockerfile="arms/Dockerfile.baseline",
        artifact_glob="*.md",
        verbosity={},
    ),
    Arm(
        name="openspec",
        dockerfile="arms/Dockerfile.openspec",
        artifact_glob="openspec/changes/**/*.md",
        verbosity={"OPENSPEC_TELEMETRY": "0"},
    ),
    Arm(
        name="superpowers",
        # glob to be confirmed against its plan file convention (kpi-scoring ADR, task 3)
        dockerfile="arms/Dockerfile.superpowers",
        artifact_glob="docs/plans/**/*.md",
        verbosity={},
    ),
    Arm(
        name="ni",
        dockerfile="arms/Dockerfile.ni",
        artifact_glob="docs/workspace/**/*.md",
        verbosity={"terse": "full"},
    ),
)


def classify_artifact(arm_name: str, rel_path: str) -> str:
    """Class a produced markdown path: ``human``, ``machine``, or ``excluded``.

    - human: documents people read (design docs, ADRs, proposals, plans)
    - machine: checklists/gates the agent executes and resumes from
    - excluded: tooling scaffolding the plugin's init writes unprompted,
      never authored plan content (counting it corrupted openspec's
      plan_words in run-20261001-154633)
    """
    path = PurePosixPath(rel_path)
    if path.parts and path.parts[0] == ".claude":  # every arm: scaffolding
        return "excluded"
    if arm_name == "ni":
        # TASKS.md / PREFLIGHT*.md are the ni machine layer
        if path.name == "TASKS.md" or (
            path.name.startswith("PREFLIGHT") and path.suffix == ".md"
        ):
            return "machine"
        return "human"
    if arm_name == "openspec":
        if path.parts[:2] == ("openspec", "specs"):  # written by `openspec init`
            return "excluded"
        if path.parts[:2] == ("openspec", "changes") and path.name == "tasks.md":
            return "machine"
        return "human"
    # superpowers and baseline ship no machine layer: authored markdown is human
    return "human"
