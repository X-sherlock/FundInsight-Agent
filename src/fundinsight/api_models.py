"""API request and response models for frontend/backend integration."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ReportTaskStatusValue = Literal[
    "queued",
    "loading_data",
    "planning_context",
    "llm_generating",
    "parsing_charts",
    "quality_checking",
    "saving_report",
    "completed",
    "failed",
]


class ApiError(BaseModel):
    code: str
    message: str


class FundBriefResponse(BaseModel):
    code: str
    name: str
    type: str
    company: str
    benchmark: str
    as_of_date: str
    category: str


class FundSearchResponse(BaseModel):
    items: list[FundBriefResponse]


class FundMetricsResponse(BaseModel):
    fund: FundBriefResponse
    metrics: dict[str, Any]
    raw: dict[str, Any]


class EnsureReportRequest(BaseModel):
    fund_code: str = Field(min_length=1)
    force_regenerate: bool = False


class EnsureReportResponse(BaseModel):
    mode: Literal["existing", "created", "running"]
    status: str
    report_id: str | None = None
    report_url: str | None = None
    task_id: str | None = None
    status_url: str | None = None


class ReportTaskResponse(BaseModel):
    task_id: str
    fund_code: str
    status: ReportTaskStatusValue
    stage: ReportTaskStatusValue
    stage_label: str
    message: str
    report_id: str | None = None
    error: ApiError | None = None
    created_at: str
    updated_at: str
