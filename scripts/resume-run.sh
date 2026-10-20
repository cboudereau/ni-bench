#!/usr/bin/env bash
# Resume an interrupted bench run: saved trials are no-ops (runner resume),
# remaining trials run live, then judging, report, and cost check.
#   ./scripts/resume-run.sh .reports/run-<timestamp> [n]
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

RUN="${1:?usage: resume-run.sh <run dir> [n]}"
N="${2:-3}"

uv run python -m harness.run matrix --n "$N" --results-root "$RUN"
./scripts/judge.sh "$RUN"
uv run python -m harness.report "$RUN" "$RUN/REPORT.md"
./scripts/cost-check.sh "$RUN"
echo BENCH-DONE
