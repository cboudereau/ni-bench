"""Regenerates the canned results fixture (run from repo root; output is checked in)."""

import json
from pathlib import Path

root = Path(__file__).resolve().parent / "results"


def result(scenario, arm, trial_id, *, verdict, tin, tout, cost, dur, turns, user_turns,
           plan_words, plan_files, judge, error=None):
    return {
        "arm": arm,
        "scenario": scenario,
        "trial_id": trial_id,
        "cli_json": {
            "total_cost_usd": cost,
            "duration_ms": dur,
            "num_turns": turns,
            "usage": {"input_tokens": tin, "output_tokens": tout},
            "subject_invocations": 1,
            "session_id": "sess-canned",
        },
        "artifact_metrics": {
            "plan_words": plan_words,
            "plan_files": plan_files,
            "files_changed": 1,
        },
        "user_turns": user_turns,
        "simulator": {
            "total_cost_usd": 0.01,
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "calls": user_turns,
        },
        "postcheck": (
            {"ok": verdict == "pass", "returncode": 0 if verdict == "pass" else 1}
            if verdict != "indeterminate"
            else None
        ),
        "judge": judge,
        "total_cost_usd": cost + 0.05,
        "verdict": verdict,
        "error": error,
    }


def judge(pq, vs):
    return {"plan_quality": pq, "verbosity_score": vs, "outcome_notes": "canned",
            "model": "claude-sonnet-5-5", "cost_usd": 0.04, "indeterminate": False}


CELLS = [
    result("plan-easy", "baseline", "t01", verdict="fail", tin=15000, tout=5000, cost=0.50,
           dur=100000, turns=10, user_turns=2, plan_words=800, plan_files=["PLAN.md"],
           judge=judge(40, 50)),
    result("plan-easy", "openspec", "t01", verdict="pass", tin=30000, tout=10000, cost=1.00,
           dur=200000, turns=20, user_turns=0, plan_words=1600,
           plan_files=["openspec/changes/plan.md"], judge=judge(80, 60)),
    result("plan-easy", "superpowers", "t01", verdict="pass", tin=8000, tout=2000, cost=0.25,
           dur=50000, turns=5, user_turns=1, plan_words=400,
           plan_files=["docs/plans/plan.md"], judge=judge(90, 80)),
    result("plan-easy", "ni", "t01", verdict="pass", tin=7000, tout=3000, cost=0.40,
           dur=80000, turns=8, user_turns=1, plan_words=500,
           plan_files=["docs/workspace/plan/TASKS.md"], judge=judge(85, 90)),
    result("debug-easy", "baseline", "t01", verdict="pass", tin=16000, tout=4000, cost=0.30,
           dur=60000, turns=6, user_turns=0, plan_words=0, plan_files=[], judge=judge(60, 70)),
    result("debug-easy", "ni", "t01", verdict="pass", tin=8000, tout=2000, cost=0.20,
           dur=40000, turns=4, user_turns=0, plan_words=0, plan_files=[], judge=judge(70, 60)),
    result("debug-easy", "ni", "t02", verdict="fail", tin=25000, tout=5000, cost=0.60,
           dur=90000, turns=9, user_turns=1, plan_words=0, plan_files=[], judge=judge(80, 90)),
    result("debug-easy", "ni", "t03", verdict="indeterminate", tin=999999, tout=0, cost=0.10,
           dur=1200000, turns=1, user_turns=0, plan_words=0, plan_files=[], judge=None,
           error="timeout: trial wall-clock budget exhausted"),
]


def main() -> None:
    for r in CELLS:
        d = root / r["scenario"] / r["arm"] / r["trial_id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "result.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")

    turns = root / "plan-easy" / "baseline" / "t01" / "turns"
    turns.mkdir(parents=True, exist_ok=True)
    (turns / "turn-01.json").write_text(
        json.dumps(
            {
                "type": "result",
                "result": "done",
                "session_id": "sess-canned",
                "modelUsage": {"claude-opus-4-6": {"inputTokens": 15000, "outputTokens": 5000}},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (root / "matrix.json").write_text(
        json.dumps(
            {
                "partial": False,
                "spent_usd": 3.75,
                "threshold_usd": 150.0,
                "trials": 8,
                "n": 3,
                "date": "2026-09-29",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"canned results written under {root}")


if __name__ == "__main__":
    main()
