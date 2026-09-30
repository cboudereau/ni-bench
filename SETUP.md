# ni-bench setup

Benchmark harness comparing Claude Code plugins (baseline, openspec, superpowers, ni) on identical scenarios in isolated Docker arms.

## Prerequisites

- Docker with Compose v2 (tested: Docker 29.4.3, Compose v5.1.3)
- Claude Code CLI on the host (tested: 2.1.285) — only used to generate the credential
- [uv](https://docs.astral.sh/uv/) on PATH (`export PATH="$HOME/.local/bin:$PATH"`)
- A trusted machine: arm containers run `--dangerously-skip-permissions`; never run the matrix on a host with secrets mounted into the repo

## 1. Credential

The arms, judge, and simulator authenticate through a single variable in `.env` (gitignored, never baked into images).

Subscription token (bills your Claude plan). `claude setup-token` is interactive — do not wrap it in command substitution or pipes; that hides its prompts and hangs. Two steps:

```bash
claude setup-token
# browser opens; approve, paste the code back; the command prints sk-ant-oat01-...
```

```bash
cd <repo-root> && printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' 'sk-ant-oat01-PASTE-HERE' > .env && chmod 600 .env
```

Console API key alternative (pay per token):

```bash
printf 'ANTHROPIC_API_KEY=%s\n' 'sk-ant-api...' > .env && chmod 600 .env
```

Keep the token out of shared terminals and transcripts. Rotate it after the benchmark if the machine is shared.

## 2. Build and verify

```bash
uv run pytest && uv run ruff check harness/   # unit suite, no docker, no API
docker compose build                           # base + 4 arm images + harness
./scripts/check-isolation.sh                   # no host config leaks, no API calls
```

## 3. Run

```bash
./scripts/run.sh smoke    # plan-easy, 4 arms, n=1 — first live spend, a few USD
./scripts/run.sh matrix   # 7 scenarios, 4 arms, n=3 (BENCH_N overrides) — cost guard 50 x n USD
```

## 4. Report

```bash
./scripts/report.sh        # renders REPORT.md from results/
./scripts/cost-check.sh    # spend vs cap
./scripts/check-blinding.sh
```

Plan, ADRs, and task breakdown: `docs/workspace/benchmark/`.
