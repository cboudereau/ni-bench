#!/usr/bin/env bash
# Drive the trial matrix (task 4, FR7):
#   run.sh smoke   - plan-easy, all arms, n=1
#   run.sh matrix  - all scenarios, all arms, n=$BENCH_N (default 3)
# Exit 2 means the cost guard stopped the run: results are marked partial.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

mode="${1:?usage: run.sh smoke|matrix}"
case "$mode" in
  smoke) uv run python -m harness.run smoke ;;
  matrix) uv run python -m harness.run matrix --n "${BENCH_N:-3}" ;;
  *) echo "usage: run.sh smoke|matrix" >&2; exit 64 ;;
esac
