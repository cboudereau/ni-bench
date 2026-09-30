# ni-bench setup

Benchmark harness comparing Claude Code plugins (baseline, openspec, superpowers, ni) on identical scenarios in isolated Docker arms.

## Prerequisites

- Docker with Compose v2 (tested: Docker 29.4.3, Compose v5.1.3)
- Claude Code CLI on the host (tested: 2.1.285) — only used to generate the credential
- [uv](https://docs.astral.sh/uv/) on PATH (`export PATH="$HOME/.local/bin:$PATH"`)
- A trusted machine: arm containers run `--dangerously-skip-permissions`; never run the matrix on a host with secrets mounted into the repo

## 1. Credential

The arms, judge, and simulator authenticate through a single variable in `.env` (gitignored, never baked into images).

Option A — subscription token (bills your Claude plan). `claude setup-token` is interactive: never wrap it in command substitution or pipes, its prompts get captured and the command hangs.

1. Generate the token:
   ```bash
   claude setup-token
   ```
2. A browser window opens. Approve the authorisation, copy the code shown, and paste it back into the terminal when prompted.
3. The command prints a long-lived token starting with `sk-ant-oat01-`. Copy it.
4. Write the `.env` file at the repo root (replace the placeholder with your token):
   ```bash
   cd <repo-root>
   printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' 'sk-ant-oat01-PASTE-HERE' > .env
   chmod 600 .env
   ```
5. Verify — must print `1`:
   ```bash
   grep -c 'sk-ant-oat01' .env
   ```

Option B — Console API key (pay per token):

```bash
cd <repo-root>
printf 'ANTHROPIC_API_KEY=%s\n' 'sk-ant-api...' > .env
chmod 600 .env
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
