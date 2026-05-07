"""Pydantic models for structured fund metrics input."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class CategoryInfo(FundInsightModel):
    name: str = Field(min_length=1)
    peer_count: int | None = Field(default=None, ge=0)


class PerformanceMetrics(FundInsightModel):
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    return_3y_annualized: float | None = None
    return_since_inception_annualized: float | None = None
    benchmark_return_1y: float | None = None
    excess_return_1y: float | None = None


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
    benchmark: BenchmarkInfo
    category: CategoryInfo
    metrics: Metrics
    manager: ManagerInfo
    data_quality: DataQuality

    def to_prompt_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable payload for prompt rendering."""

        return self.model_dump(mode="json")
