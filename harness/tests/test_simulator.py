"""Task 4 simulator tests: reply-needed heuristic, prompt building, command shape."""

from harness.simulator import (
    FALLBACK_REPLY,
    SIMULATOR_MODEL,
    SimulatedUser,
    build_simulator_prompt,
    needs_user_reply,
    simulator_command,
)


class TestNeedsUserReply:
    def test_open_question_needs_reply(self):
        assert needs_user_reply(
            "Should the JSON output include per-file totals, or only the aggregate?"
        )

    def test_approval_request_needs_reply(self):
        assert needs_user_reply(
            "The plan is drafted above.\n\nReply 'approve' to proceed with implementation."
        )

    def test_plan_mode_gate_needs_reply(self):
        assert needs_user_reply(
            "I have written the plan document.\n\n"
            "Do you approve this plan so I can proceed?"
        )

    def test_plain_completion_needs_no_reply(self):
        assert not needs_user_reply(
            "Plan written to PLAN.md. All requested sections are covered."
        )

    def test_rhetorical_question_needs_no_reply(self):
        assert not needs_user_reply(
            "Why did the test fail? Because the cache key ignored the locale. "
            "I fixed stats.py and all tests now pass."
        )

    def test_empty_message_needs_no_reply(self):
        assert not needs_user_reply("")

    def test_question_heading_option_bullets_needs_reply(self):
        # smoke-run false continue (task 7 calibration): the question line
        # heads a paragraph whose option bullets follow on single newlines,
        # then a recommendation paragraph - the subject still awaits a choice.
        assert needs_user_reply(
            "Plan written to docs/plans/plan.md.\n\n"
            "Which execution approach do you want?\n"
            "- **Subagent-driven:** a fresh subagent implements each task.\n"
            "- **Native:** I implement everything in this session.\n\n"
            "I recommend native. There are only two small tasks in one file."
        )

    def test_self_answered_open_question_needs_no_reply(self):
        # smoke-run true continue: the open question is answered in the same
        # breath ("The plan says no"), so the trial proceeds to grading.
        assert not needs_user_reply(
            "Plan written to PLAN.md.\n\n"
            "- **Tests:** nine cases are listed.\n"
            "- **Open question:** whether errors should also appear in the "
            "JSON. The plan says no, to keep current behaviour."
        )


def test_build_simulator_prompt_embeds_brief_rules_and_message():
    prompt = build_simulator_prompt("BRIEF-TEXT", "FINAL-MESSAGE")
    assert "BRIEF-TEXT" in prompt
    assert "FINAL-MESSAGE" in prompt
    assert FALLBACK_REPLY in prompt, "standing rules must carry the brief-silent reply"
    assert "never introduce new requirements" in prompt.lower()


def test_simulator_command_uses_harness_service_and_haiku(tmp_path):
    cmd = simulator_command("hello", home_dir=tmp_path / "sim-home")
    assert cmd[:4] == ["docker", "compose", "run", "--rm"]
    assert "harness" in cmd
    assert cmd[cmd.index("--model") + 1] == SIMULATOR_MODEL
    assert cmd[cmd.index("-p") + 1] == "hello"
    assert "--output-format" in cmd


def test_simulated_user_loads_scenario_brief(tmp_path):
    sim = SimulatedUser.for_scenario("plan-easy", home_dir=tmp_path / "sim-home")
    assert "wordstats" in sim.brief
    cmd = sim.command("Is streaming output required?")
    assert cmd[cmd.index("--model") + 1] == SIMULATOR_MODEL
    prompt = cmd[cmd.index("-p") + 1]
    assert "wordstats" in prompt and "Is streaming output required?" in prompt
