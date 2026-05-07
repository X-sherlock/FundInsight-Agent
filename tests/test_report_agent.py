import json
from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.report_agent import ReportAgent, render_prompt
from fundinsight.report_planner import build_report_plan
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


class FakeLLMClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return (
            "<report_markdown>\n"
            + valid_v02_report()
            + "\n</report_markdown>\n"
            + "<chart_specs_json>\n"
            + json.dumps(_chart_specs_payload(), ensure_ascii=False)
            + "\n</chart_specs_json>"
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
    llm_client = FakeLLMClient()
    agent = ReportAgent(llm_client=llm_client, prompt_template_path=PROMPT_TEMPLATE)

    result = agent.generate_report(SAMPLE_INPUT)

    assert result.guard_result.passed
    assert result.markdown.startswith("# 示例稳健成长混合基金")
    assert len(result.chart_specs) == 6
    assert result.chart_specs[0].id == "returns_by_period"
    assert len(llm_client.prompts) == 1
    assert "report_context_json" not in llm_client.prompts[0]
