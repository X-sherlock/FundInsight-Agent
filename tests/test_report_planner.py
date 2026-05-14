import json
from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics
from fundinsight.report_planner import build_report_plan
from fundinsight.research_models import RetrievedResearchChunk


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
                "source_url": "https://example.com/research-report",
                "publish_date": "2026-05-01",
                "content_hash": "hash_should_not_enter_prompt",
                "raw_text": "FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT",
            }
        ],
        "analyzed_materials": [
            {
                "material_id": "mat_1",
                "title": "Research report",
                "source_type": "report",
                "source_name": "Research Desk",
                "source_url": "https://example.com/research-report",
                "publish_date": "2026-05-01",
                "chunk_count": 2,
                "signal_count": 1,
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
            "source_url": "https://example.com/research-report",
            "publish_date": "2026-05-01",
        }
    ]
    assert payload["research_context"]["analyzed_materials"] == [
        {
            "material_id": "mat_1",
            "title": "Research report",
            "source_type": "report",
            "source_name": "Research Desk",
            "source_url": "https://example.com/research-report",
            "publish_date": "2026-05-01",
            "chunk_count": 2,
            "signal_count": 1,
        }
    ]
    assert "FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT" not in serialized
    assert "content_hash" not in serialized


def test_build_report_plan_injects_fact_card_with_retrieved_chunks() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)
    chunk = RetrievedResearchChunk(
        chunk_id="mat_1_0000",
        material_id="mat_1",
        fund_code="000001",
        chunk_index=0,
        evidence_text="The material mentions fund 000001 drawdown and return context.",
        relevance_score=0.82,
        source_type="news",
        title="Research news",
        source_name="Example News",
        source_url="https://example.com/news",
        publish_date="2026-05-01",
    )

    plan = build_report_plan(fund_metrics, retrieved_chunks=[chunk])
    payload = plan.to_prompt_payload()

    assert "fact_card" in payload
    assert payload["fact_card"]["fund_code"] == "000001"
    assert payload["fact_card"]["retrieved_chunks"][0]["chunk_id"] == "mat_1_0000"
    assert payload["fact_card"]["source_materials"][0]["source_url"] == "https://example.com/news"
    assert "research_context" not in payload


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
