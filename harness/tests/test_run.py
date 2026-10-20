"""harness.run CLI: scenario selection for a partial matrix (BENCH_SCENARIOS)."""

import pytest

from harness.run import select_scenarios
from harness.scenarios import SCENARIOS


def test_select_scenarios_none_or_blank_keeps_all():
    assert select_scenarios(SCENARIOS, None) == list(SCENARIOS)
    assert select_scenarios(SCENARIOS, " ") == list(SCENARIOS)


def test_select_scenarios_keeps_matrix_order_and_drops_duplicates():
    chosen = select_scenarios(SCENARIOS, "ported-build, build-small,build-small")
    assert [s.id for s in chosen] == [
        s.id for s in SCENARIOS if s.id in {"build-small", "ported-build"}
    ]


def test_select_scenarios_unknown_id_names_the_known_ones():
    with pytest.raises(SystemExit, match="build-smal.*build-small"):
        select_scenarios(SCENARIOS, "build-smal")
