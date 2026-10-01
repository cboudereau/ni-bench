"""Task 4 runner tests: trial loop, retries, timeout, turn cap, cost guard.

All docker/API boundaries are mocked through the injected executor — no network,
no docker, no credentials (task 4 acceptance criteria).
"""

import json
import re
import subprocess

import pytest

from harness.arms import ARMS
from harness.executor import ExecResult
from harness.models import Verdict
from harness.runner import postcheck_command, run_matrix, run_trial, subject_command
from harness.scenarios import SCENARIOS

BASELINE = ARMS[0]
PLAN_EASY = SCENARIOS[0]

COMPLETION = "Plan written to PLAN.md. All requested sections are covered."
QUESTION = "Should the JSON output include per-file totals, or only the aggregate?"
SIM_REPLY = "your call, decide and continue"


def cli_json(text, *, session="sess-1", cost=0.05, tin=100, tout=50, dur=1000, turns=2):
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": text,
            "session_id": session,
            "total_cost_usd": cost,
            "duration_ms": dur,
            "num_turns": turns,
            "usage": {"input_tokens": tin, "output_tokens": tout},
        }
    )


def kind(cmd):
    if any("postcheck.sh" in str(c) for c in cmd):
        return "postcheck"
    if "--model" in cmd:
        return "simulator"
    return "subject"


class Scripted:
    """Executor double: routes each docker compose command to a scripted response."""

    def __init__(self, subject=(), simulator=(), postcheck_rc=0, default_subject=None,
                 on_subject=None):
        self.subject = list(subject)
        self.simulator = list(simulator)
        self.postcheck_rc = postcheck_rc
        self.default_subject = default_subject
        self.on_subject = on_subject
        self.calls = []

    def __call__(self, cmd, timeout_s):
        cmd = list(cmd)
        self.calls.append((cmd, timeout_s))
        k = kind(cmd)
        if k == "postcheck":
            return ExecResult(self.postcheck_rc, "postcheck output", "")
        if k == "simulator":
            item = self.simulator.pop(0)
        else:
            if self.on_subject is not None:
                self.on_subject(cmd)
            item = self.subject.pop(0) if self.subject else self.default_subject
        if isinstance(item, Exception):
            raise item
        if isinstance(item, str):
            return ExecResult(0, item, "")
        return item

    def count(self, k):
        return sum(1 for cmd, _ in self.calls if kind(cmd) == k)


def test_subject_command_is_docker_compose_run_with_json_output():
    cmd = subject_command(
        BASELINE, "do the task", home_dir="/tmp/h", workspace_dir="/tmp/w"
    )
    assert cmd[:4] == ["docker", "compose", "run", "--rm"]
    assert "baseline" in cmd
    assert cmd[cmd.index("-p") + 1] == "do the task"
    for flag in ("claude", "--output-format", "json", "--dangerously-skip-permissions"):
        assert flag in cmd
    assert "--resume" not in cmd
    resumed = subject_command(
        BASELINE, "next", home_dir="/tmp/h", workspace_dir="/tmp/w", resume="sess-1"
    )
    assert resumed[resumed.index("--resume") + 1] == "sess-1"


def test_postcheck_command_runs_in_harness_service():
    cmd = postcheck_command("plan-easy", "/tmp/w")
    assert "harness" in cmd
    assert any("postcheck.sh" in c for c in cmd)


def test_trial_dir_layout(tmp_path):
    trial_dir = tmp_path / "plan-easy" / "baseline" / "t1"

    def write_plan(_cmd):
        (trial_dir / "workspace" / "PLAN.md").write_text("a plan with five words\n")

    ex = Scripted(subject=[cli_json(COMPLETION)], on_subject=write_plan)
    result = run_trial(BASELINE, PLAN_EASY, "t1", results_root=tmp_path, executor=ex)

    workspace = trial_dir / "workspace"
    assert (workspace / "cli.py").is_file(), "fixture not copied"
    for private in ("brief.md", "criteria.md", "postcheck.sh"):
        assert not list(workspace.rglob(private)), f"private file shipped: {private}"
    assert (trial_dir / "home").is_dir()
    turn1 = json.loads((trial_dir / "turns" / "turn-01.json").read_text())
    assert turn1["session_id"] == "sess-1"
    assert (trial_dir / "fixture.diff").is_file()
    assert "postcheck output" in (trial_dir / "postcheck.txt").read_text()

    saved = json.loads((trial_dir / "result.json").read_text())
    for key in (
        "cli_json", "artifact_metrics", "user_turns", "simulator",
        "postcheck", "verdict", "total_cost_usd",
    ):
        assert key in saved, f"result.json missing {key}"
    assert saved["cli_json"]["total_cost_usd"] == pytest.approx(0.05)
    assert saved["cli_json"]["duration_ms"] == 1000
    assert saved["cli_json"]["num_turns"] == 2
    assert saved["cli_json"]["usage"] == {"input_tokens": 100, "output_tokens": 50}
    assert saved["user_turns"] == 0
    assert saved["artifact_metrics"]["plan_words"] == 5
    assert "PLAN.md" in saved["artifact_metrics"]["plan_files"]
    assert saved["verdict"] == "pass"
    assert result.verdict is Verdict.PASS


