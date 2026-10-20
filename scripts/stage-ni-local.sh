#!/usr/bin/env bash
# Stage an unpublished ni checkout as a local marketplace for the ni arm.
#
#   NI_LOCAL_SRC=/path/to/ni-checkout ./scripts/stage-ni-local.sh
#
# build.sh and bench.sh call this when NI_LOCAL_SRC is set (environment or
# .env) and build the ni arm with NI_SOURCE=local; unset, the arm installs the
# latest marketplace release. Writes arms/ni-local/ (git-ignored): a
# marketplace named itsaspacestation whose only plugin, ni, is a copy of the
# checkout, so the arm installs ni@itsaspacestation exactly like the published
# path and the isolation check reads the same plugin id. The staged
# plugin.json version gets a +local.<sha> build tag so REPORT.md never passes
# a checkout off as a release.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${NI_LOCAL_SRC:?set NI_LOCAL_SRC to the ni checkout to stage}"
[ -f "$SRC/.claude-plugin/plugin.json" ] || {
  echo "stage-ni-local: not a ni plugin checkout (no .claude-plugin/plugin.json): $SRC" >&2
  exit 1
}

# HEAD sha read from the checkout's own git metadata (worktree-aware); no git
# command runs against the foreign repository.
head_sha() {
  local src="$1" gitdir head ref common
  if [ -f "$src/.git" ]; then gitdir="$(sed 's/^gitdir: //' "$src/.git")"; else gitdir="$src/.git"; fi
  head="$(cat "$gitdir/HEAD")"
  case "$head" in
    ref:*)
      ref="${head#ref: }"; common="$gitdir"
      [ -f "$gitdir/commondir" ] && common="$gitdir/$(cat "$gitdir/commondir")"
      if [ -f "$gitdir/$ref" ]; then cat "$gitdir/$ref"
      elif [ -f "$common/$ref" ]; then cat "$common/$ref"
      else awk -v ref="$ref" '$2 == ref { print $1 }' "$common/packed-refs"; fi ;;
    *) printf '%s\n' "$head" ;;
  esac
}

SHORT="$(head_sha "$SRC" | tr -d '[:space:]' | cut -c1-7)"
[ -n "$SHORT" ] || { echo "stage-ni-local: could not resolve HEAD of $SRC" >&2; exit 1; }

DEST=arms/ni-local
rm -rf "$DEST"
mkdir -p "$DEST/.claude-plugin" "$DEST/ni"
# shipped tree only: no git metadata, no workspace docs, no resume anchor
rsync -a --exclude .git --exclude docs --exclude CLAUDE.md --exclude .github "$SRC"/ "$DEST/ni"/

VERSION="$(python3 - "$DEST/ni/.claude-plugin/plugin.json" "$SHORT" <<'PY'
import json, sys
path, short = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as f:
    m = json.load(f)
m["version"] = m["version"].split("+", 1)[0] + "+local." + short
with open(path, "w", encoding="utf-8") as f:
    json.dump(m, f, indent=2)
    f.write("\n")
print(m["version"])
PY
)"

cat > "$DEST/.claude-plugin/marketplace.json" <<'EOF'
{
  "name": "itsaspacestation",
  "description": "Local staging of the ni plugin for ni-bench (never committed).",
  "owner": { "name": "ni-bench" },
  "plugins": [
    { "name": "ni", "source": "./ni", "description": "ni staged from a local checkout" }
  ]
}
EOF
echo "staged $SRC as ni $VERSION in $DEST"
