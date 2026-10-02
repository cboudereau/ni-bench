#!/usr/bin/env bash
# debug-easy postcheck: suite green in the post-run workspace, tests untouched.
set -euo pipefail
ws="${1:?usage: postcheck.sh <workspace_dir>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pristine="$here/../../fixtures/debug-easy"

if ! cmp -s "$pristine/test_pricing.py" "$ws/test_pricing.py"; then
  echo "postcheck: test_pricing.py was modified" >&2
  exit 1
fi

cd "$ws"
"${POSTCHECK_PYTHON:-python3}" -m pytest -q -p no:cacheprovider
echo "postcheck: suite green, tests untouched"
