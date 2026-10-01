"""CLI entry: ``python -m harness.run {smoke|matrix} [--n N]`` (driven by run.sh).

smoke: plan-easy, all arms, n=1. matrix: all scenarios, all arms, n from --n
(run.sh passes BENCH_N, default 3). Exit 0 complete, 2 when the cost guard
stopped the matrix (results marked partial in results/matrix.json).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from harness.arms import ARMS
from harness.runner import run_matrix
from harness.scenarios import REPO_ROOT, SCENARIOS


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness.run", description=__doc__)
    parser.add_argument("mode", choices=["smoke", "matrix"])
    parser.add_argument("--n", type=int, default=None, help="trials per arm x scenario")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=None,
        help="per-run results directory (default: results/)",
    )
    args = parser.parse_args(argv)

    if args.mode == "smoke":
        scenarios = [s for s in SCENARIOS if s.id == "plan-easy"]
        n = args.n or 1
    else:
        scenarios = list(SCENARIOS)
        n = args.n or 3

    results_root = args.results_root or REPO_ROOT / "results"
    result = run_matrix(ARMS, scenarios, n, results_root=results_root)
    status = "PARTIAL (cost guard)" if result.partial else "complete"
    print(
        f"{args.mode}: {len(result.trials)} trials, "
        f"{result.spent_usd:.2f} USD spent, {status}"
    )
    return 2 if result.partial else 0


if __name__ == "__main__":
    sys.exit(main())
