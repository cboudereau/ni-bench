#!/usr/bin/env bash
# build-small postcheck: visible suite green AND hidden edge-case tests green.
set -euo pipefail
ws="${1:?usage: postcheck.sh <workspace_dir>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -R "$ws/." "$work/"
find "$work" -type d -name __pycache__ -exec rm -rf {} +

cd "$work"
"${POSTCHECK_PYTHON:-python3}" -m pytest -q -p no:cacheprovider

cp "$here"/hidden/test_*.py "$work/"
"${POSTCHECK_PYTHON:-python3}" -m pytest -q -p no:cacheprovider
echo "postcheck: visible and hidden suites green"
