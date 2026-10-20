#!/usr/bin/env bash
# Sourced by build.sh and bench.sh: resolve the ni arm source.
#   NI_LOCAL_SRC=/path/to/checkout  (environment wins over .env)
# Set: stage the checkout (scripts/stage-ni-local.sh) and export
# NI_SOURCE=local for the compose build arg. Unset: NI_SOURCE=marketplace,
# the latest published release, with NI_REFRESH set to the current time so
# the install layer is rebuilt and the image never keeps an older release or
# a previous run's local checkout. The caller rebuilds the ni image either
# way. Prints one line.
if [ -z "${NI_LOCAL_SRC:-}" ] && [ -f .env ]; then
  NI_LOCAL_SRC="$( { grep -E '^NI_LOCAL_SRC=' .env || true; } | tail -1 | cut -d= -f2-)"
fi
if [ -n "${NI_LOCAL_SRC:-}" ]; then
  export NI_LOCAL_SRC
  ./scripts/stage-ni-local.sh
  export NI_SOURCE=local
  export NI_REFRESH=0
  echo "ni source: local checkout $NI_LOCAL_SRC"
else
  export NI_SOURCE=marketplace
  NI_REFRESH="$(date +%s)"
  export NI_REFRESH
  echo "ni source: marketplace (latest release, reinstalled for this run)"
fi
