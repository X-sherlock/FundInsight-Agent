import json
from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics
from fundinsight.report_planner import build_report_plan


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_build_report_plan_omits_empty_research_context() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)

    plan = build_report_plan(fund_metrics)

    assert plan.research_context is None
    assert "research_context" not in plan.to_prompt_payload()


def test_build_report_plan_injects_sanitized_research_context() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)
    research_context = {
        "positive_factors": [
            {
                "signal_id": "sig_1",
                "fund_code": "000001",
                "material_id": "mat_1",
                "signal_type": "positive_factor",
                "summary": "risk control improved",
                "evidence_text": "Evidence sentence from the material.",
                "confidence": 0.8,
                "source_type": "report",
                "raw_material_text": "FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT",
            }
        ],
        "risk_notices": [],
        "key_events": [],
        "view_changes": [],
        "source_materials": [
            {
                "material_id": "mat_1",
                "title": "Research report",
                "source_type": "report",
                "source_name": "Research Desk",
                "publish_date": "2026-05-01",
                "content_hash": "hash_should_not_enter_prompt",
                "raw_text": "FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT",
            }
        ],
        "limitations": ["limited materials"],
    }

    plan = build_report_plan(fund_metrics, research_context=research_context)
    payload = plan.to_prompt_payload()
    serialized = json.dumps(payload, ensure_ascii=False)

    assert payload["research_context"]["positive_factors"][0]["summary"] == "risk control improved"
    assert payload["research_context"]["source_materials"] == [
        {
            "material_id": "mat_1",
            "title": "Research report",
            "source_type": "report",
            "source_name": "Research Desk",
            "publish_date": "2026-05-01",
        }
    ]
    assert "FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT" not in serialized
    assert "content_hash" not in serialized


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
