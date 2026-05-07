from fundinsight.report_guard import check_report


def _valid_report() -> str:
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


def test_check_report_passes_complete_neutral_report() -> None:
    result = check_report(_valid_report())

    assert result.passed


def test_check_report_flags_empty_report() -> None:
    result = check_report("   ")

    assert not result.passed
    assert result.issues[0].code == "empty_report"


def test_check_report_flags_missing_sections() -> None:
    result = check_report("# only a title")

    assert not result.passed
    assert any(issue.code == "missing_section" for issue in result.issues)


def test_check_report_flags_prohibited_recommendations() -> None:
    report = _valid_report() + "\n因此建议买入该基金。"

    result = check_report(report)

    assert not result.passed
    assert any(issue.code == "prohibited_expression" for issue in result.issues)


def test_check_report_allows_historical_holding_percentages() -> None:
    report = _valid_report() + "\n从持仓指标看，股票配置比例为 72%，现金比例为 8%。"

    result = check_report(report)

    assert result.passed
