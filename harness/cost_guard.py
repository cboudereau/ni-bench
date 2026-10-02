"""NFR2 cost guard: stop the matrix once total spend exceeds 50 x n USD.

Per-trial ``total_cost_usd`` already sums subject and simulator (judge joins in
task 5), so the guard sees the whole spend.
"""

from __future__ import annotations

from dataclasses import dataclass

COST_CAP_PER_TRIAL_SET_USD = 50.0


def threshold_for(n: int) -> float:
    return COST_CAP_PER_TRIAL_SET_USD * n


@dataclass
class CostGuard:
    threshold_usd: float
    spent_usd: float = 0.0

    def record(self, cost_usd: float) -> None:
        self.spent_usd += cost_usd

    @property
    def exceeded(self) -> bool:
        return self.spent_usd > self.threshold_usd
