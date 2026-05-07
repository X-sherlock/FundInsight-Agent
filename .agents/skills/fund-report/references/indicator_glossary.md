# Indicator Glossary

## Basic Information

- `fund.code`: fund identifier.
- `fund.name`: fund name.
- `fund.type`: fund category or investment type.
- `fund.inception_date`: fund establishment date.
- `fund.fund_company`: asset management company.
- `as_of_date`: metric observation date.
- `currency`: reporting currency.

## Performance Metrics

- `return_1m`: historical return over the latest one-month window.
- `return_3m`: historical return over the latest three-month window.
- `return_6m`: historical return over the latest six-month window.
- `return_1y`: historical return over the latest one-year window.
- `return_3y_annualized`: annualized historical return over the latest three-year window.
- `return_since_inception_annualized`: annualized historical return since inception.
- `benchmark_return_1y`: benchmark return over the latest one-year window.
- `excess_return_1y`: fund return minus benchmark return over the latest one-year window.

## Risk Metrics

- `volatility_1y`: annualized volatility over the latest one-year window.
- `downside_volatility_1y`: annualized downside volatility over the latest one-year window.
- `beta_1y`: sensitivity to benchmark movement over the latest one-year window.
- `tracking_error_1y`: volatility of active return versus benchmark.

## Drawdown Metrics

- `max_drawdown_1y`: largest historical peak-to-trough decline over the latest one-year window.
- `max_drawdown_3y`: largest historical peak-to-trough decline over the latest three-year window.
- `drawdown_recovery_days`: number of days needed to recover from the latest major drawdown, if available.

## Risk-Adjusted Metrics

- `sharpe_1y`: excess return per unit of volatility over the latest one-year window.
- `information_ratio_1y`: active return per unit of tracking error over the latest one-year window.
- `calmar_3y`: annualized return divided by maximum drawdown over the latest three-year window.

## Holding Metrics

- `stock_position`: percentage of assets invested in stocks.
- `bond_position`: percentage of assets invested in bonds.
- `cash_position`: percentage of assets held in cash or equivalents.
- `top10_holding_weight`: total weight of top 10 holdings.
- `turnover_rate_1y`: trading turnover over the latest one-year window.

## Fee Metrics

- `management_fee`: annual management fee rate.
- `custodian_fee`: annual custodian fee rate.
- `sales_service_fee`: annual sales service fee rate, if applicable.

## Scale Metrics

- `aum`: assets under management.
- `aum_change_6m`: change in assets under management over the latest six-month window.
- `holder_count`: number of holders, if available.

## Value Format

Unless otherwise specified, percentage-like values use decimal form. For example, `0.125` means `12.5%`.

