"""Task 2 isolation tests (NFR1): no host config leaks into arm containers."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from harness.isolation import find_forbidden_mounts

REPO_ROOT = str(Path(__file__).resolve().parents[2])
HOME = "/home/clem"


def _config(volumes_by_service: dict) -> dict:
    return {
        "services": {name: {"volumes": vols} for name, vols in volumes_by_service.items()}
    }


def _bind(source: str) -> dict:
    return {"type": "bind", "source": source, "target": "/mnt/x"}


def test_flags_bind_of_host_claude_dir():
    config = _config({"ni": [_bind(f"{HOME}/.claude")]})
    violations = find_forbidden_mounts(config, repo_root=REPO_ROOT, home=HOME)
    assert len(violations) == 1
    assert "ni" in violations[0] and ".claude" in violations[0]


def test_flags_bind_under_host_config_dir():
    config = _config({"baseline": [_bind(f"{HOME}/.config/claude")]})
    violations = find_forbidden_mounts(config, repo_root=REPO_ROOT, home=HOME)
    assert len(violations) == 1
    assert ".config" in violations[0]


def test_flags_bind_outside_repo_tree():
    config = _config({"openspec": [_bind("/opt/shared-cache")]})
    violations = find_forbidden_mounts(config, repo_root=REPO_ROOT, home=HOME)
    assert violations == ["openspec: bind mount outside repo tree: /opt/shared-cache"]


def test_allows_repo_tree_trial_dir_and_non_bind_volumes():
    config = _config(
        {
            "harness": [
                _bind(f"{REPO_ROOT}/.reports/trial-001"),
                _bind("/tmp/ni-bench-trial-abc123"),
                {"type": "tmpfs", "target": "/home/node"},
                {"type": "volume", "source": "named", "target": "/data"},
            ]
        }
    )
    assert find_forbidden_mounts(config, repo_root=REPO_ROOT, home=HOME) == []


def test_handles_services_without_volumes():
    assert find_forbidden_mounts({"services": {"ni": {}}}, repo_root=REPO_ROOT, home=HOME) == []


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_compose_has_no_host_config_mounts():
    """The committed compose file declares no bind mount of host config or paths
    outside the repo tree (isolation-docker-compose ADR, NFR1)."""
    proc = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    config = json.loads(proc.stdout)
    home = str(Path.home())
    assert find_forbidden_mounts(config, repo_root=REPO_ROOT, home=home) == []
