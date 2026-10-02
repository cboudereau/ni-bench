#!/usr/bin/env bash
# plan-easy postcheck: a non-empty plan document (markdown) exists in the workspace.
set -euo pipefail
ws="${1:?usage: postcheck.sh <workspace_dir>}"

found="$(find "$ws" -type f -name '*.md' -size +0c | head -n 1)"
if [ -z "$found" ]; then
  echo "postcheck: no plan artifact (*.md) found in workspace" >&2
  exit 1
fi
echo "postcheck: plan artifact found: $found"
