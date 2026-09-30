"""Domain types: Arm, TrialResult, Verdict (schema only at task 1)."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class Arm:
    """A subject compose service: image, plan-artifact glob, verbosity setting."""

    name: str
    dockerfile: str
    artifact_glob: str
    verbosity: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TrialResult:
    """One trial's captured output: CLI JSON, artifact metrics, verdict."""

    cli_json: dict[str, Any]
    artifact_metrics: dict[str, Any]
    verdict: Verdict

    def to_dict(self) -> dict[str, Any]:
        return {
            "cli_json": self.cli_json,
            "artifact_metrics": self.artifact_metrics,
            "verdict": self.verdict.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrialResult":
        return cls(
            cli_json=data["cli_json"],
            artifact_metrics=data["artifact_metrics"],
            verdict=Verdict(data["verdict"]),
        )
