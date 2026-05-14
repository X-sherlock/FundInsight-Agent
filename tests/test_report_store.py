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


def test_report_store_enriches_fact_card_chunks_from_related_material_section(tmp_path: Path) -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)
    store = ReportStore(tmp_path / "reports")
    fact_card = {
        "fund_code": "000001",
        "source_metrics": {},
        "derived_metrics": {},
        "metric_tables": {},
        "missing_fields": [],
        "data_notes": [],
        "retrieved_chunks": [
            {
                "chunk_id": "mat_1_parent_0001",
                "material_id": "mat_1",
                "fund_code": "000001",
                "chunk_index": 0,
                "evidence_text": "完整证据原文",
                "relevance_score": 0.5,
                "source_type": "report",
                "title": "年度报告.pdf",
            }
        ],
        "source_materials": [],
        "limitations": [],
    }
    markdown = (
        "# report\n\n"
        "## 1. 报告说明\ncontent\n\n"
        "## 2. 核心结论\n1. **基于 return_1y 指标**观察历史收益。\n\n"
        "## 14. 相关材料解读\n\n"
        "**解读1：历史超额收益表现**\n"
        "- **材料摘要**：年度报告披露基金过去一年收益与基准对比。\n"
        "- **情绪标签**：正面\n"
        "- **证据原文摘录**：“过去一年 13.07% 3.47% 9.60%”\n"
        "- **详细来源**：标题《年度报告.pdf》，来源类型：report，chunk_id：mat_1_parent_0001\n\n"
        "## 15. 数据局限性\ncontent"
    )

    report_id = store.save_generated_report(
        _report_result(metrics, markdown=markdown, fact_card=fact_card),
        metrics.model_dump(mode="json"),
    )

    record = store.load_report_record(report_id)
    chunk = record["fact_card"]["retrieved_chunks"][0]
    assert chunk["analysis_title"] == "历史超额收益表现"
    assert chunk["material_summary"] == "年度报告披露基金过去一年收益与基准对比。"
    assert chunk["sentiment_label"] == "正面"
    assert chunk["evidence_excerpt"] == "“过去一年 13.07% 3.47% 9.60%”"
    assert chunk["evidence_text"] == "完整证据原文"


def _report_result(metrics, markdown: str | None = None, fact_card: dict | None = None):
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
        markdown=markdown
        or (
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
        fact_card=fact_card,
    )
