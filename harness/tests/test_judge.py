"""Task 5 judge tests: blinding transform, verdict combination, rubric judge.

All docker/API boundaries are mocked through the injected executor - no network,
no docker, no credentials.
"""

import json
import re
from pathlib import Path

import pytest

from harness.blind import ARM_WORKSPACE, REDACTED, blind
from harness.executor import ExecResult
from harness.judge import (
    JUDGE_HOME_MOUNT,
    JUDGE_MODEL,
    JUDGE_QUALITY_FLOOR,
    PROMPT_FILENAME,
    assemble_judge_input,
    combine_verdict,
    judge_command,
    judge_results,
    judge_trial,
)
from harness.models import JudgeScore, TrialResult, Verdict

# The exact NFR4 measure: zero word-bounded, case-insensitive matches.
NFR4_PATTERN = re.compile(
    r"\b(ni|openspec|opsx|superpowers|baseline|natural-intelligence"
    r"|fission|obra|itsaspacestation|terse)\b",
    re.IGNORECASE,
)

ADVERSARIAL_SAMPLES = [
    "the ni plugin wrote this plan",
    "Ni, NI and nI in mixed case",
    "path results/plan-easy/ni/trial-01/result.json",
    "openspec/changes/add-json-flag/proposal.md was created",
    "see OpenSpec docs (openspec!) and the opsx command",
    "SUPERPOWERS: engaged. superpowers-marketplace install",
    "the baseline arm changed nothing",
    "Natural-Intelligence style, brainstorm with obra",
    "fission plan from itsaspacestation",
    "```bash\ncat ~/.claude/ni/terse\n```",
    "terse-mode banner: terse, full",
    "docs/workspace/benchmark/TASKS.md holds the plan",
    "docs/plans/2026-09-30-feature.md written",
    "ni-bench harness, ni.terse=full",
]

SURVIVOR_TEXT = (
    "The initial opus showed terseness; a knight paid in nickel "
    "kept fissionable baselines and openspecial obradoiro plans, opsxy."
)


def test_blind_strips_all_arm_identifiers():
    for sample in ADVERSARIAL_SAMPLES:
        blinded = blind(sample)
        assert not NFR4_PATTERN.search(blinded), f"{sample!r} -> {blinded!r}"
    joined = blind("\n".join(ADVERSARIAL_SAMPLES))
    assert not NFR4_PATTERN.search(joined)


def test_blind_keeps_ordinary_words():
    # word-bounded: substrings of blocked words inside ordinary words survive
    assert blind(SURVIVOR_TEXT) == SURVIVOR_TEXT


def test_blind_rewrites_plugin_paths_to_neutral_workspace():
    assert (
        blind("openspec/changes/add-json/proposal.md")
        == f"{ARM_WORKSPACE}/add-json/proposal.md"
    )
    assert (
        blind("docs/workspace/benchmark/DESIGN.md")
        == f"{ARM_WORKSPACE}/benchmark/DESIGN.md"
    )
    assert blind("docs/plans/2026-plan.md") == f"{ARM_WORKSPACE}/2026-plan.md"


def test_blind_replacement_token_is_neutral():
    assert blind("ni") == REDACTED
    assert not NFR4_PATTERN.search(REDACTED)
    assert not NFR4_PATTERN.search(ARM_WORKSPACE)


def test_blind_is_pure_and_idempotent():
    once = blind(ADVERSARIAL_SAMPLES[0])
    assert blind(once) == once


