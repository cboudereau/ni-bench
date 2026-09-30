"""Compose isolation rules (NFR1, isolation-docker-compose ADR).

Arm containers must never see host Claude/OS config. Allowed bind sources:
inside the repo tree, or a per-trial throwaway dir matching TRIAL_DIR_GLOB.
"""

from __future__ import annotations

import fnmatch
from pathlib import PurePosixPath

FORBIDDEN_HOME_SUBDIRS = (".claude", ".config")
TRIAL_DIR_GLOB = "*/ni-bench-trial-*"


def _is_under(path: PurePosixPath, root: PurePosixPath) -> bool:
    return path == root or root in path.parents


def find_forbidden_mounts(config: dict, *, repo_root: str, home: str) -> list[str]:
    """Return one violation string per forbidden bind mount in a parsed
    ``docker compose config --format json`` document. Empty list == clean."""
    violations: list[str] = []
    home_path = PurePosixPath(home)
    repo_path = PurePosixPath(repo_root)
    for service, spec in (config.get("services") or {}).items():
        for volume in spec.get("volumes") or []:
            if not isinstance(volume, dict) or volume.get("type") != "bind":
                continue
            source = volume.get("source") or ""
            src_path = PurePosixPath(source)
            if any(
                _is_under(src_path, home_path / sub) for sub in FORBIDDEN_HOME_SUBDIRS
            ):
                violations.append(f"{service}: bind mount of host config: {source}")
            elif not _is_under(src_path, repo_path) and not fnmatch.fnmatch(
                source, TRIAL_DIR_GLOB
            ):
                violations.append(f"{service}: bind mount outside repo tree: {source}")
    return violations
