"""Pydantic models for structured fund metrics input and v0.2 report outputs."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FundInsightModel(BaseModel):
    """Base model with strict keys so malformed inputs fail early."""

    model_config = ConfigDict(extra="forbid")


class FundInfo(FundInsightModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    inception_date: date
    fund_company: str = Field(min_length=1)


class BenchmarkInfo(FundInsightModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    description: str | None = None


class CategoryInfo(FundInsightModel):
    name: str = Field(min_length=1)
    peer_count: int | None = Field(default=None, ge=0)


class PeerSummary(FundInsightModel):
    peer_rank_percentile: float | None = Field(default=None, ge=0, le=1)
    peer_average_return_1y: float | None = None
    peer_median_return_1y: float | None = None
    peer_average_volatility_1y: float | None = None
    peer_count: int | None = Field(default=None, ge=0)
    percentile_direction: str | None = None
    notes: str | None = None


class PerformanceMetrics(FundInsightModel):
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    return_3y_annualized: float | None = None
    return_since_inception_annualized: float | None = None
    benchmark_return_1y: float | None = None
    excess_return_1y: float | None = None


class ExcessReturnMetrics(FundInsightModel):
    excess_return_1m: float | None = None
    excess_return_3m: float | None = None
    excess_return_6m: float | None = None
    excess_return_1y: float | None = None
    excess_return_3y_annualized: float | None = None


class RiskMetrics(FundInsightModel):
    volatility_1y: float | None = None
    downside_volatility_1y: float | None = None
    beta_1y: float | None = None
    tracking_error_1y: float | None = None


class DrawdownMetrics(FundInsightModel):
    max_drawdown_1y: float | None = None
    max_drawdown_3y: float | None = None
    drawdown_recovery_days: int | None = Field(default=None, ge=0)


class RiskAdjustedMetrics(FundInsightModel):
    sharpe_1y: float | None = None
    information_ratio_1y: float | None = None
    calmar_3y: float | None = None


class HoldingMetrics(FundInsightModel):
    stock_position: float | None = None
    bond_position: float | None = None
    cash_position: float | None = None
    top10_holding_weight: float | None = None
    turnover_rate_1y: float | None = None


class FeeMetrics(FundInsightModel):
    management_fee: float | None = Field(default=None, ge=0)
    custodian_fee: float | None = Field(default=None, ge=0)
    sales_service_fee: float | None = Field(default=None, ge=0)


class ScaleMetrics(FundInsightModel):
    aum: float | None = Field(default=None, ge=0)
    aum_change_6m: float | None = None
    holder_count: int | None = Field(default=None, ge=0)


class Metrics(FundInsightModel):
    performance: PerformanceMetrics
    risk: RiskMetrics
    drawdown: DrawdownMetrics
    risk_adjusted: RiskAdjustedMetrics
    holding: HoldingMetrics
    fee: FeeMetrics
    scale: ScaleMetrics
    excess_return: ExcessReturnMetrics = Field(default_factory=ExcessReturnMetrics)


class ManagerInfo(FundInsightModel):
    name: str = Field(min_length=1)
    tenure_years: float | None = Field(default=None, ge=0)
    background: str | None = None


class DataQuality(FundInsightModel):
    source: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    notes: str | None = None


class FundMetricsInput(FundInsightModel):
    fund: FundInfo
    as_of_date: date
    currency: str = Field(min_length=1)
    benchmark: BenchmarkInfo | None = None
    benchmark_info: BenchmarkInfo | None = None
    category: CategoryInfo
    peer_summary: PeerSummary | None = None
    metrics: Metrics
    manager: ManagerInfo
    data_quality: DataQuality
    data_notes: list[str] = Field(default_factory=list)

    @field_validator("data_notes", mode="before")
    @classmethod
    def _coerce_data_notes(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def _require_benchmark_context(self) -> "FundMetricsInput":
        if self.benchmark is None and self.benchmark_info is None:
            raise ValueError("Either benchmark or benchmark_info is required.")
        return self

    @property
    def resolved_benchmark(self) -> BenchmarkInfo:
        benchmark = self.benchmark_info or self.benchmark
        if benchmark is None:
            raise ValueError("Benchmark context is missing.")
        return benchmark

    def to_prompt_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable payload for prompt rendering."""

        return self.model_dump(mode="json")


class ChartSeries(FundInsightModel):
    name: str = Field(min_length=1)
    values: list[dict[str, Any]] = Field(min_length=1)


class ChartEncoding(FundInsightModel):
    x: str | None = None
    y: str | None = None
    category: str | None = None
    value: str | None = None


class ChartSpec(FundInsightModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_fields: list[str] = Field(min_length=1)
    series: list[ChartSeries] = Field(min_length=1)
    encoding: ChartEncoding = Field(default_factory=ChartEncoding)
    x_axis: str | None = None
    y_axis: str | None = None
    value_unit: str | None = None
    notes: list[str] = Field(default_factory=list)


class ReportPlan(FundInsightModel):
    source_metrics: dict[str, Any]
    derived_metrics: dict[str, Any]
    metric_tables: dict[str, list[dict[str, Any]]]
    chart_specs: list[ChartSpec]
    analysis_focus: list[str]
    missing_fields: list[str]
    data_notes: list[str]

    def to_prompt_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable report context for the runtime prompt."""

        return self.model_dump(mode="json")
