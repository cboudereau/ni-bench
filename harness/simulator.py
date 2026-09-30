"""Simulated user (FR8, simulated-user ADR).

Runs ``claude -p`` in the plugin-free ``harness`` compose service with a fixed
cheap model and a per-scenario user brief. Replies come only from the brief;
the runner executes the command this module builds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harness.executor import compose_run_command
from harness.scenarios import scenario_dir

SIMULATOR_MODEL = "claude-haiku-4-5-20251001"
SIMULATOR_HOME_MOUNT = "/home/node"
FALLBACK_REPLY = "your call, decide and continue"

STANDING_RULES = f"""\
You are simulating the human user of a coding assistant in a benchmark.
Standing rules (simulated-user ADR):
- Answer only from the user brief below. Facts not in the brief do not exist.
- When the brief does not cover the question, reply exactly: "{FALLBACK_REPLY}"
- Approve a plan or proposal gate when the plan addresses the brief's goal.
- Never introduce new requirements beyond the brief.
- Reply with the user's next message only - no commentary, no meta-discussion."""

# Explicit approval requests and plan-mode gate phrasings; the trailing-question
# rule below covers open questions. Calibrated on the smoke run (task 7).
_APPROVAL = re.compile(
    r"\b(approve|approval|shall i proceed|may i proceed"
    r"|would you like me to (proceed|continue|implement)"
    r"|do you want me to (proceed|continue|implement)"
    r"|reply ['\"]?approve|waiting for your (approval|confirmation|go-ahead)"
    r"|exit plan mode|plan mode)\b",
    re.IGNORECASE,
)


def needs_user_reply(final_message: str) -> bool:
    """Heuristic: does the subject's final message await the user?

    True for an explicit approval request / plan-mode gate, or any LINE ending
    with a question mark in the last three paragraphs - line-level because the
    smoke run showed questions heading a paragraph of option bullets
    ("Which execution approach do you want?\\n- option A\\n- option B") followed
    by a recommendation. A question answered in the same breath (rhetorical,
    "Open question: X. The plan says no.") does not end a line with "?" and
    does not count. Single function on purpose - calibrated on the task 7
    smoke run and frozen.
    """
    text = (final_message or "").strip()
    if not text:
        return False
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    tail_paragraphs = paragraphs[-3:]
    if _APPROVAL.search("\n".join(tail_paragraphs)):
        return True
    return any(
        line.rstrip().endswith("?")
        for paragraph in tail_paragraphs
        for line in paragraph.splitlines()
    )


def build_simulator_prompt(brief: str, final_message: str) -> str:
    return (
        f"{STANDING_RULES}\n\n"
        f"## User brief\n{brief}\n\n"
        f"## The assistant's last message\n{final_message}\n\n"
        f"Your reply as the user:"
    )


def simulator_command(
    prompt: str, *, home_dir: Path | str, model: str = SIMULATOR_MODEL
) -> list[str]:
    """``claude -p`` in the harness service with its own throwaway HOME."""
    cmd = compose_run_command(
        "harness", volumes=((home_dir, SIMULATOR_HOME_MOUNT),)
    )
    cmd += [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--dangerously-skip-permissions",
        "--model",
        model,
    ]
    return cmd


@dataclass(frozen=True)
class SimulatedUser:
    """Brief-bounded simulated user; the runner executes the built command."""

    brief: str
    home_dir: Path
    model: str = SIMULATOR_MODEL

    @classmethod
    def for_scenario(cls, scenario_id: str, *, home_dir: Path) -> SimulatedUser:
        brief = (scenario_dir(scenario_id) / "brief.md").read_text(encoding="utf-8")
        return cls(brief=brief, home_dir=home_dir)

    def command(self, final_message: str) -> list[str]:
        prompt = build_simulator_prompt(self.brief, final_message)
        return simulator_command(prompt, home_dir=self.home_dir, model=self.model)
