"""API request and response models for frontend/backend integration."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ReportTaskStatusValue = Literal[
    "queued",
    "loading_data",
    "planning_context",
    "extracting_research",
    "fusing_research",
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
    include_research: bool | None = None
    research_material_ids: list[str] | None = None
    force_reextract: bool = False


class ResearchMaterialCreateRequest(BaseModel):
    title: str
    content: str
    source_type: str
    source_name: str | None = None
    source_url: str | None = None
    publish_date: date | None = None


class ResearchMaterialSummaryResponse(BaseModel):
    material_id: str
    fund_code: str
    title: str
    source_type: Literal["report", "announcement", "news", "internal_research"]
    source_name: str | None = None
    source_url: str | None = None
    publish_date: date | None = None
    file_name: str | None = None
    original_file_path: str | None = None
    extracted_text_path: str | None = None
    chunk_count: int | None = None
    vector_status: Literal["pending", "indexed", "failed"] = "pending"
    vector_error: str | None = None
    created_at: datetime


class ResearchMaterialListResponse(BaseModel):
    items: list[ResearchMaterialSummaryResponse]


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
    include_research: bool | None = None
    research_material_ids: list[str] | None = None
    force_reextract: bool = False
    created_at: str
    updated_at: str