def test_explicit_flow_prompt_variants_blind_clean():
    # explicit-flow-track ADR: each per-arm prompt variant names its own
    # plugin workflow; the blinding transform must strip every identifier
    # before the text can reach the judge (via transcript echoes).
    from harness.scenarios import arm_prompt_path

    for sid in ("plan-easy", "plan-complex"):
        for arm in ("ni", "openspec", "superpowers"):
            text = arm_prompt_path(sid, arm).read_text(encoding="utf-8")
            assert NFR4_PATTERN.search(text), f"{sid}/{arm}: variant names no plugin?"
            assert not NFR4_PATTERN.search(blind(text)), f"{sid}/{arm} leaks after blinding"
            # a transcript quoting the variant line is also clean end to end
            quoted = assemble_judge_input(
                "prompt", "criteria", f"ASSISTANT:\nFollowing the instruction: {text}", {}
            )
            assert not NFR4_PATTERN.search(quoted), f"{sid}/{arm} leaks via judge input"


# --- verdict combination -------------------------------------------------


def test_postcheck_fail_overrides_judge_pass():
    assert combine_verdict(False, True, None) is Verdict.FAIL


@pytest.mark.parametrize(
    ("postcheck_ok", "judge_ok", "error", "expected"),
    [
        # no error: postcheck governs outcome, judge refines it
        (True, True, None, Verdict.PASS),
        (True, False, None, Verdict.FAIL),
        (True, None, None, Verdict.INDETERMINATE),
        (False, True, None, Verdict.FAIL),
        (False, False, None, Verdict.FAIL),
        (False, None, None, Verdict.FAIL),
        (None, True, None, Verdict.INDETERMINATE),
        (None, False, None, Verdict.INDETERMINATE),
        (None, None, None, Verdict.INDETERMINATE),
        # trial error: indeterminate regardless of anything else
        (True, True, "timeout: budget exhausted", Verdict.INDETERMINATE),
        (True, False, "CLI failed twice", Verdict.INDETERMINATE),
        (False, True, "CLI failed twice", Verdict.INDETERMINATE),
        (False, None, "timeout", Verdict.INDETERMINATE),
        (None, None, "timeout", Verdict.INDETERMINATE),
    ],
)
def test_verdict_combination_table(postcheck_ok, judge_ok, error, expected):
    assert combine_verdict(postcheck_ok, judge_ok, error) is expected


# --- judge trial (mocked executor) ----------------------------------------


def judge_cli(result_text: str, cost: float = 0.02) -> str:
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": result_text,
            "session_id": "judge-sess",
            "total_cost_usd": cost,
            "usage": {"input_tokens": 900, "output_tokens": 40},
        }
    )


GOOD_SCORE = '{"plan_quality": 82, "verbosity_score": 64, "outcome_notes": "solid plan"}'


class ScriptedExecutor:
    """Captures each call's argv and the prompt-file content at call time
    (the prompt travels via file + stdin since the Errno 7 fix)."""

    def __init__(self, outputs, prompt_file: Path | None = None):
        self.outputs = list(outputs)
        self.calls = []
        self.prompts = []
        self.prompt_file = prompt_file

    def __call__(self, cmd, timeout_s):
        self.calls.append(list(cmd))
        if self.prompt_file is None:
            # locate the mounted home from the -v host:container pair
            vol = next(
                (c.split(":")[0] for c in cmd if c.endswith(JUDGE_HOME_MOUNT)), None
            )
            path = Path(vol) / PROMPT_FILENAME if vol else None
        else:
            path = self.prompt_file
        self.prompts.append(
            path.read_text(encoding="utf-8") if path and path.exists() else ""
        )
        return self.outputs.pop(0)

    def prompt(self, i):
        return self.prompts[i]


