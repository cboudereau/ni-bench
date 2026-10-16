#!/usr/bin/env bash
# verbosity-policy ADR: ni arm runs terse level `full`.
# Plain-text state file read by the ni SessionStart hook (scripts/terse-mode.sh);
# written into the throwaway HOME before claude launches.
set -euo pipefail
mkdir -p "$HOME/.claude/ni"
printf 'full' > "$HOME/.claude/ni/terse"
