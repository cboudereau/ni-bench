"""REPORT.md generator (FR6, FR7, NFR3, kpi-scoring ADR).

``score_kpi``, ``aggregate``, and ``Report.render`` are pure functions of the
saved ``result.json`` files plus ``matrix.json`` - never the wall clock, so a
re-render on unchanged results is byte-identical (NFR3). Formulas come from
the kpi-scoring ADR verbatim: resource KPIs score ``min(arms)/value x 100``
(lower better, value 0 scores 100), judge KPIs are raw 0-100, outcome is the
pass-rate over determinate trials.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from harness.arms import ARMS
from harness.judge import JUDGE_MODEL, JUDGE_QUALITY_FLOOR
from harness.scenarios import PORTED_SCENARIOS, REPO_ROOT, SCENARIOS
from harness.simulator import SIMULATOR_MODEL

# Pins recorded at image build time (arms/Dockerfile.* and their build logs).
CLI_VERSION = "2.1.285"
PLUGIN_VERSIONS = (("superpowers", "6.4.2"), ("ni", "1.5.0"), ("openspec", "1.13.2"))

RESOURCE_KPIS = ("tokens_total", "cost_usd", "duration_s", "turns", "user_turns", "plan_words")
JUDGE_KPIS = ("plan_quality", "verbosity_score")

EM_DASH = "—"


def score_kpi(values: dict[str, float | None]) -> dict[str, float | None]:
    """Resource KPI percent: ``min(arms)/value x 100``, lower better.

    A value of 0 scores 100 (guards the division); with min = 0 every other
    arm scores 0. Arms without data (None) stay None and are excluded from
    the min.
    """
    present = [v for v in values.values() if v is not None]
    if not present:
        return dict(values)
    minimum = min(present)
    scores: dict[str, float | None] = {}
    for arm, value in values.items():
        if value is None:
            scores[arm] = None
        elif value == 0:
            scores[arm] = 100.0
        else:
            scores[arm] = minimum / value * 100.0
    return scores


def _tokens_total(result: dict) -> float:
    """Subject tokens: every usage counter, cache reads included (kpi-scoring ADR)."""
    usage = result.get("cli_json", {}).get("usage", {})
    return sum(v for v in usage.values() if isinstance(v, int | float))


def _raw_resource(result: dict, kpi: str) -> float:
    cli = result.get("cli_json", {})
    if kpi == "tokens_total":
        return _tokens_total(result)
    if kpi == "cost_usd":
        return cli.get("total_cost_usd", 0.0)
    if kpi == "duration_s":
        return cli.get("duration_ms", 0) / 1000
    if kpi == "turns":
        return cli.get("num_turns", 0)
    if kpi == "user_turns":
        return result.get("user_turns", 0)
    if kpi == "plan_words":
        return result.get("artifact_metrics", {}).get("plan_words", 0)
    raise KeyError(kpi)


def aggregate(trials: list[dict]) -> dict:
    """One (scenario, arm) cell over n trials (FR7, kpi-scoring ADR).

    Median for raw resource and judge KPIs, pass-rate ingredients for outcome.
    Indeterminate trials are excluded from every median and from the pass-rate
    denominator; they are counted for the footnote row.
    """
    determinate = [t for t in trials if t.get("verdict") != "indeterminate"]
    row: dict = {}
    for kpi in RESOURCE_KPIS:
        values = [_raw_resource(t, kpi) for t in determinate]
        row[kpi] = statistics.median(values) if values else None
    for kpi in JUDGE_KPIS:
        values = [
            t["judge"][kpi]
            for t in determinate
            if isinstance(t.get("judge"), dict)
            and not t["judge"].get("indeterminate")
            and kpi in t["judge"]
        ]
        row[kpi] = statistics.median(values) if values else None
    row["outcome_pass"] = sum(1 for t in determinate if t.get("verdict") == "pass")
    row["determinate"] = len(determinate)
    row["indeterminate"] = len(trials) - len(determinate)
    row["trials"] = len(trials)
    return row


def _group(n: int) -> str:
    """Fixed thousands separator: plain space (byte-stable, FR6 example style)."""
    return f"{n:,}".replace(",", " ")


def _num(x: float) -> str:
    if float(x).is_integer():
        return _group(int(x))
    return f"{x:,.1f}".replace(",", " ")


def _pct(x: float) -> str:
    return f"{round(x)}%"


def _fmt_raw(kpi: str, x: float) -> str:
    if kpi == "cost_usd":
        return f"${x:.4f}"
    if kpi == "duration_s":
        return f"{x:,.1f}".replace(",", " ") + " s"
    if kpi == "tokens_total":
        return f"{_num(x)} tok"
    if kpi == "plan_words":
        return f"{_num(x)} words"
    return _num(x)


def _load(results_dir: Path) -> dict[str, dict[str, list[dict]]]:
    """results/<scenario>/<arm>/<trial>/result.json, in stable sorted order."""
    grouped: dict[str, dict[str, list[dict]]] = {}
    for path in sorted(results_dir.glob("*/*/*/result.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        scenario = data.get("scenario") or path.parts[-4]
        arm = data.get("arm") or path.parts[-3]
        grouped.setdefault(scenario, {}).setdefault(arm, []).append(data)
    return grouped


def _subject_model(results_dir: Path) -> str:
    """Subject model from the saved CLI JSONs (first turn file, sorted order)."""
    for path in sorted(results_dir.glob("*/*/*/turns/turn-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        usage = data.get("modelUsage")
        if isinstance(usage, dict) and usage:
            return ", ".join(sorted(usage))
        model = data.get("model")
        if isinstance(model, str) and model:
            return model
    return "unknown"


def _plan_words_cells(rows_agg: dict[str, dict | None], arm_names: list[str]) -> list[str]:
    """Quality floor (kpi-scoring ADR): scored only where plan_quality >= floor."""
    qualified = {
        arm
        for arm in arm_names
        if rows_agg[arm]
        and rows_agg[arm]["plan_quality"] is not None
        and rows_agg[arm]["plan_quality"] >= JUDGE_QUALITY_FLOOR
        and rows_agg[arm]["plan_words"] is not None
    }
    scores = score_kpi(
        {arm: (rows_agg[arm]["plan_words"] if arm in qualified else None) for arm in arm_names}
    )
    cells = []
    for arm in arm_names:
        agg = rows_agg[arm]
        raw = agg["plan_words"] if agg else None
        if raw is None:
            cells.append(EM_DASH)
        elif arm in qualified:
            cells.append(f"{_pct(scores[arm])} ({_fmt_raw('plan_words', raw)})")
        else:
            cells.append(f"{EM_DASH} ({_fmt_raw('plan_words', raw)})")
    return cells


class Report:
    """Renders REPORT.md from a results directory (FR6)."""

    @staticmethod
    def render(results_dir: Path | str) -> str:
        results_dir = Path(results_dir)
        grouped = _load(results_dir)
        matrix_path = results_dir / "matrix.json"
        matrix: dict = {}
        if matrix_path.is_file():
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

        arm_names = [a.name for a in ARMS]
        lines = ["# ni-bench REPORT", ""]
        if matrix.get("partial"):
            lines += [
                "> **PARTIAL RUN** - the cost guard stopped the matrix (NFR2); "
                "tables cover completed trials only.",
                "",
            ]

        verbosity = "; ".join(
            a.name
            + ": "
            + (", ".join(f"{k}={v}" for k, v in sorted(a.verbosity.items())) or "default")
            for a in ARMS
        )
        plugins = ", ".join(f"{name} {version}" for name, version in PLUGIN_VERSIONS)
        lines += [
            "## Run metadata",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Subject model | {_subject_model(results_dir)} |",
            f"| Judge model | {JUDGE_MODEL} |",
            f"| Simulator model | {SIMULATOR_MODEL} |",
            f"| claude-code | {CLI_VERSION} |",
            f"| Plugins | {plugins} |",
            f"| n (trials per arm x scenario) | {matrix.get('n', 'unknown')} |",
            f"| Verbosity config | {verbosity} |",
            f"| Date | {matrix.get('date', 'unknown')} |",
            "",
            "Resource percents are relative to this arm set (kpi-scoring ADR): "
            "the best arm scores 100%; lower raw is better.",
            "",
        ]

        for scenario in SCENARIOS:  # FR2 table order
            if scenario.id not in grouped:
                continue
            arms_data = grouped[scenario.id]
            rows_agg: dict[str, dict | None] = {
                arm: aggregate(arms_data[arm]) if arm in arms_data else None
                for arm in arm_names
            }
            origin = "superpowers-evals" if scenario.id in PORTED_SCENARIOS else "home-grown"
            lines += [
                f"## {scenario.id} ({origin})",
                "",
                "| KPI | " + " | ".join(arm_names) + " |",
                "|---|" + "---|" * len(arm_names),
            ]
            kpis = [
                k for k in RESOURCE_KPIS if k != "plan_words" or scenario.family == "plan"
            ]
            for kpi in kpis:
                if kpi == "plan_words":
                    cells = _plan_words_cells(rows_agg, arm_names)
                else:
                    values = {
                        arm: (rows_agg[arm][kpi] if rows_agg[arm] else None)
                        for arm in arm_names
                    }
                    scores = score_kpi(values)
                    cells = [
                        EM_DASH
                        if scores[arm] is None
                        else f"{_pct(scores[arm])} ({_fmt_raw(kpi, values[arm])})"
                        for arm in arm_names
                    ]
                lines.append(f"| {kpi} | " + " | ".join(cells) + " |")
            for kpi in JUDGE_KPIS:
                cells = []
                for arm in arm_names:
                    agg = rows_agg[arm]
                    value = agg[kpi] if agg else None
                    cells.append(EM_DASH if value is None else f"{_pct(value)} ({_num(value)})")
                lines.append(f"| {kpi} | " + " | ".join(cells) + " |")
            cells = []
            for arm in arm_names:
                agg = rows_agg[arm]
                if not agg or agg["determinate"] == 0:
                    cells.append(EM_DASH)
                else:
                    rate = agg["outcome_pass"] / agg["determinate"] * 100
                    cells.append(f"{_pct(rate)} ({agg['outcome_pass']}/{agg['determinate']})")
            lines.append("| outcome | " + " | ".join(cells) + " |")
            cells = [
                EM_DASH
                if not rows_agg[arm]
                else f"{rows_agg[arm]['indeterminate']}/{rows_agg[arm]['trials']}"
                for arm in arm_names
            ]
            lines.append("| indeterminate | " + " | ".join(cells) + " |")
            lines.append("")

        lines += [
            "## Notes",
            "",
            f"- `plan_words` is scored only among arms whose `plan_quality` is at least "
            f"{JUDGE_QUALITY_FLOOR} (quality floor, kpi-scoring ADR); arms below the floor "
            f"show the raw value only.",
            "- Indeterminate trials are excluded from medians and pass-rates; the "
            "`indeterminate` row counts them per arm (FR7).",
            "- Blinding residual risk (NFR4): arm identifiers are redacted from judge "
            "input, but artifact structure (directory layout, plan format) can still "
            "leak arm identity despite blinding.",
            "",
        ]
        return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """``python -m harness.report [results_dir] [output_md]`` (scripts/report.sh).

    The optional second arg renders a side report (explicit-flow track)
    without touching the default REPORT.md.
    """
    args = sys.argv[1:] if argv is None else list(argv)
    results_dir = Path(args[0]) if args else REPO_ROOT / ".reports"
    out = Path(args[1]) if len(args) > 1 else REPO_ROOT / "REPORT.md"
    out.write_text(Report.render(results_dir), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
