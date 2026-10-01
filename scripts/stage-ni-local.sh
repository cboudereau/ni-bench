#!/usr/bin/env bash
# Stage an UNPUBLISHED ni checkout for the NI_SOURCE=local arm build
# (isolation-docker-compose ADR local-COPY fallback).
#
#   NI_LOCAL_SRC=/path/to/ni-checkout ./scripts/stage-ni-local.sh
#
# Produces arms/ni-local/ (git-ignored, never committed):
#   home/   - complete /opt/arm-home overlay replicating what
#             `claude plugin marketplace add` + `claude plugin install` write:
#             plugin cache dir, installed_plugins.json ledger,
#             known_marketplaces.json, marketplace dir, settings.json
#   version-label.txt - honest report label, <version>+local.<short-sha>,
#             exported by bench.sh as BENCH_PLUGIN_OVERRIDES
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${NI_LOCAL_SRC:?set NI_LOCAL_SRC to the ni checkout to stage}"
[ -f "$SRC/.claude-plugin/plugin.json" ] || {
  echo "not a ni plugin checkout (no .claude-plugin/plugin.json): $SRC" >&2
  exit 1
}

# HEAD sha without running git against the foreign checkout (worktree-safe):
# resolve .git file -> gitdir -> HEAD -> ref via commondir, loose or packed.
head_sha() {
  local src="$1" gitdir head ref common
  if [ -f "$src/.git" ]; then
    gitdir="$(sed 's/^gitdir: //' "$src/.git")"
  else
    gitdir="$src/.git"
  fi
  head="$(cat "$gitdir/HEAD")"
  case "$head" in
    ref:*)
      ref="${head#ref: }"
      common="$gitdir"
      [ -f "$gitdir/commondir" ] && common="$gitdir/$(cat "$gitdir/commondir")"
      if [ -f "$gitdir/$ref" ]; then
        cat "$gitdir/$ref"
      elif [ -f "$common/$ref" ]; then
        cat "$common/$ref"
      else
        awk -v ref="$ref" '$2 == ref { print $1 }' "$common/packed-refs"
      fi
      ;;
    *) printf '%s\n' "$head" ;;
  esac
}

VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
  "$SRC/.claude-plugin/plugin.json")"
SHA="$(head_sha "$SRC" | tr -d '[:space:]')"
[ -n "$SHA" ] || { echo "could not resolve HEAD sha of $SRC" >&2; exit 1; }
SHORT="${SHA:0:7}"
LABEL="$VERSION+local.$SHORT"
NOW="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"

DEST=arms/ni-local
HOME_DIR="$DEST/home/.claude"
PLUGINS="$HOME_DIR/plugins"
CACHE="$PLUGINS/cache/itsaspacestation/ni/$VERSION"
MARKET="$PLUGINS/marketplaces/itsaspacestation"

rm -rf "$DEST"
mkdir -p "$CACHE" "$MARKET/.claude-plugin"
rsync -a --exclude .git "$SRC"/ "$CACHE"/

# ledger: what `claude plugin install ni@itsaspacestation` writes, with the
# installPath pointing at the baked cache copy
cat > "$PLUGINS/installed_plugins.json" <<EOF
{
  "version": 2,
  "plugins": {
    "ni@itsaspacestation": [
      {
        "scope": "user",
        "installPath": "/opt/arm-home/.claude/plugins/cache/itsaspacestation/ni/$VERSION",
        "version": "$VERSION",
        "installedAt": "$NOW",
        "lastUpdated": "$NOW",
        "gitCommitSha": "$SHA"
      }
    ]
  }
}
EOF

cat > "$PLUGINS/known_marketplaces.json" <<EOF
{
  "itsaspacestation": {
    "source": {
      "source": "github",
      "repo": "itsaspacestation/claude-marketplace"
    },
    "installLocation": "/opt/arm-home/.claude/plugins/marketplaces/itsaspacestation",
    "lastUpdated": "$NOW"
  }
}
EOF

# minimal marketplace manifest (the real clone adds only LICENSE/README/.git)
cat > "$MARKET/.claude-plugin/marketplace.json" <<'EOF'
{
  "name": "itsaspacestation",
  "description": "Claude Code plugins by itsaspacestation, each in its own repository.",
  "owner": {
    "name": "Clément Boudereau",
    "url": "https://github.com/itsaspacestation"
  },
  "plugins": [
    {
      "name": "ni",
      "source": {
        "source": "github",
        "repo": "itsaspacestation/natural-intelligence"
      },
      "description": "ni, natural intelligence: terse replies, TDD, DDD, git conventions, code and merge request reviews, .NET and Rust builds, planning, and evidence-based analysis.",
      "homepage": "https://github.com/itsaspacestation/natural-intelligence",
      "license": "Apache-2.0",
      "category": "development"
    }
  ]
}
EOF

cat > "$HOME_DIR/settings.json" <<'EOF'
{
  "extraKnownMarketplaces": {
    "itsaspacestation": {
      "source": {
        "source": "github",
        "repo": "itsaspacestation/claude-marketplace"
      }
    }
  },
  "enabledPlugins": {
    "ni@itsaspacestation": true
  }
}
EOF

printf '%s\n' "$LABEL" > "$DEST/version-label.txt"
echo "staged $SRC at $SHA -> $DEST ($LABEL)"
