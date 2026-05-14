# Real Fund Acceptance Samples

This directory includes two real public fund samples in addition to the synthetic `000001`-`000005` funds.

## 110022 易方达消费行业股票

- Metrics file: `data/funds/110022/metrics.json`
- Research material: `data/funds/110022/research/materials/mat_3a28a3b92dde5511.*`
- Primary source: 易方达消费行业股票型证券投资基金2026年第1季度报告, published 2026-04-22.
- Source URL: https://cdn.efunds.com.cn/owch/data/bulletin/20260422/%E6%98%93%E6%96%B9%E8%BE%BE%E6%B6%88%E8%B4%B9%E8%A1%8C%E4%B8%9A%E8%82%A1%E7%A5%A8%E5%9E%8B%E8%AF%81%E5%88%B8%E6%8A%95%E8%B5%84%E5%9F%BA%E9%87%912026%E5%B9%B4%E7%AC%AC1%E5%AD%A3%E5%BA%A6%E6%8A%A5%E5%91%8A.pdf?from=person
- Supplemental public page used for `max_drawdown_3y`: https://www.aniu.com/fund_detail_110022.shtml

## 161725 招商中证白酒指数A

- Metrics file: `data/funds/161725/metrics.json`
- Research material: `data/funds/161725/research/materials/mat_6a1de551fd70d0b5.*`
- Primary sources: 招商基金官网产品详情页 and 招商中证白酒指数证券投资基金2026年第1季度报告, published 2026-04-22.
- Source URLs:
  - https://www.cmfchina.com/web/fundDetail/161725/index.html
  - https://static.cmfchina.com/fundarticle/20260422/20022306017791.pdf
- Supplemental public page used for `max_drawdown_3y`: https://www.aniu.com/fund_detail_161725.shtml

## Data Policy

Only values traceable to the listed public sources are populated. Fields not found with a matching public-data口径 are left as `null` and listed in `data_quality.missing_fields` or `data_notes`. No synthetic values are used to fill these real fund samples.
