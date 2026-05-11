"""Pydantic models for unstructured fund research materials."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

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
    publish_date: date | None = None
    file_name: str | None = None
    content_hash: str = Field(min_length=1)
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
    chunk_index: int = Field(ge=0)
    chunk_text: str = Field(min_length=1)

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


class ResearchFusionContext(ResearchBaseModel):
    fund_code: str = Field(min_length=1)
    positive_factors: list[ResearchSignal] = Field(default_factory=list)
    risk_notices: list[ResearchSignal] = Field(default_factory=list)
    key_events: list[ResearchSignal] = Field(default_factory=list)
    view_changes: list[ResearchSignal] = Field(default_factory=list)
    source_materials: list[ResearchDocument] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_now)

    @field_validator("fund_code")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value
