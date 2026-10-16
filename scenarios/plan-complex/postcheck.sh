#!/usr/bin/env bash
# plan-complex postcheck: a non-empty plan artifact exists and touches both
# hard decisions (persistence, versioning) at least lexically; depth is judged.
set -euo pipefail
ws="${1:?usage: postcheck.sh <workspace_dir>}"

plans="$(find "$ws" -type f -name '*.md' -size +0c)"
if [ -z "$plans" ]; then
  echo "postcheck: no plan artifact (*.md) found in workspace" >&2
  exit 1
fi

all_text="$(cat $plans)"
for term in persist version retry; do
  if ! grep -qi "$term" <<<"$all_text"; then
    echo "postcheck: plan never mentions '$term'" >&2
    exit 1
  fi
done
echo "postcheck: plan artifact present, decision keywords found"
