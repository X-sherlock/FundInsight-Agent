"""Pydantic models for unstructured fund research materials."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SourceType = Literal["report", "announcement", "news", "internal_research"]
SignalType = Literal["positive_factor", "risk_notice", "key_event", "view_change"]
ImpactDirection = Literal["positive", "negative", "neutral", "uncertain"]
Importance = Literal["low", "medium", "high"]


def _now() -> datetime:
    return datetime.now().astimezone()


class ResearchBaseModel(BaseModel):
    """Base model for research material objects."""

    model_config = ConfigDict(extra="forbid")


class ResearchDocument(ResearchBaseModel):
    material_id: str = Field(min_length=1)
    fund_code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: SourceType
    source_name: str | None = None
    source_url: str | None = None
    publish_date: date | None = None
    file_name: str | None = None
    content_hash: str = Field(min_length=1)
    original_file_path: str | None = None
    extracted_text_path: str | None = None
    chunk_count: int | None = Field(default=None, ge=0)
    parent_chunk_count: int | None = Field(default=None, ge=0)
    vector_status: Literal["pending", "indexed", "failed"] = "pending"
    vector_error: str | None = None
    created_at: datetime = Field(default_factory=_now)

    @field_validator("material_id", "fund_code", "title", "content_hash")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class ResearchChunk(ResearchBaseModel):
    chunk_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    fund_code: str = Field(min_length=1)
    fund_name: str | None = None
    chunk_index: int = Field(ge=0)
    chunk_text: str = Field(min_length=1)
    parent_chunk_id: str | None = None
    chunk_level: Literal["small", "parent"] = "small"
    chunk_index_in_parent: int | None = Field(default=None, ge=0)
    embedding_text: str | None = None
    raw_text: str | None = None
    parent_chunk_text: str | None = None
    section_path: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    block_start_index: int | None = Field(default=None, ge=0)
    block_end_index: int | None = Field(default=None, ge=0)
    document_title: str | None = None
    document_type: str | None = None
    report_period: str | None = None
    publish_date: date | None = None
    source_url: str | None = None

    @field_validator("chunk_id", "material_id", "fund_code", "chunk_text")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class ResearchSignal(ResearchBaseModel):
    signal_id: str = Field(min_length=1)
    fund_code: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    chunk_id: str | None = None
    signal_type: SignalType
    summary: str = Field(min_length=1)
    detail: str | None = None
    category: str | None = None
    signal_date: date | None = None
    impact_direction: ImpactDirection | None = None
    importance: Importance | None = None
    confidence: float = Field(ge=0, le=1)
    evidence_text: str = Field(min_length=1)
    source_type: SourceType
    publish_date: date | None = None

    @field_validator("signal_id", "fund_code", "material_id", "summary", "evidence_text")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class ResearchSignalBundle(ResearchBaseModel):
    fund_code: str = Field(min_length=1)
    signals: list[ResearchSignal] = Field(default_factory=list)
    materials: list[ResearchDocument] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_now)

    @field_validator("fund_code")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class ResearchAnalyzedMaterial(ResearchBaseModel):
    material_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: SourceType
    source_name: str | None = None
    source_url: str | None = None
    publish_date: date | None = None
    chunk_count: int | None = Field(default=None, ge=0)
    signal_count: int = Field(default=0, ge=0)

    @field_validator("material_id", "title")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class ResearchFusionContext(ResearchBaseModel):
    fund_code: str = Field(min_length=1)
    positive_factors: list[ResearchSignal] = Field(default_factory=list)
    risk_notices: list[ResearchSignal] = Field(default_factory=list)
    key_events: list[ResearchSignal] = Field(default_factory=list)
    view_changes: list[ResearchSignal] = Field(default_factory=list)
    source_materials: list[ResearchDocument] = Field(default_factory=list)
    analyzed_materials: list[ResearchAnalyzedMaterial] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_now)

    @field_validator("fund_code")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class RetrievedResearchChunk(ResearchBaseModel):
    chunk_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    fund_code: str = Field(min_length=1)
    fund_name: str | None = None
    chunk_index: int = Field(ge=0)
    evidence_text: str = Field(min_length=1)
    relevance_score: float = Field(ge=0)
    source_type: SourceType
    title: str = Field(min_length=1)
    source_name: str | None = None
    source_url: str | None = None
    publish_date: date | None = None
    file_name: str | None = None
    original_file_path: str | None = None
    parent_chunk_id: str | None = None
    matched_small_chunk_id: str | None = None
    section_path: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    document_type: str | None = None
    report_period: str | None = None
    raw_text: str | None = None
    analysis_title: str | None = None
    material_summary: str | None = None
    sentiment_label: str | None = None
    evidence_excerpt: str | None = None

    @field_validator("chunk_id", "material_id", "fund_code", "evidence_text", "title")
    @classmethod
    def _require_retrieved_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class FactCardSourceMaterial(ResearchBaseModel):
    material_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: SourceType
    source_name: str | None = None
    source_url: str | None = None
    publish_date: date | None = None
    file_name: str | None = None
    original_file_path: str | None = None
    chunk_count: int | None = Field(default=None, ge=0)


class FactCard(ResearchBaseModel):
    fund_code: str = Field(min_length=1)
    source_metrics: dict[str, Any]
    derived_metrics: dict[str, Any] = Field(default_factory=dict)
    metric_tables: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    data_notes: list[str] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedResearchChunk] = Field(default_factory=list)
    source_materials: list[FactCardSourceMaterial] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_now)

    @field_validator("fund_code")
    @classmethod
    def _require_fact_card_fund_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value
