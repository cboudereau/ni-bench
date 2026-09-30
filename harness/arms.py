"""Subject arm registry (FR1, FR3).

The compose `harness` service (simulator + judge) is infrastructure, not a subject arm.
Artifact globs from the kpi-scoring ADR; verbosity settings from the verbosity-policy ADR.
"""

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
