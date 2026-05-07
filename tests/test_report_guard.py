from fundinsight.models import ChartSeries, ChartSpec
from fundinsight.report_guard import check_chart_specs, check_report


def valid_v02_report() -> str:
    return """# 示例稳健成长混合基金 客户级基金深度分析报告

## 1. 报告说明
本报告基于截至 2026-03-31 的结构化历史指标生成，仅用于研究和信息整理。样例数据源为 synthetic_sample，百分比指标以小数形式提供并在报告中转换为百分比展示。

## 2. 核心结论
- 结论1：数据上，基金近1年基金收益为 12.6%；比较上，基准收益为 9.1%，超额收益为 3.5%；解释上，观察期内存在正向基准相对表现；含义上，基准比较是后续跟踪重点；限制上，该结论只覆盖近1年历史窗口。
- 结论2：数据上，近1年波动率为 18.2%，最大回撤为 -13.7%；比较上，同类平均波动率为 19.6%；解释上，历史波动略低于同类均值；含义上，可结合回撤修复观察风险控制；限制上，缺少日度净值序列。
- 结论3：数据上，夏普比率为 0.64，信息比率为 0.46；比较上，需要结合超额收益和跟踪误差；解释上，收益质量并非只由绝对收益决定；含义上，应同时观察收益和风险；限制上，缺少完整风险因子拆解。
- 结论4：数据上，peer_rank_percentile 为 32.0%；比较上，样例口径表示数值越低排名位置越靠前；解释上，基金在同类中有可观察的历史相对位置；含义上，可辅助同类竞争力研究；限制上，缺少完整同类分布。
- 结论5：数据上，股票仓位为 72.0%，前十大持仓占比为 43.0%；比较上，资产结构与混合型定位相关；解释上，权益暴露会影响波动和回撤；含义上，应结合持仓变化监测风格；限制上，缺少季度持仓明细。

## 3. 基金基本信息
| 项目 | 内容 |
| --- | --- |
| 基金代码 | 000001 |
| 基金名称 | 示例稳健成长混合基金 |
| 基准 | 沪深300指数 |
| 同类 | 主动混合型基金 |

## 4. 关键指标总览
| 指标 | 数值 | 说明 |
| --- | --- | --- |
| 近1年基金收益 | 12.6% | 历史收益窗口 |
| 近1年基准收益 | 9.1% | 基准收益 |
| 近1年超额收益 | 3.5% | 基金收益减基准收益 |
| 最大回撤 | -13.7% | 近1年最大回撤 |
| 波动率 | 18.2% | 近1年波动率 |
| 夏普比率 | 0.64 | 风险调整后表现 |

## 5. 收益分析
| 周期 | 基金收益 | 基准收益 | 超额收益 |
| --- | --- | --- | --- |
| 近1年 | 12.6% | 9.1% | 3.5% |
收益分析显示，基金收益、基准收益与超额收益之间存在明确对照关系。该观察可说明近1年历史相对表现，但不能外推为未来表现。

## 6. 收益质量分析
收益质量需要结合多周期收益、超额收益、夏普比率和回撤表现。近1年收益为 12.6%，夏普比率为 0.64，说明收益观察不能脱离风险指标单独解释。

## 7. 风险控制分析
风险控制分析包含最大回撤、波动率、夏普比率、下行波动率和回撤修复天数。近1年最大回撤为 -13.7%，波动率为 18.2%，夏普比率为 0.64，表明历史收益伴随可观察的净值波动和回撤压力。

## 8. 同类竞争力分析
peer_rank_percentile 为 32.0%，同类分位按样例说明为数值越低排名位置越靠前。该数据可用于同类竞争力观察，但缺少完整同类分布和分位计算口径，因此只能作为有限参考。

## 9. 基准比较分析
基金近1年收益为 12.6%，基准收益为 9.1%，超额收益为 3.5%。结合 beta_1y 为 0.92、tracking_error_1y 为 7.6%，基准比较需要同时观察相对收益和主动偏离。

## 10. 图表解读
<!-- chart: returns_by_period -->
图表解读：该图用于展示多周期基金收益，帮助比较短中长期历史收益窗口的差异，并提示不同窗口不可直接代表未来。

<!-- chart: benchmark_excess_return_1y -->
图表解读：该图并列展示基金收益、基准收益、超额收益，支撑收益分析中的 Data 与 Comparison。

<!-- chart: risk_drawdown_profile -->
图表解读：该图展示最大回撤和波动率，有助于解释收益背后的历史风险代价。

<!-- chart: risk_adjusted_metrics -->
图表解读：该图展示夏普比率、信息比率和 Calmar 比率，辅助观察收益质量而不是形成评分。

<!-- chart: asset_allocation_profile -->
图表解读：该图展示资产配置结构，用于解释权益暴露、债券仓位和现金比例对风险特征的影响。

<!-- chart: peer_context -->
图表解读：该图展示同类分位和同类均值参照，用于观察同类竞争力分析中的比较依据和数据限制。

## 11. 主要优势
- 近1年相对基准有正向超额收益记录。
- 同类分位提供了可观察的同类比较线索。
- 风险调整指标为收益质量分析提供补充。

## 12. 主要风险
- 最大回撤显示观察期内存在净值回撤压力。
- 缺少日度净值序列限制了波动和回撤路径分析。
- 同类分析依赖样例口径，真实业务需要确认数据供应商定义。

## 13. 适合关注的场景
- 适合关注的场景包括研究历史收益与基准差异、观察风险控制特征、跟踪同类分位变化。该部分仅描述研究场景，不构成任何交易动作或配置动作。

## 14. 数据局限性
- 缺少 quarterly_holding_details，无法展开持仓变化路径。
- 缺少 daily_nav_series，无法核验回撤发生过程。
- 缺少 full_peer_distribution，同类竞争力分析受到限制。

## 15. 风险提示
本报告基于已提供的历史结构化指标生成，仅用于研究和信息整理，不构成任何买入、卖出、持有、择时或仓位配置建议，也不构成对未来收益的预测、承诺或保证。
"""


