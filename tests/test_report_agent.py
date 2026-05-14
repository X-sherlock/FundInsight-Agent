import json
import re
from datetime import date
from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.report_agent import ReportAgent, render_prompt
from fundinsight.report_planner import build_report_plan
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore
from tests.test_report_guard import valid_v02_report


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"
PROMPT_TEMPLATE = Path(__file__).resolve().parents[1] / "prompts" / "fund_report_prompt.md"


def _chart_specs_payload() -> dict:
    return {
        "charts": [
            {
                "id": "returns_by_period",
                "title": "多周期收益表现",
                "type": "bar",
                "description": "展示基金多周期收益。",
                "source_fields": ["metrics.performance.return_1y"],
                "series": [{"name": "基金收益", "values": [{"period": "1Y", "value": 0.126}]}],
                "encoding": {"x": "period", "y": "value"},
                "x_axis": "观察周期",
                "y_axis": "收益率",
                "value_unit": "decimal_percent",
                "notes": ["样例图表"],
            },
            {
                "id": "benchmark_excess_return_1y",
                "title": "近1年基金、基准与超额收益",
                "type": "bar",
                "description": "展示基金收益、基准收益、超额收益。",
                "source_fields": ["metrics.performance.return_1y"],
                "series": [{"name": "近1年", "values": [{"metric": "超额收益", "value": 0.035}]}],
                "encoding": {"x": "metric", "y": "value"},
                "x_axis": "指标",
                "y_axis": "收益率",
                "value_unit": "decimal_percent",
                "notes": ["样例图表"],
            },
            {
                "id": "risk_drawdown_profile",
                "title": "波动与回撤风险画像",
                "type": "bar",
                "description": "展示风险指标。",
                "source_fields": ["metrics.risk.volatility_1y"],
                "series": [{"name": "风险", "values": [{"metric": "波动率", "value": 0.182}]}],
                "encoding": {"x": "metric", "y": "value"},
                "x_axis": "风险指标",
                "y_axis": "指标值",
                "value_unit": "decimal_percent",
                "notes": ["样例图表"],
            },
            {
                "id": "risk_adjusted_metrics",
                "title": "风险调整后表现",
                "type": "bar",
                "description": "展示风险调整指标。",
                "source_fields": ["metrics.risk_adjusted.sharpe_1y"],
                "series": [{"name": "风险调整", "values": [{"metric": "夏普", "value": 0.64}]}],
                "encoding": {"x": "metric", "y": "value"},
                "x_axis": "风险调整指标",
                "y_axis": "指标值",
                "value_unit": "number",
                "notes": ["样例图表"],
            },
            {
                "id": "asset_allocation_profile",
                "title": "资产配置结构",
                "type": "pie",
                "description": "展示资产配置。",
                "source_fields": ["metrics.holding.stock_position"],
                "series": [{"name": "资产", "values": [{"asset": "股票", "value": 0.72}]}],
                "encoding": {"category": "asset", "value": "value"},
                "x_axis": "资产类别",
                "y_axis": "占比",
                "value_unit": "decimal_percent",
                "notes": ["样例图表"],
            },
            {
                "id": "peer_context",
                "title": "同类相对位置",
                "type": "bar",
                "description": "展示同类分位。",
                "source_fields": ["peer_summary.peer_rank_percentile"],
                "series": [{"name": "同类", "values": [{"metric": "同类分位", "value": 0.32}]}],
                "encoding": {"x": "metric", "y": "value"},
                "x_axis": "同类指标",
                "y_axis": "指标值",
                "value_unit": "mixed",
                "notes": ["样例图表"],
            },
        ]
    }


class StubLLMClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "基金相关材料结构化解读助手" in prompt:
            chunk_id_match = re.search(r'"chunk_id":\s*"([^"]+)"', prompt)
            chunk_id = chunk_id_match.group(1) if chunk_id_match else "mat_stub_0000"
            return json.dumps(
                {
                    "interpretations": [
                        {
                            "chunk_id": chunk_id,
                            "analysis_title": "材料事实解读",
                            "material_summary": "材料提到基金收益、回撤和基金经理相关背景。",
                            "sentiment_label": "中性",
                            "evidence_excerpt": "EVIDENCE_RESEARCH",
                        }
                    ]
                },
                ensure_ascii=False,
            )
        return (
            "<report_markdown>\n"
            + valid_v02_report()
            + "\n</report_markdown>\n"
            + "<chart_specs_json>\n"
            + json.dumps(_chart_specs_payload(), ensure_ascii=False)
            + "\n</chart_specs_json>"
        )


class StubResearchLLMClient:
    def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "signals": [
                    {
                        "signal_type": "positive_factor",
                        "summary": "research signal",
                        "detail": "detail",
                        "category": "operations",
                        "signal_date": "2026-05-01",
                        "impact_direction": "positive",
                        "importance": "high",
                        "confidence": 0.9,
                        "evidence_text": "EVIDENCE_RESEARCH",
                    }
                ]
            },
            ensure_ascii=False,
        )


