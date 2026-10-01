"""Task 6 report tests: KPI scoring, aggregation, deterministic REPORT.md render.

Pure functions over canned result.json files - no docker, no network
(kpi-scoring ADR formulas are binding; NFR3 determinism).
"""

import json
import shutil
from pathlib import Path

from harness.report import Report, aggregate, score_kpi

DATA = Path(__file__).parent / "data" / "report"
RESULTS = DATA / "results"


def trial(
    verdict="pass",
    tin=8000,
    tout=2000,
    cost=0.2,
    dur=40000,
    turns=4,
    user_turns=0,
    plan_words=100,
    machine_words=0,
    judge=None,
    error=None,
):
    return {
        "arm": "x",
        "scenario": "s",
        "trial_id": "t",
        "cli_json": {
            "total_cost_usd": cost,
            "duration_ms": dur,
            "num_turns": turns,
            "usage": {"input_tokens": tin, "output_tokens": tout},
        },
        "artifact_metrics": {
            "plan_words": plan_words,
            "machine_words": machine_words,
            "plan_files": [],
            "machine_files": [],
        },
        "user_turns": user_turns,
        "judge": judge,
        "verdict": verdict,
        "total_cost_usd": cost,
        "error": error,
    }


def test_score_formulas_exact():
    # golden ratios: best arm 100, others min/value x 100 (kpi-scoring ADR)
    assert score_kpi({"a": 100.0, "b": 200.0, "c": 400.0}) == {
        "a": 100.0,
        "b": 50.0,
        "c": 25.0,
    }
    # tie at the min: both score 100
    assert score_kpi({"a": 10.0, "b": 10.0, "c": 20.0}) == {
        "a": 100.0,
        "b": 100.0,
        "c": 50.0,
    }
    # min = 0 edge: arms at 0 score 100, every other arm scores 0
    assert score_kpi({"a": 0.0, "b": 5.0}) == {"a": 100.0, "b": 0.0}
    assert score_kpi({"a": 0.0, "b": 0.0}) == {"a": 100.0, "b": 100.0}
    # arms without data stay None and are excluded from the min
    assert score_kpi({"a": None, "b": 50.0}) == {"a": None, "b": 100.0}
    assert score_kpi({"a": None, "b": None}) == {"a": None, "b": None}


def test_indeterminate_excluded_from_median():
    trials = [
        trial(verdict="pass", tin=8000, tout=2000, machine_words=100,
              judge={"human_readability": 70, "agent_executability": 50,
                     "verbosity_score": 60}),
        trial(verdict="fail", tin=25000, tout=5000, machine_words=300,
              judge={"human_readability": 80, "agent_executability": 90,
                     "verbosity_score": 90}),
        trial(verdict="indeterminate", tin=999999, tout=0, error="timeout", judge=None),
    ]
    row = aggregate(trials)
    assert row["tokens_total"] == 20000  # median of 10000, 30000 - not 30000
    assert row["human_readability"] == 75
    assert row["agent_executability"] == 70
    assert row["verbosity_score"] == 75
    assert row["machine_words"] == 200
    assert row["indeterminate"] == 1
    assert row["determinate"] == 2
    assert row["outcome_pass"] == 1  # pass-rate denominator is determinate trials
    assert row["trials"] == 3


def test_aggregate_falls_back_to_v1_plan_quality():
    # old runs carry rubric-v1 judge blocks: plan_quality stands in for
    # human_readability; agent_executability stays unmeasured (None)
    trials = [
        trial(judge={"plan_quality": 70, "verbosity_score": 60}),
    ]
    row = aggregate(trials)
    assert row["human_readability"] == 70
    assert row["agent_executability"] is None
    assert row["verbosity_score"] == 60


def test_plan_words_quality_floor():
    rendered = Report.render(RESULTS)
    # baseline human_readability 40 < 50: raw shown, no percent; others scored
    assert (
        "| plan_words | — (800 words) | 25% (1 600 words) "
        "| 100% (400 words) | 80% (500 words) |" in rendered
    )


def test_machine_words_reported_raw_only():
    rendered = Report.render(RESULTS)
    # two-audience-quality ADR: machine layer reported, never scored - no percent
    assert (
        "| machine_words | 0 words | 200 words | 0 words | 785 words |" in rendered
    )
    # and absent from non-plan tables, like plan_words
    debug_table = rendered.split("## debug-easy (home-grown)")[1].split("## ")[0]
    assert "machine_words" not in debug_table


def test_render_deterministic():
    one = Report.render(RESULTS)
    two = Report.render(RESULTS)
    assert one.encode("utf-8") == two.encode("utf-8")


def test_golden_plan_easy_table():
    expected = (DATA / "expected-plan-easy.md").read_text(encoding="utf-8")
    assert expected in Report.render(RESULTS)


def test_header_metadata_and_layout():
    rendered = Report.render(RESULTS)
    # metadata header: models, versions, n, date (from matrix.json - NFR3)
    for needle in (
        "claude-opus-4-6",  # subject model, read from the saved CLI JSON
        "claude-sonnet-5-5",  # judge
        "claude-haiku-4-5-20251001",  # simulator
        "2.1.285",
        "superpowers 6.4.2",
        "ni 1.7.0",
        "openspec 1.13.2",
        "2026-09-29",
        "terse=full",
        "OPENSPEC_TELEMETRY=0",
    ):
        assert needle in rendered, f"header missing: {needle}"
    # scenarios in FR2 order, origin-tagged headings
    assert rendered.index("## plan-easy (home-grown)") < rendered.index(
        "## debug-easy (home-grown)"
    )
    # non-plan scenario has no plan_words row in its table
    debug_table = rendered.split("## debug-easy (home-grown)")[1].split("## ")[0]
    assert "plan_words" not in debug_table
    # indeterminate footnote row counts per arm; absent arms stay em-dash
    assert "| indeterminate | 0/1 | — | — | 1/3 |" in debug_table
    # blinding residual-risk note (NFR4 disclosure)
    assert "residual" in rendered
    assert "PARTIAL" not in rendered


def test_main_writes_alternate_output_path(tmp_path):
    # explicit-flow track: a second CLI arg renders to that file so a side
    # report never touches the frozen default REPORT.md
    from harness.report import main

    out = tmp_path / "REPORT-explicit.md"
    assert main([str(RESULTS), str(out)]) == 0
    assert out.read_text(encoding="utf-8") == Report.render(RESULTS)


def test_partial_matrix_marked(tmp_path):
    results = tmp_path / "results"
    shutil.copytree(RESULTS, results)
    matrix = json.loads((results / "matrix.json").read_text(encoding="utf-8"))
    matrix["partial"] = True
    (results / "matrix.json").write_text(json.dumps(matrix), encoding="utf-8")
    assert "PARTIAL" in Report.render(results)
