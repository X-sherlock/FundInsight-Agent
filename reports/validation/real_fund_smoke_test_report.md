# Real Fund Smoke Test Report

- 测试时间：2026-05-11T16:03:23.041899+08:00
- 测试基金列表：161725
- LLM 链路：真实 LLM（未配置或调用失败则验收失败，不使用模拟结果补齐）
- 是否使用任何虚拟/合成数据：否

## 161725 招商中证白酒指数A
- metrics.json 生成情况：成功
- metrics.json 路径：D:\Data\Workspace\FundInsightAgent\data\funds\161725\metrics.json
- data_sources.json 路径：D:\Data\Workspace\FundInsightAgent\data\funds\161725\data_sources.json
- 导入材料数量：3
- 是否成功导入 2 份以上材料：是
- extracted_signals.json 生成情况：成功
- fusion_context.json 生成情况：成功
- signal 数量：10
- analyzed_materials 数量：3
- source_materials 数量：2
- 增强报告生成情况：成功
- guard 是否通过：False
- 真实链路验收是否通过：否
- 是否使用任何虚拟/合成数据：否
- 缺失指标：metrics.performance.return_1m, metrics.performance.return_3y_annualized, metrics.performance.return_since_inception_annualized, metrics.risk.volatility_1y, metrics.risk.downside_volatility_1y, metrics.risk.beta_1y, metrics.risk.tracking_error_1y, metrics.drawdown.max_drawdown_1y, metrics.drawdown.drawdown_recovery_days, metrics.risk_adjusted.sharpe_1y, metrics.risk_adjusted.information_ratio_1y, metrics.risk_adjusted.calmar_3y, metrics.scale.aum_change_6m, metrics.scale.holder_count, peer_summary

| 材料 | 类型 | 来源 | 发布时间 | URL | 解析状态 | 失败原因 |
| --- | --- | --- | --- | --- | --- | --- |
| 招商中证白酒指数证券投资基金2026年第1季度报告 | report | 招商基金官网 | 2026-04-22 | https://static.cmfchina.com/fundarticle/20260422/20022306017791.pdf | parse_failed | PDF 解析库不可用；可安装 pypdf、pdfplumber 或 PyMuPDF 作为 dev 依赖 |
| 招商中证白酒指数基金官网产品详情 | announcement | 招商基金官网 |  | https://www.cmfchina.com/web/fundDetail/161725/index.html | success |  |
| 招商中证白酒指数基金档案 | announcement | 天天基金基金档案 |  | https://fundf10.eastmoney.com/161725.html | success |  |
| 招商中证白酒指数公开行情与风险数据 | news | 阿牛智投 |  | https://www.aniu.com/fund_detail_161725.shtml | success |  |

失败来源：
- https://static.cmfchina.com/fundarticle/20260422/20022306017791.pdf: PDF 解析库不可用；可安装 pypdf、pdfplumber 或 PyMuPDF 作为 dev 依赖

Guard issues：
- Report should include at least 3 tables.
- Report should contain explicit analytical interpretation language.
- Core conclusions look too close to metric restatement and need interpretation.
- chart_specs_json contains id not used by Markdown placeholders: asset_allocation_profile

等待用户批准后才能使用虚拟数据补齐。

## 多材料验收结论：不通过