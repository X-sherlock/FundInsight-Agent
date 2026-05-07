import type { ChartSpec, DashboardSummary, ReportRecord } from "../features/reports/types";
import { mockFunds } from "./mockFunds";

const charts: ChartSpec[] = [
  {
    id: "returns_by_period",
    title: "多周期收益表现",
    type: "bar",
    description: "展示基金在不同历史观察窗口内的收益表现。",
    source_fields: [
      "metrics.performance.return_1m",
      "metrics.performance.return_3m",
      "metrics.performance.return_6m",
      "metrics.performance.return_1y",
      "metrics.performance.return_3y_annualized"
    ],
    series: [
      {
        name: "基金收益",
        values: [
          { period: "1M", value: 0.018 },
          { period: "3M", value: 0.042 },
          { period: "6M", value: 0.061 },
          { period: "1Y", value: 0.126 },
          { period: "3Y Ann.", value: 0.074 }
        ]
      }
    ],
    encoding: { x: "period", y: "value" },
    x_axis: "观察周期",
    y_axis: "收益率",
    value_unit: "decimal_percent",
    notes: ["用于观察不同时间窗口的历史收益形态。"]
  },
  {
    id: "benchmark_excess_return_1y",
    title: "近一年基金、基准与超额收益",
    type: "bar",
    description: "对照展示基金近一年收益、基准收益和超额收益。",
    source_fields: [
      "metrics.performance.return_1y",
      "metrics.performance.benchmark_return_1y",
      "metrics.performance.excess_return_1y"
    ],
    series: [
      {
        name: "近一年对比",
        values: [
          { metric: "基金收益", value: 0.126 },
          { metric: "基准收益", value: 0.091 },
          { metric: "超额收益", value: 0.035 }
        ]
      }
    ],
    encoding: { x: "metric", y: "value" },
    x_axis: "指标",
    y_axis: "收益率",
    value_unit: "decimal_percent",
    notes: ["用于支持基准对比分析，不代表后续表现判断。"]
  },
  {
    id: "risk_drawdown_profile",
    title: "波动与回撤画像",
    type: "bar",
    description: "展示波动率、下行波动率和最大回撤指标。",
    source_fields: [
      "metrics.risk.volatility_1y",
      "metrics.risk.downside_volatility_1y",
      "metrics.drawdown.max_drawdown_1y",
      "metrics.drawdown.max_drawdown_3y"
    ],
    series: [
      {
        name: "风险指标",
        values: [
          { metric: "近一年波动率", value: 0.182 },
          { metric: "近一年下行波动率", value: 0.119 },
          { metric: "近一年最大回撤", value: -0.137 },
          { metric: "近三年最大回撤", value: -0.246 }
        ]
      }
    ],
    encoding: { x: "metric", y: "value" },
    x_axis: "风险指标",
    y_axis: "指标值",
    value_unit: "decimal_percent",
    notes: ["用于观察历史波动和回撤压力。"]
  },
  {
    id: "risk_adjusted_metrics",
    title: "风险调整后表现",
    type: "bar",
    description: "展示夏普比率、信息比率和 Calmar 比率。",
    source_fields: [
      "metrics.risk_adjusted.sharpe_1y",
      "metrics.risk_adjusted.information_ratio_1y",
      "metrics.risk_adjusted.calmar_3y"
    ],
    series: [
      {
        name: "风险调整指标",
        values: [
          { metric: "夏普比率", value: 0.64 },
          { metric: "信息比率", value: 0.46 },
          { metric: "Calmar 比率", value: 0.31 }
        ]
      }
    ],
    encoding: { x: "metric", y: "value" },
    x_axis: "风险调整指标",
    y_axis: "指标值",
    value_unit: "number",
    notes: ["用于观察收益与风险之间的历史匹配关系。"]
  },
  {
    id: "asset_allocation_profile",
    title: "资产结构占比",
    type: "pie",
    description: "展示权益、债券和现金类资产占比。",
    source_fields: [
      "metrics.holding.stock_position",
      "metrics.holding.bond_position",
      "metrics.holding.cash_position"
    ],
    series: [
      {
        name: "资产结构",
        values: [
          { asset: "权益", value: 0.72 },
          { asset: "债券", value: 0.12 },
          { asset: "现金", value: 0.08 }
        ]
      }
    ],
    encoding: { category: "asset", value: "value" },
    x_axis: "资产类别",
    y_axis: "占比",
    value_unit: "decimal_percent",
    notes: ["用于观察组合资产暴露结构。"]
  },
  {
    id: "peer_context",
    title: "同类相对位置",
    type: "bar",
    description: "展示同类分位、同类收益均值和同类波动均值。",
    source_fields: [
      "peer_summary.peer_rank_percentile",
      "peer_summary.peer_average_return_1y",
      "peer_summary.peer_average_volatility_1y"
    ],
    series: [
      {
        name: "同类上下文",
        values: [
          { metric: "同类分位", value: 0.32 },
          { metric: "同类近一年收益均值", value: 0.083 },
          { metric: "同类近一年波动均值", value: 0.196 }
        ]
      }
    ],
    encoding: { x: "metric", y: "value" },
    x_axis: "同类指标",
    y_axis: "指标值",
    value_unit: "mixed",
    notes: ["同类分位方向以数据供应说明为准。"]
  }
];

