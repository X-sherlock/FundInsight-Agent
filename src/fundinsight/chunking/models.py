"""Data structures used by the two-level chunking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


BlockType = Literal["title", "paragraph", "table", "list", "footer", "header", "unknown"]


@dataclass(frozen=True)
class DocumentBlock:
    block_id: str
    text: str
    block_type: BlockType
    page_number: int
    order_index: int
    level: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParentChunk:
    parent_chunk_id: str
    material_id: str
    fund_code: str
    text: str
    chunk_index: int
    blocks: tuple[DocumentBlock, ...]
    section_path: tuple[str, ...]
    page_start: int
    page_end: int
    block_start_index: int
    block_end_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SmallChunk:
    chunk_id: str
    parent_chunk_id: str
    material_id: str
    fund_code: str
    raw_text: str
    embedding_text: str
    chunk_index: int
    chunk_index_in_parent: int
    section_path: tuple[str, ...]
    page_start: int
    page_end: int
    metadata: dict[str, Any] = field(default_factory=dict)
