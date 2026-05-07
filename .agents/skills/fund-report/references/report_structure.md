# Report Structure

The Markdown report must follow this v0.2 structure. Section names should remain stable so `report_guard` can check the output without judging fund quality.

```markdown
# {基金名称} 客户级基金深度分析报告

## 1. 报告说明

## 2. 核心结论

## 3. 基金基本信息

## 4. 关键指标总览

## 5. 收益分析

## 6. 收益质量分析

## 7. 风险控制分析

## 8. 同类竞争力分析

## 9. 基准比较分析

## 10. 图表解读

## 11. 主要优势

## 12. 主要风险

## 13. 适合关注的场景

## 14. 数据局限性

## 15. 风险提示
```

## Section Requirements

### 1. 报告说明

State the report date, data source if available, and that the report is based on structured historical indicators.

### 2. 核心结论

Provide at least five concise conclusions. Each important conclusion should cite metrics and follow Data -> Comparison -> Interpretation -> Implication -> Caveat where possible.

### 3. 基金基本信息

Summarize fund code, name, type, inception date, fund company, benchmark, category, manager, and observation date.

### 4. 关键指标总览

Use Markdown tables for selected return, benchmark, excess return, risk, drawdown, risk-adjusted, holding, fee, and scale metrics.

### 5. 收益分析

Discuss historical return windows and explicitly include fund return, benchmark return, and excess return when available.

### 6. 收益质量分析

Discuss consistency across return windows, excess return, risk-adjusted return, and the relationship between return and volatility. Do not turn this into a score.

### 7. 风险控制分析

Discuss maximum drawdown, volatility, downside volatility, beta, tracking error, recovery days, and Sharpe ratio where available.

### 8. 同类竞争力分析

Use `peer_summary.peer_rank_percentile` and related peer fields when provided. Explain percentile direction and limitations. If peer data is missing, state that peer analysis is limited.

### 9. 基准比较分析

Use benchmark name, benchmark return, excess return, beta, and tracking error when available.

### 10. 图表解读

Include at least five chart placeholders such as `<!-- chart: returns_by_period -->`. Each placeholder must be followed by an interpretation paragraph.

### 11. 主要优势

Summarize historically observed strengths using evidence. Do not write promotional claims.

### 12. 主要风险

Summarize risk points and uncertainties using evidence.

### 13. 适合关注的场景

Describe research, due-diligence, or monitoring scenarios where the report may be useful. This is not a suitability, purchase, holding, timing, portfolio-construction, position-sizing, core-allocation, or allocation recommendation.

### 14. 数据局限性

List missing, stale, synthetic, or incomplete fields and explain how they limit interpretation.

### 15. 风险提示

Include a clear statement that the report is not investment advice and does not constitute buy, sell, hold, timing, or allocation guidance. State that historical indicators do not predict or guarantee future returns.
