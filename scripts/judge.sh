#!/usr/bin/env bash
# FR5 judge wiring (task 7): blind-judge every saved trial under .reports/
# (or an alternate dir). --force re-judges already-judged trials — real spend.
# The judge itself runs in the plugin-free `harness` compose service.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

uv run python -m harness.judge "$@"
