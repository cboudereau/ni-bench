"""Trial runner: resume loop with the simulated user (FR4, FR7, FR8, NFR2).

One trial = fresh trial dir (fixture copy per shipping rule, throwaway HOME),
``claude -p`` in the arm container via ``docker compose run``, then a resume
loop driven by the simulated user until completion, the 6-user-turn cap, or
the 20 min wall-clock budget. The runner captures everything and interprets
nothing beyond the deterministic postcheck exit code.

Resume mechanics: the container exits between turns, so Claude session state
must outlive it. The trial's ``home/`` dir is bind-mounted as the container
HOME on every subject turn; ``claude`` persists its session there and
``claude -p --resume <session-id>`` finds it on the next ``docker compose run``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from harness.cost_guard import CostGuard, threshold_for
from harness.executor import Executor, compose_run_command, default_executor
from harness.models import Arm, Scenario, TrialResult, Verdict
from harness.scenarios import REPO_ROOT, fixture_dir, scenario_arm_files
from harness.simulator import SimulatedUser, needs_user_reply

HOME_MOUNT = "/home/node"
WORKSPACE_MOUNT = "/workspace"
REPO_MOUNT = "/repo"
TRIAL_TIMEOUT_S = 20 * 60  # total wall clock per trial - from failure modes
MAX_USER_TURNS = 6  # then grade as-is - from failure modes
POSTCHECK_TIMEOUT_S = 10 * 60  # grading budget, outside the trial clock


class TrialError(Exception):
    """CLI failed twice (retry-once rule) -> indeterminate."""


class TrialTimeout(TrialError):
    """20 min wall-clock budget exhausted -> container killed, indeterminate."""


def subject_command(
    arm: Arm,
    prompt: str,
    *,
    home_dir: Path | str,
    workspace_dir: Path | str,
    resume: str | None = None,
) -> list[str]:
    """Pure builder for one subject turn in the arm container."""
    cmd = compose_run_command(
        arm.name,
        volumes=((home_dir, HOME_MOUNT), (workspace_dir, WORKSPACE_MOUNT)),
        workdir=WORKSPACE_MOUNT,
    )
    cmd += [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--dangerously-skip-permissions",
    ]
    if resume is not None:
        cmd += ["--resume", resume]
    return cmd


def postcheck_command(scenario_id: str, workspace_dir: Path | str) -> list[str]:
    """Postcheck in the harness container: repo material read-only, workspace rw."""
    cmd = compose_run_command(
        "harness",
        volumes=(
            (REPO_ROOT / "scenarios", f"{REPO_MOUNT}/scenarios", True),
            (REPO_ROOT / "fixtures", f"{REPO_MOUNT}/fixtures", True),
            (workspace_dir, WORKSPACE_MOUNT),
        ),
    )
    cmd += ["bash", f"{REPO_MOUNT}/scenarios/{scenario_id}/postcheck.sh", WORKSPACE_MOUNT]
    return cmd


def artifact_metrics(workspace: Path, artifact_glob: str) -> dict:
    """Plan word count and file list per the arm's artifact glob (kpi-scoring ADR)."""
    files = [p for p in sorted(workspace.glob(artifact_glob)) if p.is_file()]
    words = sum(
        len(p.read_text(encoding="utf-8", errors="replace").split()) for p in files
    )
    return {
        "plan_words": words,
        "plan_files": [p.relative_to(workspace).as_posix() for p in files],
    }


