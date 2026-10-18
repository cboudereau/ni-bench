#!/usr/bin/env bash
# Build the shared base image, then every compose service.
#
#   ./scripts/build.sh              # cached: plugin layers keep the version they resolved at first build
#   ./scripts/build.sh --no-cache   # refresh: every arm reinstalls its plugin at the current latest
#
# Plugin installs run at build time and resolve "latest" once; Docker caches
# that layer, so a later cached build keeps the old version. Pass --no-cache
# (or any other `docker compose build` flag) to re-resolve. The CLI pin lives
# in arms/Dockerfile.base and is not affected by plugin refreshes.
set -euo pipefail
cd "$(dirname "$0")/.."

# ni source: NI_LOCAL_SRC (environment, else .env) names an unpublished
# checkout to stage and build from; unset, the arm installs the latest release.
# shellcheck source=scripts/ni-source.sh
. ./scripts/ni-source.sh

docker build -f arms/Dockerfile.base -t ni-bench-base arms
docker compose build "$@"
