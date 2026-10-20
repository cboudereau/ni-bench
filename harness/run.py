"""CLI entry: ``python -m harness.run {smoke|matrix} [--n N] [--scenarios a,b]``.

smoke: plan-easy, all arms, n=1. matrix: all scenarios, all arms, n from --n
(bench.sh passes BENCH_N, default 3); ``--scenarios`` narrows the matrix to a
comma-separated list of scenario ids (bench.sh passes BENCH_SCENARIOS). Exit 0
complete, 2 when the cost guard stopped the matrix (results marked partial in
<run dir>/matrix.json).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from harness.arms import ARMS
from harness.runner import plugin_overrides_from_env, run_matrix
from harness.scenarios import REPO_ROOT, SCENARIOS


def select_scenarios(scenarios: Sequence, spec: str | None) -> list:
    """Pure: the scenarios named in ``spec`` (comma list), in matrix order.

    ``None`` or empty keeps them all; an unknown id raises ``SystemExit`` with
    the known ids, so a typo never silently runs the full matrix.
    """
    if not spec or not spec.strip():
        return list(scenarios)
    wanted = {s.strip() for s in spec.split(",") if s.strip()}
    known = {s.id for s in scenarios}
    unknown = sorted(wanted - known)
    if unknown:
        raise SystemExit(
            f"unknown scenario id(s) {unknown}; known: {sorted(known)}"
        )
    return [s for s in scenarios if s.id in wanted]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness.run", description=__doc__)
    parser.add_argument("mode", choices=["smoke", "matrix"])
    parser.add_argument("--n", type=int, default=None, help="trials per arm x scenario")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=None,
        help="per-run results directory (default: .reports/)",
    )
    parser.add_argument(
        "--scenarios",
        default=None,
        help="matrix only: comma-separated scenario ids (default: all)",
    )
    args = parser.parse_args(argv)

    if args.mode == "smoke":
        scenarios = [s for s in SCENARIOS if s.id == "plan-easy"]
        n = args.n or 1
    else:
        scenarios = select_scenarios(SCENARIOS, args.scenarios)
        n = args.n or 3

    results_root = args.results_root or REPO_ROOT / ".reports"
    result = run_matrix(
        ARMS,
        scenarios,
        n,
        results_root=results_root,
        plugin_overrides=plugin_overrides_from_env(dict(os.environ)),
    )
    status = "PARTIAL (cost guard)" if result.partial else "complete"
    print(
        f"{args.mode}: {len(result.trials)} trials, "
        f"{result.spent_usd:.2f} USD spent, {status}"
    )
    return 2 if result.partial else 0


if __name__ == "__main__":
    sys.exit(main())
