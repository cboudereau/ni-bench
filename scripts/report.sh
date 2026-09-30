#!/usr/bin/env bash
# FR6/NFR3 report generation (task 6): pure render of results/**/result.json
# into REPORT.md at the repo root. Optional arg: an alternate results dir.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run python -m harness.report "${1:-results}"