def make_trial_dir(tmp_path: Path, *, arm: str = "ni", postcheck_ok: bool = True) -> Path:
    trial = tmp_path / "plan-easy" / arm / "ni-bench-trial-01"
    (trial / "turns").mkdir(parents=True)
    (trial / "simulator").mkdir()
    workspace = trial / "workspace"
    workspace.mkdir()
    (workspace / "PLAN.md").write_text(
        "Plan by the ni arm; superpowers-grade docs/workspace layout.",
        encoding="utf-8",
    )
    (trial / "turns" / "turn-01.json").write_text(
        json.dumps({"result": "Is openspec/changes/x the right place for the plan?"}),
        encoding="utf-8",
    )
    (trial / "turns" / "turn-02.json").write_text(
        json.dumps({"result": "Plan written to PLAN.md with terse output."}),
        encoding="utf-8",
    )
    (trial / "simulator" / "transcript.json").write_text(
        json.dumps([{"assistant": "Is it?", "user": "your call, decide and continue"}]),
        encoding="utf-8",
    )
    result = TrialResult(
        cli_json={"total_cost_usd": 0.4},
        artifact_metrics={"plan_words": 9, "plan_files": ["PLAN.md"]},
        verdict=Verdict.PASS if postcheck_ok else Verdict.FAIL,
        arm=arm,
        scenario="plan-easy",
        trial_id="ni-bench-trial-01",
        user_turns=1,
        postcheck={"ok": postcheck_ok, "returncode": 0 if postcheck_ok else 1},
        total_cost_usd=0.5,
    )
    (trial / "result.json").write_text(
        json.dumps(result.to_dict(), indent=2), encoding="utf-8"
    )
    return trial


def read_result(trial: Path) -> dict:
    return json.loads((trial / "result.json").read_text(encoding="utf-8"))


def test_judge_returns_strict_json_scores_on_canned_blinded_sample(tmp_path):
    trial = make_trial_dir(tmp_path)
    ex = ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))])
    score = judge_trial(trial, executor=ex)

    assert score == JudgeScore(82, 64, "solid plan")
    assert len(ex.calls) == 1

    # judge input saved and NFR4-clean, even though trial files name the arm
    input_text = (trial / "judge" / "input.txt").read_text(encoding="utf-8")
    assert not NFR4_PATTERN.search(input_text)
    assert "acceptance criteria" in input_text.lower()
    # the prompt sent to the judge is exactly the saved blinded input
    assert ex.prompt(0) == input_text

    output = json.loads((trial / "judge" / "output.json").read_text(encoding="utf-8"))
    assert output["score"] == {
        "plan_quality": 82,
        "verbosity_score": 64,
        "outcome_notes": "solid plan",
    }
    assert output["indeterminate"] is False


def test_judge_scores_wired_into_result_json(tmp_path):
    trial = make_trial_dir(tmp_path)
    judge_trial(trial, executor=ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))]))

    data = read_result(trial)
    assert data["judge"]["plan_quality"] == 82
    assert data["judge"]["verbosity_score"] == 64
    assert data["judge"]["model"] == JUDGE_MODEL
    assert data["verdict"] == "pass"
    # judge cost joins the NFR2 total
    assert data["total_cost_usd"] == pytest.approx(0.5 + 0.02)
    # schema roundtrip still lossless with the judge block
    assert TrialResult.from_dict(data).to_dict() == data


def test_judge_parse_retry_then_indeterminate(tmp_path):
    trial = make_trial_dir(tmp_path)
    ex = ScriptedExecutor(
        [
            ExecResult(0, judge_cli("I think the plan deserves about 80/100.")),
            ExecResult(0, judge_cli("still not json, sorry")),
        ]
    )
    score = judge_trial(trial, executor=ex)

    assert score is None
    assert len(ex.calls) == 2
    # the retry carries a format reminder on top of the same blinded input
    assert "JSON" in ex.prompt(1)
    assert ex.prompt(1) != ex.prompt(0)
    assert ex.prompt(1).startswith(ex.prompt(0))

    output = json.loads((trial / "judge" / "output.json").read_text(encoding="utf-8"))
    assert output["indeterminate"] is True
    assert output["score"] is None
    data = read_result(trial)
    assert data["verdict"] == "indeterminate"
    assert data["judge"]["indeterminate"] is True


def test_judge_retry_recovers_after_bad_first_reply(tmp_path):
    trial = make_trial_dir(tmp_path)
    ex = ScriptedExecutor(
        [
            ExecResult(1, "", "boom"),
            ExecResult(0, judge_cli(GOOD_SCORE, cost=0.03)),
        ]
    )
    score = judge_trial(trial, executor=ex)
    assert score == JudgeScore(82, 64, "solid plan")
    assert read_result(trial)["verdict"] == "pass"