def test_render_prompt_injects_report_context_json() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)
    report_plan = build_report_plan(fund_metrics)
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")

    prompt = render_prompt(template, report_plan)

    assert "{{report_context_json}}" not in prompt
    assert '"code": "000001"' in prompt
    assert '"analysis_focus"' in prompt
    assert '"chart_specs"' in prompt


def test_report_agent_generates_parses_and_checks_report() -> None:
    llm_client = StubLLMClient()
    agent = ReportAgent(llm_client=llm_client, prompt_template_path=PROMPT_TEMPLATE)

    result = agent.generate_report(SAMPLE_INPUT)

    assert result.guard_result.passed
    assert result.markdown.startswith("# 示例稳健成长混合基金")
    assert len(result.chart_specs) == 6
    assert result.chart_specs[0].id == "returns_by_period"
    assert len(llm_client.prompts) == 1
    assert "report_context_json" not in llm_client.prompts[0]


def test_report_agent_includes_research_context_when_requested(tmp_path: Path) -> None:
    report_llm = StubLLMClient()
    research_store = ResearchStore(tmp_path / "data")
    service = ResearchMaterialService(research_store)
    service.import_text_material(
        fund_code="000001",
        title="research material",
        source_type="report",
        source_name="Research Desk",
        publish_date=date(2026, 5, 1),
        content="EVIDENCE_RESEARCH appears here. Fund 000001 return, drawdown and manager context are discussed.",
    )
    agent = ReportAgent(
        llm_client=report_llm,
        prompt_template_path=PROMPT_TEMPLATE,
        research_store=research_store,
        research_material_service=service,
    )

    result = agent.generate_report(SAMPLE_INPUT, include_research=True, force_reextract=True)

    assert result.fact_card is not None
    assert result.fact_card["retrieved_chunks"][0]["chunk_id"].startswith("mat_")
    assert result.fact_card["retrieved_chunks"][0]["analysis_title"] == "材料事实解读"
    assert result.fact_card["retrieved_chunks"][0]["sentiment_label"] == "中性"
    assert '"fact_card"' in report_llm.prompts[-1]
    assert "EVIDENCE_RESEARCH" in report_llm.prompts[-1]


def test_report_agent_degrades_when_research_processing_fails(tmp_path: Path, monkeypatch) -> None:
    def fail_processing(*args, **kwargs):
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr("fundinsight.report_agent.ResearchIngestionService.import_text_material", fail_processing)
    report_llm = StubLLMClient()
    research_store = ResearchStore(tmp_path / "data")
    ResearchMaterialService(research_store).import_text_material(
        fund_code="000001",
        title="research material",
        source_type="report",
        publish_date=date(2026, 5, 1),
        content="EVIDENCE_RESEARCH appears here.",
    )
    agent = ReportAgent(
        llm_client=report_llm,
        prompt_template_path=PROMPT_TEMPLATE,
        research_store=research_store,
    )

    result = agent.generate_report(SAMPLE_INPUT, include_research=True)

    assert result.guard_result.passed
    assert result.research_processing_error
    assert "pipeline failed" in result.research_processing_error
    assert result.research_context is None
    assert "pipeline failed" not in report_llm.prompts[0]


def test_report_agent_auto_includes_research_only_when_materials_exist(tmp_path: Path) -> None:
    report_llm = StubLLMClient()
    research_store = ResearchStore(tmp_path / "data")
    service = ResearchMaterialService(research_store)
    service.import_text_material(
        fund_code="000001",
        title="research material",
        source_type="report",
        source_name="Research Desk",
        publish_date=date(2026, 5, 1),
        content="EVIDENCE_RESEARCH appears here.",
    )
    agent = ReportAgent(
        llm_client=report_llm,
        prompt_template_path=PROMPT_TEMPLATE,
        research_store=research_store,
        research_material_service=service,
    )

    result = agent.generate_report(SAMPLE_INPUT, force_reextract=True)

    assert result.research_mode == "auto"
    assert result.research_materials_found is True
    assert result.research_material_count == 1
    assert result.research_used is True
    assert '"fact_card"' in report_llm.prompts[-1]


def test_report_agent_auto_skips_research_without_materials(tmp_path: Path) -> None:
    report_llm = StubLLMClient()
    agent = ReportAgent(
        llm_client=report_llm,
        prompt_template_path=PROMPT_TEMPLATE,
        research_store=ResearchStore(tmp_path / "data"),
    )

    result = agent.generate_report(SAMPLE_INPUT)

    assert result.research_mode == "auto"
    assert result.research_materials_found is False
    assert result.research_material_count == 0
    assert result.research_used is False
    assert '"research_context"' not in report_llm.prompts[0]


def test_prompt_contains_research_context_rules() -> None:
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")

    assert "research_context 使用规则" in template
    assert "fact_card / RAG 使用规则" in template
    assert "相关材料解读" in template
    assert "不要在 Markdown 正文中新增 `## 14. 相关材料解读`" in template
    assert "`## 14. 数据局限性`、`## 15. 风险提示`" in template
    assert "不能让非结构化材料覆盖" in template
    assert "不得编造任何投研材料" in template
