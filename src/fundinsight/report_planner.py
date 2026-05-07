"""Prepare v0.2 report context without judging fund quality."""

from __future__ import annotations

from typing import Any

from fundinsight.models import ChartEncoding, ChartSeries, ChartSpec, FundMetricsInput, ReportPlan


def build_report_plan(fund_metrics: FundMetricsInput) -> ReportPlan:
    """Build deterministic context for the LLM.

    The planner only organizes data, computes simple derived metrics, drafts
    charts, and identifies analysis focus. It does not score or recommend funds.
    """

    derived_metrics = _build_derived_metrics(fund_metrics)
    metric_tables = _build_metric_tables(fund_metrics, derived_metrics)
    chart_specs = _build_chart_specs(fund_metrics, derived_metrics)
    missing_fields = _collect_missing_fields(fund_metrics, derived_metrics)
    data_notes = _collect_data_notes(fund_metrics)
    analysis_focus = _build_analysis_focus(fund_metrics, missing_fields)

    return ReportPlan(
        source_metrics=fund_metrics.to_prompt_payload(),
        derived_metrics=derived_metrics,
        metric_tables=metric_tables,
        chart_specs=chart_specs,
        analysis_focus=analysis_focus,
        missing_fields=missing_fields,
        data_notes=data_notes,
    )


def _build_derived_metrics(fund_metrics: FundMetricsInput) -> dict[str, Any]:
    metrics = fund_metrics.metrics
    performance = metrics.performance
    holding = metrics.holding
    fee = metrics.fee

    computed_excess_return_1y = _subtract(
        performance.return_1y,
        performance.benchmark_return_1y,
    )
    reported_excess_return_1y = (
        metrics.excess_return.excess_return_1y
        if metrics.excess_return.excess_return_1y is not None
        else performance.excess_return_1y
    )

    fee_total = _sum_known(
        fee.management_fee,
        fee.custodian_fee,
        fee.sales_service_fee,
    )
    asset_position_total = _sum_known(
        holding.stock_position,
        holding.bond_position,
        holding.cash_position,
    )

    return {
        "computed_excess_return_1y": computed_excess_return_1y,
        "reported_excess_return_1y": reported_excess_return_1y,
        "fee_total": fee_total,
        "asset_position_total": asset_position_total,
        "return_to_volatility_1y": _safe_divide(
            performance.return_1y,
            metrics.risk.volatility_1y,
        ),
        "drawdown_to_return_1y": _safe_divide(
            metrics.drawdown.max_drawdown_1y,
            performance.return_1y,
        ),
    }


