"""Subprocess boundary: docker compose command building and execution.

Everything that touches docker goes through an ``Executor`` so the runner and
simulator stay unit-testable without docker or API (task 4 acceptance criteria).
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecResult:
    returncode: int
    stdout: str
    stderr: str = ""


# (command, timeout_s) -> ExecResult; raises subprocess.TimeoutExpired on kill
Executor = Callable[[Sequence[str], float], ExecResult]


def default_executor(cmd: Sequence[str], timeout_s: float) -> ExecResult:
    proc = subprocess.run(
        list(cmd), capture_output=True, text=True, timeout=timeout_s
    )
    return ExecResult(proc.returncode, proc.stdout, proc.stderr)


def compose_run_command(
    service: str,
    *,
    volumes: Sequence[tuple] = (),
    env: Sequence[tuple[str, str]] = (),
    workdir: str | None = None,
) -> list[str]:
    """Pure builder for ``docker compose run`` invocations.

    ``volumes``: (host_path, container_path[, read_only]) tuples.
    """
    cmd = ["docker", "compose", "run", "--rm", "--no-deps", "-T"]
    for volume in volumes:
        src, dst, *flags = volume
        spec = f"{src}:{dst}" + (":ro" if flags and flags[0] else "")
        cmd += ["-v", spec]
    for key, value in env:
        cmd += ["-e", f"{key}={value}"]
    if workdir is not None:
        cmd += ["-w", workdir]
    cmd.append(service)
    return cmd