def _git(workspace: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }
    proc = subprocess.run(
        [
            "git",
            "-c", "user.email=harness@ni-bench",
            "-c", "user.name=ni-bench",
            "-c", "commit.gpgsign=false",
            *args,
        ],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _prepare_workspace(scenario_id: str, workspace: Path) -> None:
    """Fixture copy per the shipping rule: prompt + fixture files, nothing else."""
    fixture = fixture_dir(scenario_id)
    if fixture is None:
        return
    for path in scenario_arm_files(scenario_id):
        if not path.is_relative_to(fixture):
            continue  # the prompt travels via -p, not the workspace
        dest = workspace / path.relative_to(fixture)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def _invoke_json(
    executor: Executor,
    cmd: Sequence[str],
    *,
    deadline: float,
    clock: Callable[[], float],
    save_stem: Path,
) -> dict:
    """Run one CLI invocation: retry once on error, then TrialError; timeout kills."""
    last_error = ""
    for attempt in (1, 2):
        remaining = deadline - clock()
        if remaining <= 0:
            raise TrialTimeout("trial wall-clock budget exhausted")
        try:
            result = executor(cmd, remaining)
        except subprocess.TimeoutExpired as exc:
            raise TrialTimeout(f"killed after {TRIAL_TIMEOUT_S}s wall clock") from exc
        if result.returncode == 0:
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError:
                last_error = "unparseable CLI JSON"
                parsed = None
            if parsed is not None and not parsed.get("is_error"):
                save_stem.with_suffix(".json").write_text(
                    result.stdout, encoding="utf-8"
                )
                return parsed
            last_error = last_error or f"CLI reported is_error: {result.stdout[:500]}"
        else:
            last_error = f"exit {result.returncode}: {result.stderr[-500:]}"
        save_stem.with_name(f"{save_stem.name}.attempt-{attempt}.err.txt").write_text(
            f"{last_error}\n--- stdout ---\n{result.stdout}", encoding="utf-8"
        )
    raise TrialError(f"CLI failed twice (retry-once rule): {last_error}")


def _usage_sum(turns: list[dict]) -> dict:
    return {
        "input_tokens": sum(t.get("usage", {}).get("input_tokens", 0) for t in turns),
        "output_tokens": sum(t.get("usage", {}).get("output_tokens", 0) for t in turns),
    }


def run_trial(
    arm: Arm,
    scenario: Scenario,
    trial_id: str,
    *,
    results_root: Path,
    executor: Executor = default_executor,
    clock: Callable[[], float] = time.monotonic,
    timeout_s: float = TRIAL_TIMEOUT_S,
    max_user_turns: int = MAX_USER_TURNS,
) -> TrialResult:
    trial_dir = results_root / scenario.id / arm.name / trial_id
    workspace = trial_dir / "workspace"
    home = trial_dir / "home"  # persists session state across compose runs
    sim_home = trial_dir / "sim-home"
    turns_dir = trial_dir / "turns"
    sim_dir = trial_dir / "simulator"
    for d in (workspace, home, sim_home, turns_dir, sim_dir):
        d.mkdir(parents=True, exist_ok=True)

    _prepare_workspace(scenario.id, workspace)
    _git(workspace, "init", "-q")
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "--allow-empty", "-m", "fixture baseline")

    prompt = (REPO_ROOT / scenario.prompt_path).read_text(encoding="utf-8")
    simulated_user = SimulatedUser.for_scenario(scenario.id, home_dir=sim_home)

    deadline = clock() + timeout_s
    subject_turns: list[dict] = []
    simulator_calls: list[dict] = []
    transcript: list[dict] = []
    user_turns = 0
    session_id: str | None = None
    error: str | None = None

    try:
        parsed = _invoke_json(
            executor,
            subject_command(arm, prompt, home_dir=home, workspace_dir=workspace),
            deadline=deadline,
            clock=clock,
            save_stem=turns_dir / "turn-01",
        )
        subject_turns.append(parsed)
        session_id = parsed.get("session_id")
        final_message = parsed.get("result") or ""
        while needs_user_reply(final_message) and user_turns < max_user_turns:
            sim_parsed = _invoke_json(
                executor,
                simulated_user.command(final_message),
                deadline=deadline,
                clock=clock,
                save_stem=sim_dir / f"turn-{user_turns + 1:02d}",
            )
            simulator_calls.append(sim_parsed)
            user_turns += 1
            reply = sim_parsed.get("result") or ""
            transcript.append({"assistant": final_message, "user": reply})
            parsed = _invoke_json(
                executor,
                subject_command(
                    arm, reply, home_dir=home, workspace_dir=workspace,
                    resume=session_id,
                ),
                deadline=deadline,
                clock=clock,
                save_stem=turns_dir / f"turn-{len(subject_turns) + 1:02d}",
            )
            subject_turns.append(parsed)
            session_id = parsed.get("session_id") or session_id
            final_message = parsed.get("result") or ""
    except TrialTimeout as exc:
        error = f"timeout: {exc}"
    except TrialError as exc:
        error = str(exc)

    (sim_dir / "transcript.json").write_text(
        json.dumps(transcript, indent=2), encoding="utf-8"
    )
    _git(workspace, "add", "-A")
    (trial_dir / "fixture.diff").write_text(
        _git(workspace, "diff", "--cached"), encoding="utf-8"
    )
    changed = _git(workspace, "diff", "--cached", "--name-only").split()

    metrics = artifact_metrics(workspace, arm.artifact_glob)
    metrics["files_changed"] = len(changed)

    postcheck: dict | None = None
    if error is None:
        check = executor(
            postcheck_command(scenario.id, workspace), POSTCHECK_TIMEOUT_S
        )
        (trial_dir / "postcheck.txt").write_text(
            check.stdout + check.stderr, encoding="utf-8"
        )
        postcheck = {"ok": check.returncode == 0, "returncode": check.returncode}
        verdict = Verdict.PASS if postcheck["ok"] else Verdict.FAIL
    else:
        verdict = Verdict.INDETERMINATE

    subject_summary = {
        "total_cost_usd": sum(t.get("total_cost_usd", 0.0) for t in subject_turns),
        "duration_ms": sum(t.get("duration_ms", 0) for t in subject_turns),
        "num_turns": sum(t.get("num_turns", 0) for t in subject_turns),
        "usage": _usage_sum(subject_turns),
        "subject_invocations": len(subject_turns),
        "session_id": session_id,
    }
    simulator_summary = {
        "total_cost_usd": sum(t.get("total_cost_usd", 0.0) for t in simulator_calls),
        "usage": _usage_sum(simulator_calls),
        "calls": len(simulator_calls),
    }
    result = TrialResult(
        cli_json=subject_summary,
        artifact_metrics=metrics,
        verdict=verdict,
        arm=arm.name,
        scenario=scenario.id,
        trial_id=trial_id,
        user_turns=user_turns,
        simulator=simulator_summary,
        postcheck=postcheck,
        total_cost_usd=subject_summary["total_cost_usd"]
        + simulator_summary["total_cost_usd"],
        error=error,
    )
    (trial_dir / "result.json").write_text(
        json.dumps(result.to_dict(), indent=2), encoding="utf-8"
    )
    return result