def test_check_report_passes_complete_neutral_report() -> None:
    result = check_report(valid_v02_report())

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
    report = valid_v02_report() + "\n因此建议买入该基金。"

    result = check_report(report)

    assert not result.passed
    assert any(issue.code == "prohibited_expression" for issue in result.issues)


def test_check_report_allows_historical_holding_percentages() -> None:
    report = valid_v02_report() + "\n从持仓指标看，股票配置比例为 72%，现金配置比例为 8%。"

    result = check_report(report)

    assert result.passed


def test_check_report_flags_non_negated_prediction_text() -> None:
    report = valid_v02_report() + "\n预计收益可能改善。"

    result = check_report(report)

    assert not result.passed
    assert any(issue.code == "prohibited_expression" for issue in result.issues)
    assert "context:" in result.issues[-1].message


def test_check_report_flags_missing_chart_placeholders() -> None:
    report = valid_v02_report().replace("<!-- chart:", "<!-- removed:")

    result = check_report(report)

    assert not result.passed
    assert any(issue.code == "too_few_chart_placeholders" for issue in result.issues)


def test_check_report_counts_aligned_markdown_tables() -> None:
    report = valid_v02_report().replace("| --- | --- |", "| :--- | ---: |")

    result = check_report(report)

    assert result.passed


def test_check_report_accepts_metric_synonyms() -> None:
    report = (
        valid_v02_report()
        .replace("基金收益", "本基金回报")
        .replace("基准收益", "业绩比较基准")
        .replace("超额收益", "超额回报")
    )

    result = check_report(report)

    assert result.passed


def test_check_report_accepts_chart_explanation_without_literal_interpretation_word() -> None:
    report = (
        valid_v02_report()
        .replace("图表解读：该图用于展示", "该图展示")
        .replace("图表解读：该图并列展示", "该图并列展示")
        .replace("图表解读：该图展示", "该图展示")
    )

    result = check_report(report)

    assert result.passed


def test_check_report_allows_long_term_holder_risk_context() -> None:
    report = valid_v02_report() + "\n长期持有者需承受较大净值波动。"

    result = check_report(report)

    assert result.passed


def test_check_chart_specs_flags_placeholder_mismatch() -> None:
    chart_specs = [
        ChartSpec(
            id="returns_by_period",
            title="多周期收益表现",
            type="bar",
            description="展示收益。",
            source_fields=["metrics.performance.return_1y"],
            series=[ChartSeries(name="基金收益", values=[{"period": "1Y", "value": 0.126}])],
            encoding={"x": "period", "y": "value"},
            x_axis="观察周期",
            y_axis="收益率",
            value_unit="decimal_percent",
        )
    ]

    result = check_chart_specs(valid_v02_report(), chart_specs)

    assert not result.passed
    assert any(issue.code == "missing_chart_spec" for issue in result.issues)


def test_check_report_flags_data_restatement_risk() -> None:
    report = valid_v02_report().replace(
        "数据上，基金近1年基金收益为 12.6%；比较上，基准收益为 9.1%，超额收益为 3.5%；解释上，观察期内存在正向基准相对表现；含义上，基准比较是后续跟踪重点；限制上，该结论只覆盖近1年历史窗口。",
        "基金近1年基金收益为 12.6%，基准收益为 9.1%，超额收益为 3.5%。",
    ).replace(
        "数据上，近1年波动率为 18.2%，最大回撤为 -13.7%；比较上，同类平均波动率为 19.6%；解释上，历史波动略低于同类均值；含义上，可结合回撤修复观察风险控制；限制上，缺少日度净值序列。",
        "近1年波动率为 18.2%，最大回撤为 -13.7%。",
    ).replace(
        "数据上，夏普比率为 0.64，信息比率为 0.46；比较上，需要结合超额收益和跟踪误差；解释上，收益质量并非只由绝对收益决定；含义上，应同时观察收益和风险；限制上，缺少完整风险因子拆解。",
        "夏普比率为 0.64，信息比率为 0.46。",
    ).replace(
        "数据上，peer_rank_percentile 为 32.0%；比较上，样例口径表示数值越低排名位置越靠前；解释上，基金在同类中有可观察的历史相对位置；含义上，可辅助同类竞争力研究；限制上，缺少完整同类分布。",
        "peer_rank_percentile 为 32.0%。",
    )

    result = check_report(report)

    assert not result.passed
    assert any(issue.code == "data_restatement_risk" for issue in result.issues)


def test_check_report_flags_portfolio_configuration_advice() -> None:
    report = valid_v02_report() + "\n该基金适合作为组合中的核心配置之一。"

    result = check_report(report)

    assert not result.passed
    assert any(issue.code == "prohibited_expression" for issue in result.issues)


def test_check_chart_specs_requires_frontend_metadata() -> None:
    chart_specs = [
        ChartSpec(
            id="returns_by_period",
            title="多周期收益表现",
            type="bar",
            description="展示收益。",
            source_fields=["metrics.performance.return_1y"],
            series=[ChartSeries(name="基金收益", values=[{"period": "1Y", "value": 0.126}])],
        )
    ]

    result = check_chart_specs(
        "<!-- chart: returns_by_period -->\n图表解读：该图展示收益。",
        chart_specs,
    )

    assert not result.passed
    assert any("encoding" in issue.message for issue in result.issues)
