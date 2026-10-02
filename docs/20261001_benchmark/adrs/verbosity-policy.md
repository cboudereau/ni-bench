---
status: accepted
---
# Per-plugin verbosity policy

Addresses: [FR3](../designs/benchmark.md#fr3)

## Problem

The benchmark judges verbosity. Each plugin should run at its own least-verbose supported setting; a plugin without a verbosity setting runs at its default. The setting must be applied inside the isolated arm without interactive steps.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. Per-plugin native setting where it exists, default otherwise | Measures each plugin as its author intends terse use; matches user instruction | Arms differ in configuration effort (documented, not hidden) |
| B. Force all arms terse via a shared CLAUDE.md instruction | Uniform | Measures our prompt, not the plugins; contaminates baseline |
| C. All defaults | Zero config | Ignores ni's flagship terse feature — the user asked for it on |

## Decision

Option A. Verified per plugin:

- **ni**: terse mode, level `full`. Seeded non-interactively: write `full` into `$HOME/.claude/ni/terse` in the throwaway home before launch (plain-text state file read by the SessionStart hook `scripts/terse-activate.sh`; default would be `lite`).
- **openspec**: no verbosity or terseness option (checked `openspec/config.yaml` levers: `context`, `rules`, `operations.*.guidance`, `schema.yaml` — style control would mean writing custom rules, which is our prompt, not their setting). Runs default. `OPENSPEC_TELEMETRY=0` set.
- **superpowers**: no verbosity option found in the plugin. Runs default.
- **baseline**: default Claude Code output style.

REPORT.md states each arm's verbosity configuration in the metadata header so readers see the asymmetry is deliberate.

## Consequences

Easier: ni measured at its intended terse operating point; other arms untouched, no invented settings. Harder: verbosity KPI partially reflects configuration availability, not only behaviour — that is the point, and the header discloses it.
