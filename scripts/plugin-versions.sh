#!/usr/bin/env bash
# Read the actually-installed plugin versions from the built arm images and
# print them as the BENCH_PLUGIN_OVERRIDES JSON. Images install the latest
# marketplace version at build time, so the report header must never trust a
# hardcoded constant (the renderer's PLUGIN_VERSIONS is a fallback for runs
# recorded before this script existed).
set -euo pipefail
cd "$(dirname "$0")/.."

plugin_version() { # arm
  # grep -m1 closes the pipe early; SIGPIPE under pipefail would fail the
  # whole pipeline, so capture the full listing first
  local listing
  listing="$(docker compose run --rm --no-deps -T "$1" claude plugin list 2>/dev/null || true)"
  printf '%s\n' "$listing" | grep -m1 'Version:' | sed 's/.*Version: *//' | tr -d ' \r' || true
}

NI_V="$(plugin_version ni)"
SP_V="$(plugin_version superpowers)"
OS_V="$(docker compose run --rm --no-deps -T openspec openspec --version 2>/dev/null | tr -d ' \r\n')"

[ -n "$NI_V" ] && [ -n "$SP_V" ] && [ -n "$OS_V" ] || {
  echo "plugin-versions: could not read a version (ni='$NI_V' superpowers='$SP_V' openspec='$OS_V')" >&2
  exit 1
}

printf '{"ni": "%s", "superpowers": "%s", "openspec": "%s"}\n' "$NI_V" "$SP_V" "$OS_V"
