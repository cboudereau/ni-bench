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

## 3. Run — one command per benchmark run

```bash
./scripts/bench.sh            # full matrix, 4 arms x 7 scenarios, n=3 — cost guard 50 x n USD
BENCH_N=1 ./scripts/bench.sh  # cheaper full matrix
./scripts/bench.sh smoke      # plan-easy only, n=1 — a few USD
```

Each run gets its own folder `results/run-<timestamp>/` containing the trial dirs, matrix.json, the rendered REPORT.md, and an ANALYSIS.md stub to fill (FR9 reading). All run outputs are local and git-excluded.

## 4. Extra checks

```bash
./scripts/cost-check.sh results/run-<timestamp>   # spend vs cap
./scripts/check-blinding.sh                       # judge inputs carry no arm identifiers
./scripts/check-isolation.sh                      # no host config leaks
```

Plan, ADRs, and task breakdown: `docs/workspace/benchmark/`.
