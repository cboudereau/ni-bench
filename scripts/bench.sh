#!/usr/bin/env bash
# One-command benchmark run: trials + judging + report into a dedicated
# timestamped folder under .reports/. All outputs are local (git-excluded).
#
#   ./scripts/bench.sh            # full matrix, n=3
#   BENCH_N=1 ./scripts/bench.sh  # cheaper run
#   ./scripts/bench.sh smoke      # plan-easy only, n=1
#   BENCH_SCENARIOS=build-small,ported-build ./scripts/bench.sh   # partial matrix
#   ANTHROPIC_MODEL=claude-haiku-5-5 ./scripts/bench.sh          # subject model for this run only
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

# The ni arm is rebuilt on every run: a local checkout is re-staged (cached
# when unchanged), a marketplace run reinstalls the latest release. Without
# the rebuild the image keeps whatever the previous run built, so a marketplace
# run after a local one would silently benchmark the local checkout.
# shellcheck source=scripts/ni-source.sh
. ./scripts/ni-source.sh
docker compose build ni

# Plugin versions are whatever the built images actually hold (images install
# the latest marketplace release at build time), so read them live and record
# them in matrix.json; the renderer stays a pure function of the results dir
# (NFR3) and never trusts a hardcoded pin.
export BENCH_PLUGIN_OVERRIDES="$(./scripts/plugin-versions.sh)"
echo "plugin versions: $BENCH_PLUGIN_OVERRIDES"

# Models: the subject model is mandatory in .env so a run never depends on
# the arm CLI's own default (REPORT.md records the one actually billed);
# judge and simulator are pinned in the harness. A value in the shell
# environment wins for this run (docker-compose.yml passes it through to the
# arm containers; unset, the .env line stands).
SUBJECT_MODEL="${ANTHROPIC_MODEL:-$( { grep -E '^ANTHROPIC_MODEL=' .env 2>/dev/null || true; } | tail -1 | cut -d= -f2-)}"
if [ -z "$SUBJECT_MODEL" ]; then
  echo "bench: ANTHROPIC_MODEL is not set in .env (see .env.example)" >&2
  exit 1
fi
JUDGE_SIM="$(uv run python -c 'from harness.judge import JUDGE_MODEL; from harness.simulator import SIMULATOR_MODEL; print(f"judge={JUDGE_MODEL} simulator={SIMULATOR_MODEL}")')"
echo "models: subject=$SUBJECT_MODEL $JUDGE_SIM"

MODE="${1:-matrix}"
N="${BENCH_N:-3}"
[ "$MODE" = "smoke" ] && N="${BENCH_N:-1}"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR=".reports/run-$STAMP"
mkdir -p "$RUN_DIR"
SCENARIO_ARGS=()
if [ -n "${BENCH_SCENARIOS:-}" ]; then
  SCENARIO_ARGS=(--scenarios "$BENCH_SCENARIOS")
  echo "scenarios: $BENCH_SCENARIOS (partial matrix)"
fi
echo "run folder: $RUN_DIR (mode=$MODE, n=$N)"

uv run python -m harness.run "$MODE" --n "$N" --results-root "$RUN_DIR" "${SCENARIO_ARGS[@]}"
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
