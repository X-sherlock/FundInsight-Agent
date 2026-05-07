from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics
from fundinsight.report_planner import build_report_plan


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_build_report_plan_creates_derived_metrics_tables_and_charts() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)

    plan = build_report_plan(fund_metrics)

    assert plan.derived_metrics["computed_excess_return_1y"] == pytest.approx(0.035)
    assert plan.derived_metrics["reported_excess_return_1y"] == 0.035
    assert len(plan.metric_tables["return_periods"]) >= 5
    assert len(plan.chart_specs) >= 5
    assert plan.chart_specs[0].encoding.x == "period"
    assert plan.chart_specs[0].encoding.y == "value"
    assert plan.chart_specs[0].value_unit == "decimal_percent"
    assert "quarterly_holding_details" in plan.missing_fields
    assert any("不形成评级" in focus for focus in plan.analysis_focus)