def _build_metric_tables(
    fund_metrics: FundMetricsInput,
    derived_metrics: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    metrics = fund_metrics.metrics
    performance = metrics.performance
    peer = fund_metrics.peer_summary

    return {
        "return_periods": [
            _row("近1个月收益", "return_1m", performance.return_1m, "percentage"),
            _row("近3个月收益", "return_3m", performance.return_3m, "percentage"),
            _row("近6个月收益", "return_6m", performance.return_6m, "percentage"),
            _row("近1年收益", "return_1y", performance.return_1y, "percentage"),
            _row(
                "近3年年化收益",
                "return_3y_annualized",
                performance.return_3y_annualized,
                "percentage",
            ),
            _row(
                "成立以来年化收益",
                "return_since_inception_annualized",
                performance.return_since_inception_annualized,
                "percentage",
            ),
        ],
        "benchmark_comparison": [
            _row("基金近1年收益", "return_1y", performance.return_1y, "percentage"),
            _row(
                "基准近1年收益",
                "benchmark_return_1y",
                performance.benchmark_return_1y,
                "percentage",
            ),
            _row(
                "近1年超额收益",
                "reported_excess_return_1y",
                derived_metrics.get("reported_excess_return_1y"),
                "percentage",
            ),
            _row(
                "计算近1年超额收益",
                "computed_excess_return_1y",
                derived_metrics.get("computed_excess_return_1y"),
                "percentage",
            ),
        ],
        "risk_profile": [
            _row("近1年波动率", "volatility_1y", metrics.risk.volatility_1y, "percentage"),
            _row(
                "近1年下行波动率",
                "downside_volatility_1y",
                metrics.risk.downside_volatility_1y,
                "percentage",
            ),
            _row("近1年最大回撤", "max_drawdown_1y", metrics.drawdown.max_drawdown_1y, "percentage"),
            _row("近3年最大回撤", "max_drawdown_3y", metrics.drawdown.max_drawdown_3y, "percentage"),
            _row(
                "回撤修复天数",
                "drawdown_recovery_days",
                metrics.drawdown.drawdown_recovery_days,
                "days",
            ),
            _row("夏普比率", "sharpe_1y", metrics.risk_adjusted.sharpe_1y, "number"),
        ],
        "peer_summary": [
            _row(
                "同类分位",
                "peer_rank_percentile",
                peer.peer_rank_percentile if peer else None,
                "percentile",
            ),
            _row(
                "同类平均近1年收益",
                "peer_average_return_1y",
                peer.peer_average_return_1y if peer else None,
                "percentage",
            ),
            _row(
                "同类中位近1年收益",
                "peer_median_return_1y",
                peer.peer_median_return_1y if peer else None,
                "percentage",
            ),
            _row(
                "同类平均近1年波动率",
                "peer_average_volatility_1y",
                peer.peer_average_volatility_1y if peer else None,
                "percentage",
            ),
        ],
    }


def _build_chart_specs(
    fund_metrics: FundMetricsInput,
    derived_metrics: dict[str, Any],
) -> list[ChartSpec]:
    metrics = fund_metrics.metrics
    performance = metrics.performance
    peer = fund_metrics.peer_summary

    return [
        ChartSpec(
            id="returns_by_period",
            title="多周期收益表现",
            type="bar",
            description="展示基金在不同历史观察窗口内的收益表现。",
            source_fields=[
                "metrics.performance.return_1m",
                "metrics.performance.return_3m",
                "metrics.performance.return_6m",
                "metrics.performance.return_1y",
                "metrics.performance.return_3y_annualized",
            ],
            series=[
                ChartSeries(
                    name="基金收益",
                    values=[
                        {"period": "1M", "value": performance.return_1m},
                        {"period": "3M", "value": performance.return_3m},
                        {"period": "6M", "value": performance.return_6m},
                        {"period": "1Y", "value": performance.return_1y},
                        {"period": "3Y Ann.", "value": performance.return_3y_annualized},
                    ],
                )
            ],
            encoding=ChartEncoding(x="period", y="value"),
            x_axis="观察周期",
            y_axis="收益率",
            value_unit="decimal_percent",
            notes=["用于观察不同时间窗口的历史收益形态。"],
        ),
        ChartSpec(
            id="benchmark_excess_return_1y",
            title="近1年基金、基准与超额收益",
            type="bar",
            description="对照基金近1年收益、基准收益和超额收益。",
            source_fields=[
                "metrics.performance.return_1y",
                "metrics.performance.benchmark_return_1y",
                "metrics.performance.excess_return_1y",
                "metrics.excess_return.excess_return_1y",
            ],
            series=[
                ChartSeries(
                    name="近1年对比",
                    values=[
                        {"metric": "基金收益", "value": performance.return_1y},
                        {"metric": "基准收益", "value": performance.benchmark_return_1y},
                        {
                            "metric": "超额收益",
                            "value": derived_metrics.get("reported_excess_return_1y"),
                        },
                    ],
                )
            ],
            encoding=ChartEncoding(x="metric", y="value"),
            x_axis="指标",
            y_axis="收益率",
            value_unit="decimal_percent",
            notes=["用于支撑基准比较分析，不代表未来相对表现。"],
        ),
        ChartSpec(
            id="risk_drawdown_profile",
            title="波动与回撤风险画像",
            type="bar",
            description="展示波动率、下行波动率和最大回撤指标。",
            source_fields=[
                "metrics.risk.volatility_1y",
                "metrics.risk.downside_volatility_1y",
                "metrics.drawdown.max_drawdown_1y",
                "metrics.drawdown.max_drawdown_3y",
            ],
            series=[
                ChartSeries(
                    name="风险指标",
                    values=[
                        {"metric": "近1年波动率", "value": metrics.risk.volatility_1y},
                        {
                            "metric": "近1年下行波动率",
                            "value": metrics.risk.downside_volatility_1y,
                        },
                        {"metric": "近1年最大回撤", "value": metrics.drawdown.max_drawdown_1y},
                        {"metric": "近3年最大回撤", "value": metrics.drawdown.max_drawdown_3y},
                    ],
                )
            ],
            encoding=ChartEncoding(x="metric", y="value"),
            x_axis="风险指标",
            y_axis="指标值",
            value_unit="decimal_percent",
            notes=["用于观察历史波动和回撤压力。"],
        ),
        ChartSpec(
            id="risk_adjusted_metrics",
            title="风险调整后表现",
            type="bar",
            description="展示夏普比率、信息比率和 Calmar 比率。",
            source_fields=[
                "metrics.risk_adjusted.sharpe_1y",
                "metrics.risk_adjusted.information_ratio_1y",
                "metrics.risk_adjusted.calmar_3y",
            ],
            series=[
                ChartSeries(
                    name="风险调整指标",
                    values=[
                        {"metric": "夏普比率", "value": metrics.risk_adjusted.sharpe_1y},
                        {
                            "metric": "信息比率",
                            "value": metrics.risk_adjusted.information_ratio_1y,
                        },
                        {"metric": "Calmar 比率", "value": metrics.risk_adjusted.calmar_3y},
                    ],
                )
            ],
            encoding=ChartEncoding(x="metric", y="value"),
            x_axis="风险调整指标",
            y_axis="指标值",
            value_unit="number",
            notes=["用于观察收益与风险之间的历史匹配关系。"],
        ),
        ChartSpec(
            id="asset_allocation_profile",
            title="资产配置结构",
            type="pie",
            description="展示股票、债券和现金仓位比例。",
            source_fields=[
                "metrics.holding.stock_position",
                "metrics.holding.bond_position",
                "metrics.holding.cash_position",
            ],
            series=[
                ChartSeries(
                    name="资产配置",
                    values=[
                        {"asset": "股票", "value": metrics.holding.stock_position},
                        {"asset": "债券", "value": metrics.holding.bond_position},
                        {"asset": "现金", "value": metrics.holding.cash_position},
                    ],
                )
            ],
            encoding=ChartEncoding(category="asset", value="value"),
            x_axis="资产类别",
            y_axis="占比",
            value_unit="decimal_percent",
            notes=["用于观察组合资产暴露结构。"],
        ),
        ChartSpec(
            id="peer_context",
            title="同类相对位置",
            type="bar",
            description="展示同类分位和同类收益、波动参照。",
            source_fields=[
                "peer_summary.peer_rank_percentile",
                "peer_summary.peer_average_return_1y",
                "peer_summary.peer_average_volatility_1y",
            ],
            series=[
                ChartSeries(
                    name="同类上下文",
                    values=[
                        {
                            "metric": "同类分位",
                            "value": peer.peer_rank_percentile if peer else None,
                        },
                        {
                            "metric": "同类平均近1年收益",
                            "value": peer.peer_average_return_1y if peer else None,
                        },
                        {
                            "metric": "同类平均近1年波动率",
                            "value": peer.peer_average_volatility_1y if peer else None,
                        },
                    ],
                )
            ],
            encoding=ChartEncoding(x="metric", y="value"),
            x_axis="同类指标",
            y_axis="指标值",
            value_unit="mixed",
            notes=["同类分位方向应以数据提供方说明为准。"],
        ),
    ]


def _collect_missing_fields(
    fund_metrics: FundMetricsInput,
    derived_metrics: dict[str, Any],
) -> list[str]:
    missing = list(fund_metrics.data_quality.missing_fields)
    if fund_metrics.peer_summary is None:
        missing.append("peer_summary")
    elif fund_metrics.peer_summary.peer_rank_percentile is None:
        missing.append("peer_summary.peer_rank_percentile")
    if derived_metrics.get("reported_excess_return_1y") is None:
        missing.append("metrics.performance.excess_return_1y")
    return sorted(set(missing))


def _collect_data_notes(fund_metrics: FundMetricsInput) -> list[str]:
    notes = list(fund_metrics.data_notes)
    if fund_metrics.data_quality.notes:
        notes.append(fund_metrics.data_quality.notes)
    if fund_metrics.peer_summary and fund_metrics.peer_summary.notes:
        notes.append(fund_metrics.peer_summary.notes)
    return notes


def _build_analysis_focus(
    fund_metrics: FundMetricsInput,
    missing_fields: list[str],
) -> list[str]:
    focus = [
        "围绕基金收益、基准收益、超额收益建立收益分析链条。",
        "结合波动率、最大回撤、夏普比率解释风险控制特征。",
        "使用同类分位和同类均值信息说明同类竞争力，但不形成评级或排序。",
        "结合持仓结构、费用、规模和管理人信息解释运作特征。",
        "每个核心结论需要说明数据限制和历史指标边界。",
    ]
    if fund_metrics.peer_summary is None or "peer_summary.peer_rank_percentile" in missing_fields:
        focus.append("同类分位数据不足时，应明确同类竞争力分析受限。")
    return focus


def _row(label: str, field: str, value: Any, unit: str) -> dict[str, Any]:
    return {
        "label": label,
        "field": field,
        "value": value,
        "unit": unit,
        "display": _format_value(value, unit),
    }


def _format_value(value: Any, unit: str) -> str:
    if value is None:
        return "缺失"
    if unit in {"percentage", "percentile"}:
        return f"{value * 100:.2f}%"
    if unit == "days":
        return f"{value} 天"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _subtract(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return numerator / denominator


def _sum_known(*values: float | None) -> float | None:
    known = [value for value in values if value is not None]
    if not known:
        return None
    return sum(known)
