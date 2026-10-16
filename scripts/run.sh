#!/usr/bin/env bash
# Drive the trial matrix (task 4, FR7):
#   run.sh smoke   - plan-easy, all arms, n=1
#   run.sh matrix  - all scenarios, all arms, n=$BENCH_N (default 3)
# Exit 2 means the cost guard stopped the run: results are marked partial.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

mode="${1:?usage: run.sh smoke|matrix}"
status=0
case "$mode" in
  smoke) uv run python -m harness.run smoke || status=$? ;;
  matrix) uv run python -m harness.run matrix --n "${BENCH_N:-3}" || status=$? ;;
  *) echo "usage: run.sh smoke|matrix" >&2; exit 64 ;;
esac
if [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; then
  exit "$status" # real failure; 2 = cost-guard partial, still judge what ran
fi

# Judging is a post-trial step (task 7): blind-judge every new trial so both
# smoke and matrix produce judged result.json without a separate command.
./scripts/judge.sh
exit "$status"
