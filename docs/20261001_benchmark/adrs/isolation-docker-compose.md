---
status: accepted
---
# Isolation: docker compose with throwaway HOME per trial

Addresses: [FR1](../designs/benchmark.md#fr1), [NFR1](../designs/benchmark.md#nfr1)

## Problem

Each arm must run Claude Code with exactly one plugin (or none), with no leakage from the host `~/.claude` (this machine has ni, platform-d-edge, and official plugins installed) and no cross-trial session state. superpowers-evals documents a real leak of this kind (Codex reading host-side skill configs).

## Options

| Option | Pros | Cons |
|---|---|---|
| A. docker compose, one service per arm, plugin baked into image, throwaway `$HOME` volume per trial | Full filesystem isolation; arm images reviewable and pinned; matches user request; compose config is the isolation manifest | Image build per arm; plugin install must work non-interactively at build |
| B. Single container, swap `CLAUDE_CONFIG_DIR` per trial | One image | One bad trial can pollute shared layers; plugin set changes at runtime, harder to audit |
| C. Reuse everyharness-container | Battle-tested | ~15 GB image, 23 agents we do not need, external dependency |

## Decision

Option A. One `Dockerfile.<arm>` per arm from a common base (node + pinned Claude Code CLI). Plugin install at build time: `claude plugin marketplace add <repo>` + `claude plugin install <name>` for superpowers and ni; `npm install -g @fission-ai/openspec` for openspec (it is a CLI, not a plugin — `openspec init` runs per trial on the fixture copy). Per trial: fresh tmpfs-backed `$HOME`, fixture copied in, only `ANTHROPIC_API_KEY` passed as env, no host mounts except the trial directory. Fallback if `claude plugin install` resists build-time non-interactive use: COPY a pinned git clone into the image plugin cache path (time-boxed in the design doc rabbit holes).

## Consequences

Easier: auditable isolation (NFR1 checkable from compose config), reproducible arms via pinned versions, parallel trial execution. Harder: four Dockerfiles to keep in sync (mitigated by a shared base image); plugin version bumps require rebuild.
