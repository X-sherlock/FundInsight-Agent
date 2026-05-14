"""Adaptive two-level chunking for research materials."""

from fundinsight.chunking.config import ChunkingConfig
from fundinsight.chunking.models import DocumentBlock, ParentChunk, SmallChunk
from fundinsight.chunking.parent_chunker import build_parent_chunks
from fundinsight.chunking.small_chunker import build_small_chunks
from fundinsight.chunking.structure_detector import build_document_blocks

__all__ = [
    "ChunkingConfig",
    "DocumentBlock",
    "ParentChunk",
    "SmallChunk",
    "build_document_blocks",
    "build_parent_chunks",
    "build_small_chunks",
]
