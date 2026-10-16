#!/usr/bin/env bash
# tracker-seed ADR: headless stand-in for the interactive /setup-matt-pocock-skills.
# Writes the `## Agent skills` block (local-markdown tracker, default triage
# labels, domain docs) into the throwaway HOME's user-level CLAUDE.md before
# claude launches. Idempotent: an existing file is left untouched so --resume
# turns never rewrite it.
set -euo pipefail
target="$HOME/.claude/CLAUDE.md"
[ -e "$target" ] && exit 0
mkdir -p "$HOME/.claude"
cat > "$target" <<'SEED'
## Agent skills

### Issue tracker
Issues and specs live as local markdown under `.scratch/` in the working directory.
One feature per directory `.scratch/<feature-slug>/`; the spec is `spec.md`; tickets are one file each at `issues/<NN>-<slug>.md` numbered from `01`; triage state is a `Status:` line near the top of each file. "Publish to the issue tracker" means create the file. Do not run `/setup-matt-pocock-skills`: this is the configuration.

### Triage labels
Defaults: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

### Domain docs
Single-context: `GLOSSARY.md` at the repo root and ADRs under `docs/adr/`. Proceed silently when they do not exist; create them lazily.
SEED
