#!/usr/bin/env bash
# Seed the (possibly throwaway, per-trial) $HOME from the arm template baked at
# build time (isolation-docker-compose ADR), run per-arm init hooks
# (verbosity-policy ADR), then exec the requested command.
set -euo pipefail

TEMPLATE=/opt/arm-home
if [ -d "$TEMPLATE" ] && [ "$HOME" != "$TEMPLATE" ]; then
  cp -a "$TEMPLATE/." "$HOME/"
fi

for hook in /opt/arm-init.d/*.sh; do
  [ -e "$hook" ] || continue
  bash "$hook"
done

exec "$@"
