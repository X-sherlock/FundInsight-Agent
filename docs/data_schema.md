# Data Schema

## 1. Overview

Version 1 accepts one local JSON file containing structured fund metrics. The schema is designed for report generation, not deterministic scoring.

## 2. Top-Level Fields

```json
{
  "fund": {},
  "as_of_date": "2026-03-31",
  "currency": "CNY",
  "benchmark": {},
  "category": {},
  "metrics": {},
  "manager": {},
  "data_quality": {}
}
```

## 3. `fund`

```json
{
  "code": "000001",
  "name": "Example Growth Fund",
  "type": "equity",
  "inception_date": "2018-01-15",
  "fund_company": "Example Asset Management"
}
```

## 4. `benchmark`

```json
{
  "name": "CSI 300",
  "code": "000300.SH"
}
```

## 5. `category`

```json
{
  "name": "主动权益",
  "peer_count": 420
}
```

## 6. `metrics`

Recommended groups:

- `performance`: return and excess return over historical windows.
- `risk`: volatility, downside volatility, beta, tracking error.
- `drawdown`: maximum drawdown and recovery information.
- `risk_adjusted`: Sharpe ratio, information ratio, Calmar ratio.
- `holding`: concentration, turnover, asset allocation.
- `fee`: management fee, custodian fee, sales service fee.
- `scale`: assets under management and share changes.

## 7. `manager`

```json
{
  "name": "Manager Name",
  "tenure_years": 4.2,
  "background": "Equity research and portfolio management"
}
```

## 8. `data_quality`

```json
{
  "source": "sample",
  "missing_fields": [],
  "notes": "Synthetic sample data for project skeleton."
}
```

## 9. Design Notes

- Missing values should be represented as `null`, not fabricated.
- Historical performance fields must include the time window.
- All percentage fields should state whether values are decimals or percentages. Version 1 sample data uses decimal form, where `0.125` means `12.5%`.
- The schema supports benchmark and category context, but the report must avoid turning those comparisons into investment recommendations.
- Important report conclusions should cite relevant fields from this schema, such as `return_1y`, `volatility_1y`, `max_drawdown_1y`, or `excess_return_1y`.
