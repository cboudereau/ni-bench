#!/usr/bin/env bash
# One-command benchmark run: trials + judging + report into a dedicated
# timestamped folder under .reports/. All outputs are local (git-excluded).
#
#   ./scripts/bench.sh            # full matrix, n=3
#   BENCH_N=1 ./scripts/bench.sh  # cheaper run
#   ./scripts/bench.sh smoke      # plan-easy only, n=1
#
# The run folder .reports/run-<timestamp>/ receives the trial dirs,
# matrix.json, REPORT.md, and an ANALYSIS.md stub. The analysis reading
# (FR9: bias table, baseline comparison, recommendations) is written by
# the operator or an agent from the run's REPORT.md and trial dirs.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

# bench.sh assumes nothing about image state: the base image is local-only
# (FROM ni-bench-base), so a pruned docker store would fail every trial.
docker image inspect ni-bench-base >/dev/null 2>&1 || ./scripts/build.sh

# Plugin versions are whatever the built images actually hold (images install
# the latest marketplace release at build time), so read them live and record
# them in matrix.json; the renderer stays a pure function of the results dir
# (NFR3) and never trusts a hardcoded pin.
export BENCH_PLUGIN_OVERRIDES="$(./scripts/plugin-versions.sh)"
echo "plugin versions: $BENCH_PLUGIN_OVERRIDES"

# NI_SOURCE=local (unpublished ni staged by scripts/stage-ni-local.sh): the
# honest build label wins over whatever version string the local build claims.
if [ "${NI_SOURCE:-marketplace}" = "local" ]; then
  LABEL="$(cat arms/ni-local/version-label.txt)"
  export BENCH_PLUGIN_OVERRIDES="$(printf '%s' "$BENCH_PLUGIN_OVERRIDES" | sed "s|\"ni\": \"[^\"]*\"|\"ni\": \"$LABEL\"|")"
  echo "ni arm: local build $LABEL"
fi

MODE="${1:-matrix}"
N="${BENCH_N:-3}"
[ "$MODE" = "smoke" ] && N="${BENCH_N:-1}"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR=".reports/run-$STAMP"
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
