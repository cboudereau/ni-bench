#!/usr/bin/env bash
# One-command benchmark run: trials + judging + report into a dedicated
# timestamped folder under results/. All outputs are local (git-excluded).
#
#   ./scripts/bench.sh            # full matrix, n=3
#   BENCH_N=1 ./scripts/bench.sh  # cheaper run
#   ./scripts/bench.sh smoke      # plan-easy only, n=1
#
# The run folder results/run-<timestamp>/ receives the trial dirs,
# matrix.json, REPORT.md, and an ANALYSIS.md stub. The analysis reading
# (FR9: bias table, baseline comparison, recommendations) is written by
# the operator or an agent from the run's REPORT.md and trial dirs.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

MODE="${1:-matrix}"
N="${BENCH_N:-3}"
[ "$MODE" = "smoke" ] && N="${BENCH_N:-1}"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="results/run-$STAMP"
mkdir -p "$RUN_DIR"
echo "run folder: $RUN_DIR (mode=$MODE, n=$N)"

uv run python -m harness.run "$MODE" --n "$N" --results-root "$RUN_DIR"
./scripts/judge.sh "$RUN_DIR"
uv run python -m harness.report "$RUN_DIR" "$RUN_DIR/REPORT.md"
./scripts/cost-check.sh "$RUN_DIR"

cat > "$RUN_DIR/ANALYSIS.md" <<'EOF'
# Analysis (FR9) — to be written from this run's REPORT.md and trial dirs

## Winners at a glance
(pending)

## Bias table
(pending — expected direction per scenario, followed or defied)

## True enhancement vs baseline
(pending)

## Recommendations
(pending)

## Disclosures
(pending — verbosity asymmetry, author affiliation, blinding residual risks)
EOF

echo "done: $RUN_DIR/REPORT.md rendered, ANALYSIS.md stub created"
