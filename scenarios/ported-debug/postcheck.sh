#!/usr/bin/env bash
# ported-debug postcheck: repro green, suite green, and root-cause probes —
# messy SKUs consolidate under one key; unknown SKUs still fail loudly.
set -euo pipefail
ws="${1:?usage: postcheck.sh <workspace_dir>}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -R "$ws/." "$work/"
find "$work" -type d -name __pycache__ -exec rm -rf {} +

pybin="${POSTCHECK_PYTHON:-python3}"
cd "$work"
"$pybin" -m pytest -q -p no:cacheprovider
"$pybin" repro.py

"$pybin" - <<'PY'
import sys

from inventory import Inventory

# root-cause probe 1: messy write-path SKUs consolidate under one key
inv = Inventory()
inv.restock("wh-042 ", 4)
inv.restock("WH-042", 6)
if inv.available("wh-042") != 10:
    print("postcheck: restock does not consolidate SKU variants", file=sys.stderr)
    sys.exit(1)

# root-cause probe 2: a genuinely unknown SKU must still fail loudly
try:
    Inventory().reserve("WH-404", 1)
except Exception:
    pass
else:
    print("postcheck: unknown SKU reserve no longer fails (masking fix)", file=sys.stderr)
    sys.exit(1)
PY
echo "postcheck: repro, suite, and root-cause probes green"
