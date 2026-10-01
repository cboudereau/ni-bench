"""Blind LLM judge (FR5, NFR4, blind-llm-judge ADR).

Runs ``claude -p`` in the plugin-free ``harness`` compose service with a fixed
model and its own throwaway HOME - never the arm container, never the host CLI.
Input is the scenario prompt, the private criteria, and the blinded transcript
and artifacts; output is strict JSON scores, one retry with a format reminder
on parse failure, then indeterminate. Deterministic postchecks override the
judge on outcome: ``combine_verdict`` holds the whole table.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from harness.blind import blind
from harness.executor import Executor, compose_run_command, default_executor
from harness.models import JudgeScore, Verdict
from harness.scenarios import scenario_dir

JUDGE_MODEL = "claude-sonnet-5-5"
JUDGE_HOME_MOUNT = "/home/node"
JUDGE_TIMEOUT_S = 10 * 60  # grading budget, outside the trial clock
# A trial passes on quality only at or above this floor - mirrors the
# kpi-scoring ADR quality floor for plan_words.
JUDGE_QUALITY_FLOOR = 50

RUBRIC = """\
You are grading one anonymised coding-assistant trial for a benchmark.
Plugin, arm, and tool identifiers have been redacted; ignore redaction tokens
and neutral path prefixes and grade the content only.

Grade the trial against the private acceptance criteria below:
- plan_quality (0-100): completeness, testability, traceability, and task
  actionability against the criteria; for debugging tasks, whether the root
  cause is named before the fix.
- verbosity_score (0-100): signal density of the produced text - 100 means
  every sentence carries information the task needs, 0 means mostly padding.
- outcome_notes: one or two sentences on whether the trial achieved the task.

Reply with a single strict JSON object and nothing else - no prose, no code
fences:
{"plan_quality": <int 0-100>, "verbosity_score": <int 0-100>, "outcome_notes": "<string>"}"""

FORMAT_REMINDER = (
    "REMINDER: your previous reply was not valid JSON. Reply with exactly one "
    'strict JSON object {"plan_quality": <int 0-100>, "verbosity_score": '
    '<int 0-100>, "outcome_notes": "<string>"} and nothing else.'
)


def combine_verdict(
    postcheck_ok: bool | None, judge_ok: bool | None, error_state: str | None
) -> Verdict:
    """Three-valued verdict (FR5). Postcheck fail overrides judge on outcome.

    - trial error (retry exhausted, timeout) -> indeterminate, nothing gradable
    - deterministic postcheck fail -> fail, whatever the judge said
    - postcheck missing or judge indeterminate -> indeterminate
    - both fine -> judge quality decides pass/fail
    """
    if error_state:
        return Verdict.INDETERMINATE
    if postcheck_ok is False:
        return Verdict.FAIL
    if postcheck_ok is None or judge_ok is None:
        return Verdict.INDETERMINATE
    return Verdict.PASS if judge_ok else Verdict.FAIL


def assemble_judge_input(
    prompt: str, criteria: str, transcript: str, artifacts: dict[str, str]
) -> str:
    """Blinded judge input: rubric, scenario prompt, criteria, transcript, artifacts."""
    parts = [
        RUBRIC,
        "## Scenario prompt (what the user asked)",
        prompt,
        "## Private acceptance criteria (judge only)",
        criteria,
        "## Session transcript",
        transcript or "(no transcript captured)",
    ]
    for name, text in artifacts.items():
        parts += [f"## Artifact: {name}", text]
    return blind("\n\n".join(parts))


PROMPT_FILENAME = "judge-prompt.txt"


def judge_command(*, home_dir: Path | str, model: str = JUDGE_MODEL) -> list[str]:
    """``claude -p`` in the harness service with its own throwaway HOME.

    The prompt travels as a file inside the mounted HOME and is piped on
    stdin: a long transcript as a docker argv argument exceeds the kernel
    exec arg limit (OSError Errno 7 seen on the first full run).
    """
    cmd = compose_run_command("harness", volumes=((home_dir, JUDGE_HOME_MOUNT),))
    cmd += [
        "sh",
        "-c",
        f"claude -p --output-format json --dangerously-skip-permissions "
        f"--model {model} < {JUDGE_HOME_MOUNT}/{PROMPT_FILENAME}",
    ]
    return cmd


def parse_score(text: str) -> JudgeScore | None:
    """Strict JSON -> JudgeScore; None on any shape or range violation."""
    try:
        data = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    plan_quality = data.get("plan_quality")
    verbosity_score = data.get("verbosity_score")
    notes = data.get("outcome_notes", "")
    for value in (plan_quality, verbosity_score):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            return None
    if not isinstance(notes, str):
        return None
    return JudgeScore(plan_quality, verbosity_score, notes)


def _load_transcript(trial_dir: Path) -> str:
    """Interleave saved subject turns with the simulated user's replies."""
    replies: list[str] = []
    transcript_path = trial_dir / "simulator" / "transcript.json"
    if transcript_path.exists():
        entries = json.loads(transcript_path.read_text(encoding="utf-8"))
        replies = [entry.get("user", "") for entry in entries]
    lines: list[str] = []
    for i, turn in enumerate(sorted((trial_dir / "turns").glob("turn-*.json"))):
        message = json.loads(turn.read_text(encoding="utf-8")).get("result") or ""
        lines.append(f"ASSISTANT:\n{message}")
        if i < len(replies):
            lines.append(f"USER:\n{replies[i]}")
    return "\n\n".join(lines)


