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
class Scenario:
    """One benchmark scenario: public prompt, private criteria, deterministic post-checks."""

    id: str
    family: str  # plan | debug | build
    prompt_path: str
    criteria_path: str
    post_checks: tuple[str, ...]


@dataclass(frozen=True)
class JudgeScore:
    """Blinded judge scores on 0-100 scales (FR5, blind-llm-judge ADR)."""

    plan_quality: int
    verbosity_score: int
    outcome_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_quality": self.plan_quality,
            "verbosity_score": self.verbosity_score,
            "outcome_notes": self.outcome_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JudgeScore":
        return cls(
            plan_quality=data["plan_quality"],
            verbosity_score=data["verbosity_score"],
            outcome_notes=data.get("outcome_notes", ""),
        )


@dataclass(frozen=True)
class TrialResult:
    """One trial's captured output (FR4).

    ``cli_json`` holds the subject KPIs summed across all subject turns;
    ``simulator`` usage is recorded separately and never enters subject KPIs
    (simulated-user ADR). ``total_cost_usd`` sums subject + simulator (+ judge,
    task 5) for the NFR2 cost guard.
    """

    cli_json: dict[str, Any]
    artifact_metrics: dict[str, Any]
    verdict: Verdict
    arm: str = ""
    scenario: str = ""
    trial_id: str = ""
    user_turns: int = 0
    simulator: dict[str, Any] = field(default_factory=dict)
    postcheck: dict[str, Any] | None = None
    judge: dict[str, Any] | None = None  # JudgeScore fields + model, cost (task 5)
    total_cost_usd: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "scenario": self.scenario,
            "trial_id": self.trial_id,
            "cli_json": self.cli_json,
            "artifact_metrics": self.artifact_metrics,
            "user_turns": self.user_turns,
            "simulator": self.simulator,
            "postcheck": self.postcheck,
            "judge": self.judge,
            "total_cost_usd": self.total_cost_usd,
            "verdict": self.verdict.value,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrialResult":
        return cls(
            cli_json=data["cli_json"],
            artifact_metrics=data["artifact_metrics"],
            verdict=Verdict(data["verdict"]),
            arm=data.get("arm", ""),
            scenario=data.get("scenario", ""),
            trial_id=data.get("trial_id", ""),
            user_turns=data.get("user_turns", 0),
            simulator=data.get("simulator", {}),
            postcheck=data.get("postcheck"),
            judge=data.get("judge"),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            error=data.get("error"),
        )