@dataclass(frozen=True)
class MatrixResult:
    partial: bool
    trials: list[TrialResult]
    spent_usd: float


def run_matrix(
    arms: Sequence[Arm],
    scenarios: Sequence[Scenario],
    n: int,
    *,
    results_root: Path,
    executor: Executor = default_executor,
    threshold_usd: float | None = None,
    clock: Callable[[], float] = time.monotonic,
    timeout_s: float = TRIAL_TIMEOUT_S,
) -> MatrixResult:
    """All (scenario, arm, trial) cells; the cost guard stops it, marked partial."""
    guard = CostGuard(threshold_usd if threshold_usd is not None else threshold_for(n))
    trials: list[TrialResult] = []
    partial = False
    for scenario in scenarios:
        for arm in arms:
            for i in range(1, n + 1):
                trial = run_trial(
                    arm,
                    scenario,
                    f"ni-bench-trial-{i:02d}",
                    results_root=results_root,
                    executor=executor,
                    clock=clock,
                    timeout_s=timeout_s,
                )
                trials.append(trial)
                guard.record(trial.total_cost_usd)
                if guard.exceeded:
                    partial = True
                    break
            if partial:
                break
        if partial:
            break
    results_root.mkdir(parents=True, exist_ok=True)
    (results_root / "matrix.json").write_text(
        json.dumps(
            {
                "partial": partial,
                "spent_usd": guard.spent_usd,
                "threshold_usd": guard.threshold_usd,
                "trials": len(trials),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return MatrixResult(partial=partial, trials=trials, spent_usd=guard.spent_usd)
