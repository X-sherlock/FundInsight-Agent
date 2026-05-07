from pathlib import Path

from fundinsight.report_agent import ReportAgent, render_prompt
from fundinsight.data_loader import load_fund_metrics


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"
PROMPT_TEMPLATE = Path(__file__).resolve().parents[1] / "prompts" / "fund_report_prompt.md"


class FakeLLMClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return """# 示例稳健成长混合基金 基金指标分析报告

## 1. 报告说明
本报告基于历史结构化指标生成。

## 2. 基金基本信息
基金代码为 000001。

## 3. 核心指标概览
| 指标 | 数值 |
| --- | --- |
| 近一年收益 | 12.6% |

## 4. 收益表现分析
近一年收益指标 return_1y 为 0.126。

## 5. 风险与回撤分析
近一年最大回撤 max_drawdown_1y 为 -0.137。

## 6. 风险调整后表现
夏普比率 sharpe_1y 为 0.64。

## 7. 基准与同类对照
基准为沪深300指数。

## 8. 管理人与运作观察
管理人任职年限为 4.2 年。

## 9. 数据缺口与解读限制
缺少同类分位数据。

## 10. 非投资建议声明
本报告基于已提供的历史结构化指标生成，仅用于研究和信息整理，不构成任何买入、卖出、持有、择时或仓位配置建议，也不构成对未来收益的预测或保证。
"""


def test_render_prompt_injects_validated_json() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")

    prompt = render_prompt(template, fund_metrics)

    assert "{{fund_metrics_json}}" not in prompt
    assert '"code": "000001"' in prompt
    assert '"return_1y": 0.126' in prompt


def test_report_agent_generates_and_checks_report() -> None:
    llm_client = FakeLLMClient()
    agent = ReportAgent(llm_client=llm_client, prompt_template_path=PROMPT_TEMPLATE)

    result = agent.generate_report(SAMPLE_INPUT)

    assert result.guard_result.passed
    assert result.markdown.startswith("# 示例稳健成长混合基金")
    assert len(llm_client.prompts) == 1
    assert "fund_report_prompt" not in llm_client.prompts[0]