def test_postcheck_fail_keeps_fail_despite_high_judge_score(tmp_path):
    trial = make_trial_dir(tmp_path, postcheck_ok=False)
    score = judge_trial(
        trial, executor=ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))])
    )
    assert score == JudgeScore(82, 64, "solid plan")
    assert read_result(trial)["verdict"] == "fail"


def test_low_plan_quality_fails_when_postcheck_passes(tmp_path):
    trial = make_trial_dir(tmp_path)
    low = json.dumps(
        {
            "plan_quality": JUDGE_QUALITY_FLOOR - 1,
            "verbosity_score": 90,
            "outcome_notes": "thin",
        }
    )
    judge_trial(trial, executor=ScriptedExecutor([ExecResult(0, judge_cli(low))]))
    assert read_result(trial)["verdict"] == "fail"


def test_judge_command_runs_in_harness_service_with_fixed_model(tmp_path):
    cmd = judge_command(home_dir=tmp_path / "home")
    assert cmd[:6] == ["docker", "compose", "run", "--rm", "--no-deps", "-T"]
    assert "harness" in cmd
    shell = cmd[-1]
    assert f"--model {JUDGE_MODEL}" in shell
    assert JUDGE_MODEL == "claude-sonnet-5-5"
    # prompt travels via a file in the mounted HOME, never argv (Errno 7 fix)
    assert f"< {JUDGE_HOME_MOUNT}/{PROMPT_FILENAME}" in shell
    assert all(len(part) < 10_000 for part in cmd)


def test_judge_trial_writes_prompt_file_not_argv(tmp_path):
    trial = make_trial_dir(tmp_path)
    ex = ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))])
    judge_trial(trial, executor=ex)
    prompt_file = trial / "judge" / "home" / PROMPT_FILENAME
    assert prompt_file.exists()
    content = prompt_file.read_text(encoding="utf-8")
    assert content  # prompt persisted for the container to read
    # the full prompt never appears inline in argv (Errno 7 regression guard)
    assert all(content not in part for part in ex.calls[0])
    assert ex.prompts[0] == content


# --- judge_results discovery (task 7 wiring) -------------------------------


def test_judge_results_judges_every_unjudged_trial(tmp_path):
    trial_a = make_trial_dir(tmp_path)
    trial_b = make_trial_dir(tmp_path, arm="baseline")
    ex = ScriptedExecutor(
        [
            ExecResult(0, judge_cli(GOOD_SCORE)),
            ExecResult(0, judge_cli(GOOD_SCORE)),
        ]
    )
    judged = judge_results(tmp_path, executor=ex)
    assert sorted(judged) == sorted([trial_a, trial_b])
    assert read_result(trial_a)["judge"] is not None
    assert read_result(trial_b)["judge"] is not None


def test_judge_results_skips_already_judged_unless_forced(tmp_path):
    trial = make_trial_dir(tmp_path)
    judge_trial(trial, executor=ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))]))
    assert judge_results(tmp_path, executor=ScriptedExecutor([])) == []
    ex = ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))])
    assert judge_results(tmp_path, executor=ex, force=True) == [trial]


def test_judge_trial_mounts_absolute_home_from_relative_trial_dir(tmp_path, monkeypatch):
    # smoke-run infra bug (task 7): judge.sh passes a relative results dir and
    # docker -v rejects relative host paths ("invalid characters for a local
    # volume name"). The judge must resolve the trial dir before mounting.
    make_trial_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    ex = ScriptedExecutor([ExecResult(0, judge_cli(GOOD_SCORE))])
    judge_trial(Path("plan-easy/ni/ni-bench-trial-01"), executor=ex)
    cmd = ex.calls[0]
    volume = cmd[cmd.index("-v") + 1]
    assert volume.split(":")[0].startswith("/"), volume
