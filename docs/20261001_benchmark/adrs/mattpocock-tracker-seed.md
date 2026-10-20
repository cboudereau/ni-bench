---
status: accepted
---
# Headless tracker seed in the throwaway HOME

Addresses: [FR3](../designs/mattpocock-arm.md#fr3), [FR4](../designs/mattpocock-arm.md#fr4)

## Problem

`to-spec`, `to-tickets`, `implement`, and `implement-spec` read the issue tracker and triage labels "provided to you" by `/setup-matt-pocock-skills`, an interactive skill that writes `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, `docs/agents/triage-labels.md`, and an `## Agent skills` block in the repo's `CLAUDE.md`. Absent that, each skill says "tell the user to run `/setup-matt-pocock-skills`". Headless, the simulated user answers "your call, decide and continue", and the agent either runs the setup interview (burning simulator turns on configuration, not the task) or guesses. The arm container has no forge credential, so only the local-markdown tracker is possible.

## Options

| Option | Pros | Cons |
|---|---|---|
| A. No seed; the prompt line alone | Measures the raw headless experience | Spends up to 6 user turns on setup questions; conflates configuration cost with workflow value; other arms are not measured on first-run setup either (openspec's `openspec init` is the agent's own `/opsx:` step, but its config has no interactive questions) |
| B. Seed the setup output into the fixture workspace (`docs/agents/*.md`, `CLAUDE.md`) per trial | Exactly what the setup skill writes | Fixture differs per arm; `fixture.diff` and `plan_words` must exclude the seed; the judge's artifact set needs new exclusion rules |
| C. Seed into the throwaway HOME: `~/.claude/CLAUDE.md` carrying the `## Agent skills` block with the local-tracker conventions, domain-doc rules, and default triage labels inline | Same mechanism as the ni arm's terse seed (`/opt/arm-init.d` hook writing into `$HOME`); workspace stays identical across arms; no classification exclusions; user-level memory is a supported Claude Code surface | Diverges from the skill's own layout (repo files), so a skill that reads `docs/agents/issue-tracker.md` by path finds nothing; mitigated because every skill reads the config from context, and the setup skill itself only asks `CLAUDE.md` to point at those files |
| D. Extend the prompt line with the tracker choice | No infrastructure | Breaks the one-line parity rule and puts configuration text in the measured prompt |

## Decision

**C.** `arms/mattpocock-init.sh` (copied to `/opt/arm-init.d/`, idempotent: skip when the file exists so `--resume` turns do not rewrite it) writes `$HOME/.claude/CLAUDE.md` containing:

```markdown
## Agent skills

### Issue tracker
Issues and specs live as local markdown under `.scratch/` in the working directory.
One feature per directory `.scratch/<feature-slug>/`; the spec is `spec.md`; tickets are one file each at `issues/<NN>-<slug>.md` numbered from `01`; triage state is a `Status:` line near the top of each file. "Publish to the issue tracker" means create the file. Do not run `/setup-matt-pocock-skills`: this is the configuration.

### Triage labels
Defaults: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

### Domain docs
Single-context: `GLOSSARY.md` at the repo root and ADRs under `docs/adr/`. Proceed silently when they do not exist; create them lazily.
```

The text is the setup skill's own templates ([issue-tracker-local.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md), [triage-labels.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/triage-labels.md), [domain.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/domain.md)) condensed; it adds no instruction a user running the setup skill with default answers would not have.

`classify_artifact("mattpocock", path)`: `.scratch/*/issues/*.md` → `machine`; everything else authored → `human`. The HOME seed never enters the workspace, so no `excluded` rule is needed beyond the shared `.claude/**` one.

## Consequences

Easier: the arm's first turn goes straight to the task, like the other arms; the fixture stays byte-identical across arms; the machine layer (tickets) is classified without special cases. Harder: the seed is benchmark-authored text inside an arm, the same category of asymmetry the verbosity-policy ADR already discloses for ni's terse seed; the REPORT.md header and ANALYSIS.md disclosures name it. If the plugin later ships a non-interactive setup mode, replace the seed with it.