def test_retry_then_indeterminate(tmp_path):
    ex = Scripted(subject=[ExecResult(1, "", "boom"), ExecResult(1, "", "boom")])
    result = run_trial(BASELINE, PLAN_EASY, "t1", results_root=tmp_path, executor=ex)
    assert ex.count("subject") == 2, "CLI failure must be retried exactly once"
    assert ex.count("postcheck") == 0, "no postcheck on an indeterminate trial"
    assert result.verdict is Verdict.INDETERMINATE
    saved = json.loads((tmp_path / "plan-easy" / "baseline" / "t1" / "result.json").read_text())
    assert saved["verdict"] == "indeterminate"
    assert saved["error"]


def test_timeout_kills_and_marks_indeterminate(tmp_path):
    ex = Scripted(subject=[subprocess.TimeoutExpired(cmd="claude", timeout=1200)])
    result = run_trial(BASELINE, PLAN_EASY, "t1", results_root=tmp_path, executor=ex)
    assert result.verdict is Verdict.INDETERMINATE
    assert "timeout" in (result.error or "")
    subject_calls = [(cmd, t) for cmd, t in ex.calls if kind(cmd) == "subject"]
    assert len(subject_calls) == 1, "a timeout consumes the whole budget: no retry"
    assert subject_calls[0][1] <= 20 * 60, "executor timeout must fit the 20 min budget"


def test_resume_loop_stops_at_turn_cap(tmp_path):
    ex = Scripted(
        subject=[cli_json(QUESTION)] * 7,
        simulator=[cli_json(SIM_REPLY, cost=0.01)] * 6,
    )
    result = run_trial(BASELINE, PLAN_EASY, "t1", results_root=tmp_path, executor=ex)
    assert ex.count("subject") == 7, "1 initial turn + 6 resumes"
    assert ex.count("simulator") == 6
    assert result.user_turns == 6
    resumes = [cmd for cmd, _ in ex.calls if kind(cmd) == "subject" and "--resume" in cmd]
    assert len(resumes) == 6
    for cmd in resumes:
        assert cmd[cmd.index("--resume") + 1] == "sess-1"
    assert result.verdict is Verdict.PASS, "turn cap grades as-is, not indeterminate"


def test_simulator_tokens_excluded_from_subject_kpis(tmp_path):
    ex = Scripted(
        subject=[
            cli_json(QUESTION, cost=0.05, tin=100, tout=50, dur=1000, turns=2),
            cli_json(COMPLETION, cost=0.07, tin=200, tout=80, dur=2000, turns=3),
        ],
        simulator=[cli_json(SIM_REPLY, cost=0.01, tin=7, tout=3)],
    )
    result = run_trial(BASELINE, PLAN_EASY, "t1", results_root=tmp_path, executor=ex)
    assert result.cli_json["total_cost_usd"] == pytest.approx(0.12)
    assert result.cli_json["usage"] == {"input_tokens": 300, "output_tokens": 130}
    assert result.cli_json["duration_ms"] == 3000
    assert result.cli_json["num_turns"] == 5
    assert result.user_turns == 1
    assert result.simulator["total_cost_usd"] == pytest.approx(0.01)
    assert result.simulator["usage"] == {"input_tokens": 7, "output_tokens": 3}
    assert result.simulator["calls"] == 1
    assert result.total_cost_usd == pytest.approx(0.13)


def test_cost_guard_stops_matrix(tmp_path):
    ex = Scripted(default_subject=cli_json(COMPLETION, cost=30.0))
    matrix = run_matrix(
        ARMS, [PLAN_EASY], 1, results_root=tmp_path, executor=ex, threshold_usd=50.0
    )
    assert matrix.partial is True
    assert len(matrix.trials) == 2, "guard trips once the sum crosses 50 USD"
    assert matrix.spent_usd == pytest.approx(60.0)
    marker = json.loads((tmp_path / "matrix.json").read_text())
    assert marker["partial"] is True


def test_matrix_completes_under_threshold(tmp_path):
    ex = Scripted(default_subject=cli_json(COMPLETION, cost=0.05))
    matrix = run_matrix(
        ARMS, [PLAN_EASY], 1, results_root=tmp_path, executor=ex, threshold_usd=50.0
    )
    assert matrix.partial is False
    assert len(matrix.trials) == len(ARMS)


