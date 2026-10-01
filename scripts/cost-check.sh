#!/usr/bin/env bash
# NFR2 cost check (task 6): sums total_cost_usd over <run dir>/**/result.json
# (subject + simulator + judge already summed per trial) and compares against
# the 50 x n USD cap, n read from <run dir>/matrix.json. Prints the sum; exits 0
# under the cap, 1 over it.
set -euo pipefail
cd "$(dirname "$0")/.."

RESULTS_DIR="${1:-.reports}" uv run python - <<'PY'
import json
import os
import sys
from pathlib import Path

results = Path(os.environ["RESULTS_DIR"])
total = sum(
    json.loads(p.read_text(encoding="utf-8")).get("total_cost_usd", 0.0)
    for p in sorted(results.glob("*/*/*/result.json"))
)
matrix_path = results / "matrix.json"
n = 1
if matrix_path.is_file():
    n = json.loads(matrix_path.read_text(encoding="utf-8")).get("n", 1)
cap = 50.0 * n
print(f"total spend: {total:.2f} USD (cap {cap:.2f} USD, n={n})")
sys.exit(0 if total <= cap else 1)
PY
