# ni-bench

Benchmark comparing Claude Code plugins (baseline, openspec, superpowers, ni) on identical scenarios in isolated Docker arms, scored by a blind LLM judge plus deterministic post-checks. Design and ADRs: [docs/20261001_benchmark/](docs/20261001_benchmark/README.md).

## 1. Setup

Prerequisites:

- Docker with Compose v2 (tested: Docker 29.4.3, Compose v5.1.3)
- Claude Code CLI on the host (tested: 2.1.285) — only used to generate the credential
- [uv](https://docs.astral.sh/uv/) on PATH (`export PATH="$HOME/.local/bin:$PATH"`)
- A trusted machine: arm containers run `--dangerously-skip-permissions`; never run the matrix on a host with secrets mounted into the repo

Credential — one variable in `.env` at the repo root (gitignored, never baked into images).

Option A, subscription token (bills your Claude plan). `claude setup-token` is interactive: never wrap it in command substitution or pipes, its prompts get captured and the command hangs.

1. Generate the token:
   ```bash
   claude setup-token
   ```
2. A browser window opens. Approve the authorisation, copy the code shown, and paste it back into the terminal when prompted.
3. The command prints a long-lived token starting with `sk-ant-oat01-`. Copy it.
4. Write the `.env` file (replace the placeholder):
   ```bash
   printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' 'sk-ant-oat01-PASTE-HERE' > .env
   chmod 600 .env
   ```
5. Verify — must print `1`:
   ```bash
   grep -c 'sk-ant-oat01' .env
   ```

Option B, Console API key (pay per token):

```bash
printf 'ANTHROPIC_API_KEY=%s\n' 'sk-ant-api...' > .env
chmod 600 .env
```

Keep the token out of shared terminals and transcripts. Rotate it after the benchmark if the machine is shared.

Build and verify (no API spend):

```bash
uv run pytest && uv run ruff check harness/   # unit suite, no docker, no API
docker compose build                           # base + 4 arm images + harness service
./scripts/check-isolation.sh                   # no host config leaks
```

## 2. How to run the benchmark

One command per run; each run gets a dedicated timestamped folder:

```bash
./scripts/bench.sh            # full matrix: 4 arms x 7 scenarios, n=3 — cost guard 50 x n USD
BENCH_N=1 ./scripts/bench.sh  # cheaper full matrix (n=1)
./scripts/bench.sh smoke      # plan-easy only, n=1 — a few USD
```

The run folder `results/run-<timestamp>/` receives:

- one trial dir per (scenario, arm, trial): raw CLI JSON per turn, simulator transcript, fixture diff, postcheck output, `result.json`, blinded judge input/output
- `matrix.json` (n, date, spend, partial flag)
- `REPORT.md` (generated KPI tables)
- `ANALYSIS.md` stub (the reading — see section 3)

All run outputs are local and git-excluded. Live trials bill real API spend; the cost guard stops the matrix at 50 × n USD and marks the report partial.

Extra checks:

```bash
./scripts/cost-check.sh results/run-<timestamp>   # spend vs cap
./scripts/check-blinding.sh                       # judge inputs carry no arm identifiers
./scripts/check-isolation.sh                      # no host config leaks
```

## 3. Analyzing the report (results)

### Reading REPORT.md

- Header: subject/judge/simulator models, CLI and plugin versions, n, per-arm verbosity configuration, run date. Resource percents are relative to this arm set — adding or removing an arm changes percents, never raw values.
- One table per scenario, origin-tagged (home-grown or superpowers-evals). Rows = KPIs, columns = arms, cell = `score% (raw)`.
- Every percent reads higher = better; 100% = best arm in that row:
  - Resource KPIs (`tokens_total`, `cost_usd`, `duration_s`, `turns`, `user_turns`, `plan_words`): raw is lower-better, normalised `min(arms)/value × 100`.
  - Judge KPIs (`plan_quality`, `verbosity_score`): the blind judge's 0–100 score, shown directly.
  - `outcome`: pass-rate over determinate trials.
- `plan_words` is scored only among arms with `plan_quality ≥ 50` (quality floor); below-floor arms show `— (raw)`. A one-word plan cannot win verbosity.
- Verdict rule: deterministic postchecks override the judge — a postcheck fail is a fail regardless of judge score; with green postchecks, `plan_quality < 50` still fails the trial.
- `indeterminate` footnote row: trials excluded from medians (infra errors, timeouts, judge parse failures).

### Writing ANALYSIS.md

The report stays pure numbers by design; the reading goes into the run's `ANALYSIS.md` (stub pre-created). Sections:

1. **Winners at a glance** — per scenario: outcome pass-rate first, then judged quality, then cost; cite the REPORT.md cell for every claim.
2. **Bias table** — expected structural bias per scenario (home-grown plan/debug families are ni-shaped; ported ones superpowers-shaped; the verbosity KPI favours ni by configuration) and whether results follow or defy it. A win against the grain is the stronger signal.
3. **True enhancement vs baseline** — per arm, where outcome and quality beat the no-plugin control, and at what token/cost delta.
4. **Recommendations and disclosures** — per-plugin advice, benchmark limits (the judge sees only final messages and markdown artifacts, so process scores partly grade self-reporting; artifact structure can leak the arm despite blinding; author affiliation).

### Triaging a single verdict

Every trial dir is self-contained — no re-run needed:

- `turns/turn-NN.json` — raw subject CLI JSON per turn (tokens, cost, session id)
- `simulator/transcript.json` — what the simulated user was asked and answered
- `fixture.diff` — every change the arm made to the fixture
- `postcheck.txt` — deterministic check output (hidden tests included)
- `judge/input.txt` and `judge/output.json` — exactly what the judge saw (blinded) and scored

Disagree with a score? Read `judge/input.txt` first: the judge only knows what is in there.
