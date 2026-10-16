---
status: accepted
---
# Skill mapping per scenario family and install source

Addresses: [FR1](../designs/mattpocock-arm.md#fr1), [FR2](../designs/mattpocock-arm.md#fr2), [FR6](../designs/mattpocock-arm.md#fr6)

## Problem

mattpocock-skills ships 27 skills and no single "plan" or "build" entry point. The explicit-flow track names one canonical workflow per arm per family. Which skill chain stands for the plugin in each family, and from which source is the plugin installed?

The plugin's own router (`ask-matt`, read at commit `49dd158`) defines the routes:
- main flow: `grill-with-docs` → (`to-spec` → `to-tickets`) → `implement` (drives `tdd`, closes with `code-review`) → `retro`
- on-ramp "something's broken": `diagnosing-bugs`
- on-ramp "huge foggy effort, too big for one session": `wayfinder`, which "hands off, it doesn't build" and produces decisions, not deliverables
- standalone `tdd`: "when you just want to build a concrete behaviour test-first without a full spec"

## Options

Plan family (plan-easy, plan-complex: a written plan a developer can implement from, planning only)

| Option | Pros | Cons |
|---|---|---|
| A. `grill-with-docs` → `to-spec` → `to-tickets` | The plugin's documented idea-to-plan route; produces a spec (human) and tickets (machine), matching the two-audience judge | Three user-invoked skills in one line; grilling costs simulator turns; `to-spec` forbids file paths (bias vs plan-easy criterion 3) |
| B. `grill-me` only | One skill, cheapest | Leaves no artifact: postcheck requires a `.md`; not a plan |
| C. `wayfinder` for plan-complex | Built for greenfield fog | Router says it produces decisions, not a plan, and is for multi-session work; the scenario wants one implementable plan |
| D. `to-spec` alone | No interview, one artifact | Skips the plugin's flagship step (grilling); unfair to the plugin's own claim |

Debug family (debug-easy, debug-complex, ported-debug)

| Option | Pros | Cons |
|---|---|---|
| E. `diagnosing-bugs` | The only debugging skill; model-invoked, phase-gated root-cause loop, mirrors ni:debug and superpowers systematic-debugging | Phase 3 shows hypotheses to the user "without blocking", may cost a simulator turn |
| F. implicit (no line) | Model-invoked skill may trigger alone | Session-log verification on other arms showed zero autonomous triggers headless; keep the track uniform |

Build family (build-small, ported-build)

| Option | Pros | Cons |
|---|---|---|
| G. `implement` | The plugin's build entry point: drives `tdd` at seams, closes with `code-review`, commits; parallels "planning workflow to drive this implementation" on other arms | Expects a spec or tickets; here the prompt's prose spec stands in; `code-review` spawns two subagents (cost) |
| H. `tdd` alone | Cheapest; the router allows it "without a full spec" | Measures one discipline, not the workflow; other arms are named their full flow |
| I. `to-spec` → `to-tickets` → `implement` | Full main flow | Planning a 3-test function into tickets is overhead the plugin's router does not prescribe for single-session work |

Install source

| Option | Pros | Cons |
|---|---|---|
| J. `claude plugin marketplace add mattpocock/skills` then `install mattpocock-skills@mattpocock` | Same pattern as the superpowers and ni arms (author marketplace, head of main); `plugin list` records the version | Not the route the README documents for Claude Code |
| K. `install mattpocock-skills@claude-plugins-official` | The documented Claude Code route | Listing is sha-pinned and has lagged main (plugin ADR 0002, 2026-08-05); version measured may trail the author's release |

## Decision

- Plan family: **A**. The appended line: `Use the grill-with-docs, to-spec, and to-tickets skill workflow for this plan.` One line, names only the arm's tools, keeps the word `workflow` for the parity test.
- Debug family: **E**. Line: `Use the diagnosing-bugs skill workflow for this investigation.`
- Build family: **G**. Line: `Use the implement skill workflow to drive this implementation.`
- Install: **J**, the author marketplace, for symmetry with the two other plugin arms and so the measured version is the author's current release. `scripts/plugin-versions.sh` records whatever resolved.

Structural bias to disclose in the bias table (FR6): plan-easy criterion 3 (traceability to `cli.py`, `build_parser`, `stats.summarize`) rewards what `to-spec` forbids ("Do NOT include specific file paths or code snippets"). Expected direction: against mattpocock on plan-easy traceability; neutral elsewhere. The home-grown plan/debug families stay ni-shaped, the ported ones superpowers-shaped, as already recorded.

## Consequences

Easier: the arm enters the explicit track with the same instruction shape as the others; the two-audience judge gets a human layer (spec, glossary, ADRs) and a machine layer (tickets) without new rubric work. Harder: the plan line names three skills where others name one; the comparability caveat already disclosed for the explicit track covers it. `implement` adds a `code-review` subagent pass per build trial, raising the arm's cost and tokens: that is the plugin's workflow, measured as-is.
