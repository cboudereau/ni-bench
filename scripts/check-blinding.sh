#!/usr/bin/env bash
# NFR4 blinding check (task 5, blind-llm-judge ADR).
# Greps every saved judge input for arm identifiers - word-bounded,
# case-insensitive, the exact measure from DESIGN.md NFR4. Exits 0 when zero
# matches or when no judge inputs exist yet; prints offending lines otherwise.
set -euo pipefail
cd "$(dirname "$0")/.."

pattern='\b(ni|openspec|opsx|superpowers|baseline|natural-intelligence|fission|obra|itsaspacestation|terse)\b'

inputs=()
while IFS= read -r file; do
  inputs+=("$file")
done < <(find results -type f -path '*/judge/input.txt' 2>/dev/null || true)

if [ "${#inputs[@]}" -eq 0 ]; then
  echo "blinding check: no judge inputs under results/ yet - trivially clean"
  exit 0
fi

if grep -HniE "$pattern" "${inputs[@]}"; then
  echo "blinding check: FAILURES ABOVE (${#inputs[@]} inputs scanned)"
  exit 1
fi
echo "blinding check: ALL CLEAN (${#inputs[@]} inputs scanned)"
