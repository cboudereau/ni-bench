#!/usr/bin/env bash
# FR6/NFR3 report generation (task 6): pure render of results/**/result.json
# into REPORT.md at the repo root. Optional args: an alternate results dir and
# an alternate output file (explicit-flow track), e.g.
#   report.sh results/explicit-v1 results/explicit-v1/REPORT.md
set -euo pipefail
cd "$(dirname "$0")/.."

uv run python -m harness.report "${1:-results}" ${2:+"$2"}