const markdown = `# 示例稳健成长混合基金 客户级基金分析报告

## 1. 报告说明

本报告基于结构化基金指标样本生成，数据截至 2026-03-31。报告用于研究辅助和报告草拟，重点解释历史收益、风险、同类上下文和数据局限，不构成任何投资建议。

## 2. 核心结论

1. 近一年基金收益为 12.60%，同期基准收益为 9.10%，超额收益为 3.50%，说明该观察窗口内基金相对基准有正向差异。
2. 近一年波动率为 18.20%，低于同类均值 19.60%，但近三年最大回撤为 -24.60%，说明长期回撤压力仍需在研究中持续关注。
3. 夏普比率为 0.64，信息比率为 0.46，显示单位风险收益效率存在一定支撑，但主动差异的稳定性仍受观察窗口限制。
4. 权益资产占比为 72.00%，债券占比为 12.00%，现金占比为 8.00%，组合暴露以权益资产为主。
5. 同类分位为 32.00%，同类样本数量为 420，只能说明样本口径下的相对位置，不能替代完整同类分布分析。

## 3. 基金基本信息

| 项目 | 内容 |
| :--- | :--- |
| 基金代码 | 000001 |
| 基金名称 | 示例稳健成长混合基金 |
| 基金类型 | 混合型 |
| 管理公司 | 示例基金管理有限公司 |
| 业绩比较基准 | 沪深300指数 |
| 数据日期 | 2026-03-31 |

## 4. 关键指标总览

| 指标 | 数值 | 说明 |
| :--- | :--- | :--- |
| 近一年收益 | 12.60% | 历史观察窗口收益 |
| 近一年超额收益 | 3.50% | 相对基准差异 |
| 近一年波动率 | 18.20% | 历史收益波动 |
| 近一年最大回撤 | -13.70% | 样本期内回撤压力 |
| 夏普比率 | 0.64 | 风险调整后收益观察 |

## 5. 收益分析

近一年基金收益为 12.60%，高于基准收益 9.10%。近三年年化收益为 7.40%，低于近一年收益水平，说明不同观察窗口的收益形态并不一致，需要结合市场环境和样本长度解释。

## 6. 收益质量分析

收益质量需要结合波动率、下行波动率和风险调整指标观察。近一年下行波动率为 11.90%，低于总波动率 18.20%，说明下行区间波动与总体波动之间存在差异。

## 7. 风险控制分析

近一年最大回撤为 -13.70%，近三年最大回撤为 -24.60%，回撤修复天数为 84 天。该组指标提示历史下行压力不能只看短期窗口，还需要观察更长周期中的修复能力。

## 8. 同类竞争力分析

同类分位为 32.00%，同类近一年收益均值为 8.30%，同类近一年波动均值为 19.60%。该结果说明基金在样本口径下具备可讨论的相对位置，但缺少完整分布数据，分析精度受限。

## 9. 基准比较分析

基准采用沪深300指数。基金近一年收益高于基准 3.50 个百分点，但基准口径是否充分覆盖混合型基金的多资产特征，仍需要在正式业务数据中进一步确认。

## 10. 图表解读

<!-- chart: returns_by_period -->
多周期收益图用于观察不同时间窗口的历史收益形态。近一年收益高于近三年年化收益，提示短期窗口和中长期窗口之间存在差异。

<!-- chart: benchmark_excess_return_1y -->
基准对比图展示近一年基金收益、基准收益和超额收益。该图用于解释相对基准差异，不用于形成行动建议。

<!-- chart: risk_drawdown_profile -->
波动与回撤图展示波动率、下行波动率和最大回撤。近三年最大回撤幅度明显大于近一年最大回撤，提示需要关注不同周期的风险暴露。

<!-- chart: risk_adjusted_metrics -->
风险调整指标图展示夏普比率、信息比率和 Calmar 比率。该组指标用于解释收益与风险之间的历史匹配关系。

<!-- chart: asset_allocation_profile -->
资产结构图展示权益、债券和现金类资产占比。权益资产占比较高，说明组合历史暴露更依赖权益资产表现。

<!-- chart: peer_context -->
同类上下文图展示同类分位、同类收益均值和同类波动均值。由于缺少完整同类分布，该图只能作为研究线索。

## 11. 主要观察点

- 收益、风险和同类指标之间存在可解释关系。
- 样本中包含基准、同类和资产结构信息，有助于形成多维报告。
- 风险调整指标可以帮助避免只看收益指标。

## 12. 主要风险

- 样本缺少完整日度净值序列，无法还原更细颗粒度波动。
- 同类分布不完整，无法进行更精细的分位解释。
- 历史指标只描述过去数据，不代表后续结果。

## 13. 适合关注的研究场景

该报告适用于基金研究、报告草拟、指标复核和数据质量检查。

## 14. 数据局限性

缺失字段包括 quarterly_holding_details、daily_nav_series、full_peer_distribution。相关结论应以这些缺失项为边界。

## 15. 风险提示

本报告仅为研究辅助材料，基于样本数据生成。历史指标不代表后续结果，报告不构成任何投资建议。`;

