#!/usr/bin/env bash
# Seed the (possibly throwaway, per-trial) $HOME from the arm template baked at
# build time (isolation-docker-compose ADR), run per-arm init hooks
# (verbosity-policy ADR), then exec the requested command.
set -euo pipefail

TEMPLATE=/opt/arm-home
# Seed once per trial HOME: the resume loop reuses the same bind-mounted HOME
# across containers, and re-copying fails on the read-only git pack files the
# first copy created (task 7 smoke run) - and would clobber session state.
SEEDED="$HOME/.arm-home-seeded"
if [ -d "$TEMPLATE" ] && [ "$HOME" != "$TEMPLATE" ] && [ ! -e "$SEEDED" ]; then
  cp -a "$TEMPLATE/." "$HOME/"
  touch "$SEEDED"
fi

for hook in /opt/arm-init.d/*.sh; do
  [ -e "$hook" ] || continue
  bash "$hook"
done

exec "$@"
