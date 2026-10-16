#!/usr/bin/env bash
# Build the shared base image, then every compose service.
set -euo pipefail
cd "$(dirname "$0")/.."

docker build -f arms/Dockerfile.base -t ni-bench-base arms
docker compose build