export const mockReports: ReportRecord[] = [
  {
    report_id: "mock-report-000001",
    status: "passed",
    fund: mockFunds[0],
    as_of_date: "2026-03-31",
    created_at: "2026-05-07T11:30:00+08:00",
    core_conclusions: [
      "近一年收益为 12.60%，高于基准收益 9.10%，超额收益为 3.50%。",
      "近一年波动率为 18.20%，低于同类波动均值 19.60%，但近三年最大回撤为 -24.60%。",
      "同类分位为 32.00%，该结论受同类分布数据完整性限制。"
    ],
    key_metrics: [
      { label: "近一年收益", value: "12.60%", tone: "positive", helper: "metrics.performance.return_1y" },
      { label: "近一年超额收益", value: "3.50%", tone: "positive", helper: "metrics.performance.excess_return_1y" },
      { label: "近一年波动率", value: "18.20%", tone: "neutral", helper: "metrics.risk.volatility_1y" },
      { label: "近一年最大回撤", value: "-13.70%", tone: "warning", helper: "metrics.drawdown.max_drawdown_1y" },
      { label: "夏普比率", value: "0.64", tone: "neutral", helper: "metrics.risk_adjusted.sharpe_1y" },
      { label: "同类分位", value: "32.00%", tone: "neutral", helper: "peer_summary.peer_rank_percentile" }
    ],
    markdown,
    chart_specs: { charts },
    guard_result: { passed: true, issues: [] },
    data_quality: {
      missing_fields: ["quarterly_holding_details", "daily_nav_series", "full_peer_distribution"],
      notes: ["示例数据为项目样本，不代表真实基金。", "百分比指标使用小数形式，前端已转换为百分比展示。"]
    }
  }
];

export function buildDashboardSummary(): DashboardSummary {
  return {
    total_reports: mockReports.length,
    passed_reports: mockReports.filter((report) => report.status === "passed").length,
    warning_reports: mockReports.filter((report) => report.status === "warning").length,
    mock_mode: true,
    latest_report: mockReports[0],
    recent_reports: mockReports,
    system_status: [
      { label: "数据模式", value: "Mock Sample", status: "mock" },
      { label: "报告 Guard", value: "Passed", status: "ok" },
      { label: "LLM Provider", value: "Not connected", status: "mock" },
      { label: "后端接口", value: "Mock service", status: "mock" }
    ]
  };
}