def _load_artifacts(trial_dir: Path, plan_files: list[str]) -> dict[str, str]:
    workspace = trial_dir / "workspace"
    artifacts: dict[str, str] = {}
    for rel in plan_files:
        path = workspace / rel
        if path.is_file():
            artifacts[rel] = path.read_text(encoding="utf-8", errors="replace")
    return artifacts


def find_trial_dirs(results_root: Path) -> list[Path]:
    """Trial dirs = scenario/arm/trial holding a result.json (runner layout)."""
    return sorted(p.parent for p in results_root.glob("*/*/*/result.json"))


def judge_results(
    results_root: Path | str,
    *,
    executor: Executor = default_executor,
    model: str = JUDGE_MODEL,
    force: bool = False,
) -> list[Path]:
    """Judge every saved trial under ``results_root`` (task 7 wiring).

    Already-judged trials (``judge`` block in result.json) are skipped unless
    ``force`` — re-judging respends real API budget, so it is opt-in only.
    """
    results_root = Path(results_root)
    judged: list[Path] = []
    for trial_dir in find_trial_dirs(results_root):
        data = json.loads((trial_dir / "result.json").read_text(encoding="utf-8"))
        if data.get("judge") is not None and not force:  # to_dict emits judge: null
            continue
        judge_trial(trial_dir, executor=executor, model=model)
        judged.append(trial_dir)
    return judged


def judge_trial(
    trial_dir: Path | str,
    *,
    executor: Executor = default_executor,
    model: str = JUDGE_MODEL,
    timeout_s: float = JUDGE_TIMEOUT_S,
) -> JudgeScore | None:
    """Judge one saved trial; writes judge/{input.txt,output.json}, updates result.json."""
    # resolve() because docker -v rejects relative host paths (smoke-run fix)
    trial_dir = Path(trial_dir).resolve()
    data = json.loads((trial_dir / "result.json").read_text(encoding="utf-8"))
    sdir = scenario_dir(data["scenario"])
    judge_input = assemble_judge_input(
        (sdir / "prompt.md").read_text(encoding="utf-8"),
        (sdir / "criteria.md").read_text(encoding="utf-8"),
        _load_transcript(trial_dir),
        _load_artifacts(trial_dir, data["artifact_metrics"].get("plan_files", [])),
    )

    judge_dir = trial_dir / "judge"
    home = judge_dir / "home"  # throwaway HOME for the harness service
    home.mkdir(parents=True, exist_ok=True)
    (judge_dir / "input.txt").write_text(judge_input, encoding="utf-8")

    score: JudgeScore | None = None
    cost_usd = 0.0
    attempts: list[dict] = []
    prompt = judge_input
    for _attempt in (1, 2):  # retry-once rule (blind-llm-judge ADR)
        (home / PROMPT_FILENAME).write_text(prompt, encoding="utf-8")
        try:
            result = executor(judge_command(home_dir=home, model=model), timeout_s)
        except subprocess.TimeoutExpired:
            attempts.append({"error": f"judge timeout after {timeout_s}s"})
            prompt = judge_input + "\n\n" + FORMAT_REMINDER
            continue
        attempt: dict = {"returncode": result.returncode, "stdout": result.stdout}
        if result.stderr:
            attempt["stderr"] = result.stderr
        try:
            cli = json.loads(result.stdout)
        except json.JSONDecodeError:
            cli = None
        if isinstance(cli, dict):
            cost_usd += cli.get("total_cost_usd", 0.0)
            if result.returncode == 0 and not cli.get("is_error"):
                score = parse_score(cli.get("result") or "")
        attempts.append(attempt)
        if score is not None:
            break
        prompt = judge_input + "\n\n" + FORMAT_REMINDER

    (judge_dir / "output.json").write_text(
        json.dumps(
            {
                "model": model,
                "score": score.to_dict() if score else None,
                "indeterminate": score is None,
                "cost_usd": cost_usd,
                "attempts": attempts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    postcheck = data.get("postcheck")
    postcheck_ok = postcheck.get("ok") if postcheck else None
    judge_ok = None if score is None else score.plan_quality >= JUDGE_QUALITY_FLOOR
    verdict = combine_verdict(postcheck_ok, judge_ok, data.get("error"))

    judge_block: dict = score.to_dict() if score else {}
    judge_block.update(
        {"model": model, "cost_usd": cost_usd, "indeterminate": score is None}
    )
    data["judge"] = judge_block
    data["verdict"] = verdict.value
    data["total_cost_usd"] = data.get("total_cost_usd", 0.0) + cost_usd
    (trial_dir / "result.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    return score


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m harness.judge [results_dir] [--force]`` (scripts/judge.sh)."""
    import argparse

    parser = argparse.ArgumentParser(prog="harness.judge")
    parser.add_argument("results", nargs="?", default=".reports")
    parser.add_argument("--force", action="store_true", help="re-judge judged trials")
    args = parser.parse_args(argv)
    judged = judge_results(Path(args.results), force=args.force)
    for trial_dir in judged:
        data = json.loads((trial_dir / "result.json").read_text(encoding="utf-8"))
        judge = data.get("judge", {})
        print(
            f"{trial_dir}: verdict={data.get('verdict')} "
            f"plan_quality={judge.get('plan_quality')} "
            f"verbosity={judge.get('verbosity_score')} "
            f"judge_cost={judge.get('cost_usd', 0.0):.4f}"
        )
    print(f"judged {len(judged)} trial(s)")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
