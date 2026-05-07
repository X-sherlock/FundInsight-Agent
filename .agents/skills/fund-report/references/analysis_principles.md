# Analysis Principles

## 1. Do Not Merely Restate Data

Reports must convert metrics into grounded interpretation. A sentence that only repeats a value is insufficient unless it supports a larger analytical chain.

## 2. Use The Analysis Chain

Important conclusions should follow this chain:

```text
Data -> Comparison -> Interpretation -> Implication -> Caveat
```

Examples:

- Data: `return_1y` is 12.6%.
- Comparison: benchmark one-year return is 9.1%, so excess return is 3.5%.
- Interpretation: the fund had positive historical active return over this window.
- Implication: this makes benchmark-relative behavior a useful monitoring dimension.
- Caveat: the conclusion is limited to the supplied one-year window and does not predict future excess return.

If comparison data is absent, state the limitation explicitly.

## 3. Ground Conclusions In Input Metrics

Important conclusions should cite the specific input metrics that support them.

Use:

- `return_1m`, `return_3m`, `return_6m`, `return_1y`, and `return_3y_annualized` for return behavior.
- `benchmark_return_1y`, `excess_return_1y`, and `metrics.excess_return` for benchmark-relative behavior.
- `volatility_1y`, `downside_volatility_1y`, `beta_1y`, and `tracking_error_1y` for risk exposure.
- `max_drawdown_1y`, `max_drawdown_3y`, and `drawdown_recovery_days` for drawdown pressure.
- `sharpe_1y`, `information_ratio_1y`, and `calmar_3y` for risk-adjusted performance.
- `peer_summary.peer_rank_percentile` for same-category context when available.

If an important metric is missing, state that the conclusion is limited by missing data.

## 4. Compare Only When Context Exists

Benchmark and peer comparisons should be made only when the input provides relevant benchmark, category, peer average, percentile, or comparison fields.

If comparison data is absent, say that comparison is limited.

## 5. Avoid Rule-Based Scoring

Do not calculate a fund score from fixed weights. Do not infer a final grade from a hidden scoring rubric.

The report may summarize historical characteristics, pressures, and uncertainties qualitatively, but must not turn them into an investment rating.

## 6. Treat Historical Performance Carefully

Historical return, volatility, and drawdown metrics describe past behavior. They do not imply future return, future volatility, or future drawdown.

## 7. Separate Return, Risk, Competition, And Operations

Discuss:

- return behavior
- return quality
- risk exposure
- drawdown experience
- risk-adjusted performance
- benchmark context
- peer context
- manager and operation factors
- fees, scale, and holding concentration

Avoid collapsing these dimensions into a single verdict.

## 8. Preserve Uncertainty

When data is missing, stale, synthetic, or incomplete, explicitly describe the limitation.

Use cautious phrases such as:

- "从已提供数据看"
- "在该观察区间内"
- "该指标只能反映历史表现"
- "由于缺少同类分位数据，无法判断其在同类中的相对位置"
