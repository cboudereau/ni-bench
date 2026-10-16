#!/usr/bin/env bash
# NFR1 isolation check (task 2, isolation-docker-compose + verbosity-policy ADRs).
# Runs without .env and without API calls.
#   1) compose config declares no forbidden bind mounts (host ~/.claude, ~/.config,
#      or anything outside the repo tree except trial dirs)
#   2) each of the 5 services contains exactly its own plugin (baseline, openspec,
#      harness: none)
#   3) openspec CLI present with telemetry off; ni terse level seeded to `full`
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

fail=0
say() { printf '%s\n' "$*"; }

say "== 1. compose config mount check =="
if docker compose config --format json | uv run python -c '
import json
import sys
from pathlib import Path

from harness.isolation import find_forbidden_mounts

config = json.load(sys.stdin)
violations = find_forbidden_mounts(
    config, repo_root=str(Path.cwd()), home=str(Path.home())
)
for violation in violations:
    print("FORBIDDEN:", violation)
sys.exit(1 if violations else 0)
'; then
  say "OK: no forbidden bind mounts"
else
  fail=1
fi
# belt and braces: raw grep for host config paths in the rendered config
if docker compose config | grep -E "$HOME/\.(claude|config)"; then
  say "FORBIDDEN: host config path appears in compose config"
  fail=1
fi

run_in() { docker compose run --rm --no-deps -T "$@" 2>/dev/null; }

check_plugins() { # service expected_plugin_line_or_empty
  local service="$1" expected="${2:-}" out count
  out="$(run_in "$service" claude plugin list)"
  count="$(printf '%s\n' "$out" | grep -c 'Version:' || true)"
  if [ -z "$expected" ]; then
    if [ "$count" -eq 0 ] && printf '%s' "$out" | grep -q 'No plugins installed'; then
      say "OK: $service has no plugin"
    else
      say "FAIL: $service should have no plugin, got: $out"
      fail=1
    fi
  else
    if [ "$count" -eq 1 ] && printf '%s' "$out" | grep -q "$expected"; then
      say "OK: $service has exactly $expected"
    else
      say "FAIL: $service should have exactly $expected, got: $out"
      fail=1
    fi
  fi
}

say "== 2. per-service plugin presence/absence =="
check_plugins baseline ""
check_plugins openspec ""
check_plugins harness ""
check_plugins superpowers "superpowers@superpowers-marketplace"
check_plugins ni "ni@itsaspacestation"

say "== 3. arm-specific configuration =="
if run_in openspec openspec --version | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+'; then
  say "OK: openspec CLI present"
else
  say "FAIL: openspec CLI missing or wrong version"
  fail=1
fi
if [ "$(run_in openspec printenv OPENSPEC_TELEMETRY)" = "0" ]; then
  say "OK: OPENSPEC_TELEMETRY=0"
else
  say "FAIL: OPENSPEC_TELEMETRY not 0"
  fail=1
fi
# postcheck runtime: pytest must exist in the shared base image - the harness
# service runs the test-based postchecks and the arms run the fixture suites
# (missing pytest silently failed every test-based postcheck in the first
# full matrix)
for svc in harness baseline; do
  if run_in "$svc" python3 -m pytest --version >/dev/null; then
    say "OK: $svc has pytest for fixture suites/postchecks"
  else
    say "FAIL: $svc lacks pytest (postchecks/fixture suites cannot run)"
    fail=1
  fi
done
# ni terse seed: entrypoint must write `full` before claude launches (verbosity-policy ADR)
if [ "$(run_in ni cat /home/node/.claude/ni/terse)" = "full" ]; then
  say "OK: ni terse level seeded to full"
else
  say "FAIL: ni terse seed missing or wrong"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  say "isolation check: ALL CLEAN"
else
  say "isolation check: FAILURES ABOVE"
fi
exit "$fail"
