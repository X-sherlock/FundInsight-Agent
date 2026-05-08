import json
from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.models import ChartSeries, ChartSpec, ReportPlan
from fundinsight.report_agent import ReportResult
from fundinsight.report_guard import GuardResult
from fundinsight.report_store import ReportStore


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_report_store_saves_and_loads_frontend_record(tmp_path: Path) -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)
    store = ReportStore(tmp_path / "reports")

    report_id = store.save_generated_report(_report_result(metrics), metrics.model_dump(mode="json"))
    record = store.load_report_record(report_id)

    assert store.report_exists("000001")
    assert (tmp_path / "reports" / "funds" / "000001" / "report.md").exists()
    assert (tmp_path / "reports" / "funds" / "000001" / "chart_specs.json").exists()
    assert record["report_id"] == "000001"
    assert record["fund"]["code"] == "000001"
    assert record["guard_result"]["passed"] is True
    assert record["chart_specs"]["charts"][0]["id"] == "returns_by_period"
    assert record["key_metrics"][0]["helper"] == "metrics.performance.return_1y"
    assert record["core_conclusions"][0].startswith("**基于 return_1y 指标**")


def _report_result(metrics):
    return ReportResult(
        fund_metrics=metrics,
        report_plan=ReportPlan(
            source_metrics={},
            derived_metrics={},
            metric_tables={},
            chart_specs=[],
            analysis_focus=[],
            missing_fields=[],
            data_notes=[],
        ),
        prompt="",
        markdown=(
            "# report\n\n"
            "## 1. 报告说明\ncontent\n\n"
            "## 2. 核心结论\n1. **基于 return_1y 指标**观察历史收益。\n\n"
            "## 3. 基金基本信息\ncontent"
        ),
        chart_specs=[
            ChartSpec(
                id="returns_by_period",
                title="多周期收益表现",
                type="bar",
                description="展示收益。",
                source_fields=["metrics.performance.return_1y"],
                series=[ChartSeries(name="基金收益", values=[{"period": "1Y", "value": 0.126}])],
                x_axis="观察周期",
                y_axis="收益率",
                value_unit="decimal_percent",
            )
        ],
        guard_result=GuardResult(tuple()),
    )
