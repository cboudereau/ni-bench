"""Blinding transform (NFR4, blind-llm-judge ADR).

Pure text transform applied to everything the judge reads: arm and plugin
identifiers are replaced by a neutral token, and plugin-specific artifact
roots (which reveal the arm by structure alone) are rewritten to a neutral
workspace prefix. Word-bounded and case-insensitive, matching the NFR4 grep
exactly, so ordinary words containing blocked substrings survive.
"""

from __future__ import annotations

import re

REDACTED = "[REDACTED]"
ARM_WORKSPACE = "ARM_WORKSPACE"

# NFR4 blocklist - longest alternatives first so the regex never leaves a
# blocked remainder behind.
BLOCKLIST: tuple[str, ...] = (
    "natural-intelligence",
    "itsaspacestation",
    "superpowers",
    "openspec",
    "baseline",
    "fission",
    "terse",
    "obra",
    "opsx",
    "ni",
)

# Plugin-specific artifact roots: ni -> docs/workspace, openspec ->
# openspec/changes, superpowers -> docs/plans (arm registry globs).
_PATH_RE = re.compile(
    r"\b(?:docs/workspace|openspec/changes|docs/plans)/", re.IGNORECASE
)
_WORD_RE = re.compile(r"\b(?:" + "|".join(BLOCKLIST) + r")\b", re.IGNORECASE)


def blind(text: str) -> str:
    """Judge input with zero arm-identifier matches (NFR4). Idempotent."""
    return _WORD_RE.sub(REDACTED, _PATH_RE.sub(f"{ARM_WORKSPACE}/", text))