def test_matrix_json_records_n_and_date(tmp_path):
    # the report header reads n and date from matrix.json, never the wall clock (NFR3)
    ex = Scripted(default_subject=cli_json(COMPLETION, cost=0.05))
    run_matrix(ARMS, [PLAN_EASY], 1, results_root=tmp_path, executor=ex, threshold_usd=50.0)
    marker = json.loads((tmp_path / "matrix.json").read_text())
    assert marker["n"] == 1
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", marker["date"])


def test_run_trial_sends_arm_prompt_variant(tmp_path):
    # explicit-flow-track ADR: an arm with a prompt variant gets it verbatim;
    # the baseline control keeps the shared prompt.
    from harness.scenarios import arm_prompt_path

    ni_arm = next(a for a in ARMS if a.artifact_glob == "docs/workspace/**/*.md")
    for arm in (ni_arm, BASELINE):
        ex = Scripted(subject=[cli_json(COMPLETION)])
        run_trial(arm, PLAN_EASY, "t1", results_root=tmp_path / arm.name, executor=ex)
        first = next(cmd for cmd, _ in ex.calls if kind(cmd) == "subject")
        sent = first[first.index("-p") + 1]
        expected = arm_prompt_path(PLAN_EASY.id, arm.name).read_text(encoding="utf-8")
        assert sent == expected, f"{arm.name} got the wrong prompt"
    assert arm_prompt_path(PLAN_EASY.id, ni_arm.name).name != "prompt.md"


def test_plan_artifacts_outside_arm_glob_still_captured(tmp_path):
    # smoke-run measurement gap (task 7): 3 of 4 arms wrote the plan at the
    # workspace root, outside their conventional glob, yielding plan_words=0
    # (which the min/value formula would score 100) and an artifact-less judge
    # input. Changed markdown files are captured whatever the glob says.
    from harness.arms import ARMS

    ni_arm = next(a for a in ARMS if a.artifact_glob == "docs/workspace/**/*.md")
    trial_dir = tmp_path / "plan-easy" / ni_arm.name / "t1"

    def write_plan(_cmd):
        (trial_dir / "workspace" / "PLAN.md").write_text("plan of five words here\n")

    ex = Scripted(subject=[cli_json(COMPLETION)], on_subject=write_plan)
    run_trial(ni_arm, PLAN_EASY, "t1", results_root=tmp_path, executor=ex)

    saved = json.loads((trial_dir / "result.json").read_text())
    assert saved["artifact_metrics"]["plan_files"] == ["PLAN.md"]
    assert saved["artifact_metrics"]["plan_words"] == 5


def test_existing_result_json_skips_trial(tmp_path):
    """Resume: a saved result.json returns as-is, no executor call."""
    from harness.arms import ARMS
    from harness.models import TrialResult, Verdict
    from harness.runner import run_trial
    from harness.scenarios import SCENARIOS

    arm = ARMS[0]
    scenario = next(s for s in SCENARIOS if s.id == "plan-easy")
    trial_dir = tmp_path / scenario.id / arm.name / "t1"
    trial_dir.mkdir(parents=True)
    canned = TrialResult(
        arm=arm.name,
        scenario=scenario.id,
        trial_id="t1",
        verdict=Verdict.PASS,
        cli_json={},
        artifact_metrics={},
    )
    import json as _json

    (trial_dir / "result.json").write_text(_json.dumps(canned.to_dict()))

    def exploding_executor(cmd, timeout_s):
        raise AssertionError("executor must not run on resume")

    got = run_trial(
        arm, scenario, "t1", results_root=tmp_path, executor=exploding_executor
    )
    assert got.verdict == "pass"
    assert got.trial_id == "t1"


def test_indeterminate_saved_result_retries_trial(tmp_path):
    """Resume retries indeterminate trials instead of replaying them."""
    import json as _json

    from harness.arms import ARMS
    from harness.executor import ExecResult
    from harness.models import TrialResult, Verdict
    from harness.runner import run_trial
    from harness.scenarios import SCENARIOS

    arm = ARMS[0]
    scenario = next(s for s in SCENARIOS if s.id == "plan-easy")
    trial_dir = tmp_path / scenario.id / arm.name / "t1"
    trial_dir.mkdir(parents=True)
    canned = TrialResult(
        arm=arm.name,
        scenario=scenario.id,
        trial_id="t1",
        verdict=Verdict.INDETERMINATE,
        cli_json={},
        artifact_metrics={},
        error="429",
    )
    (trial_dir / "result.json").write_text(_json.dumps(canned.to_dict()))
    calls = []

    def failing_executor(cmd, timeout_s):
        calls.append(cmd)
        return ExecResult(1, "", "boom")

    got = run_trial(
        arm, scenario, "t1", results_root=tmp_path, executor=failing_executor
    )
    assert calls, "indeterminate trial must re-run, not replay"
    assert got.verdict == Verdict.INDETERMINATE
