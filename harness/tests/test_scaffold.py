"""Task 1 scaffold tests: TrialResult schema, subject arm registry."""

import json

from harness.arms import ARMS
from harness.models import TrialResult, Verdict


def test_result_schema_roundtrip():
    result = TrialResult(
        cli_json={
            "total_cost_usd": 1.23,
            "duration_ms": 4500,
            "num_turns": 3,
            "usage": {"input_tokens": 10, "output_tokens": 20},
        },
        artifact_metrics={"plan_words": 120, "files_created": 2},
        verdict=Verdict.INDETERMINATE,
    )
    payload = json.dumps(result.to_dict())
    assert TrialResult.from_dict(json.loads(payload)) == result


def test_arm_registry_lists_four_arms():
    # harness is a 5th compose service, not a subject arm
    assert [arm.name for arm in ARMS] == ["baseline", "openspec", "superpowers", "ni"]
