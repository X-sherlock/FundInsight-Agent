"""Configuration for adaptive two-level research material chunking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:
    parent_chunk_min_chars: int = 800
    parent_chunk_target_chars: int = 1800
    parent_chunk_max_chars: int = 3000
    parent_chunk_overlap_chars: int = 0
    small_chunk_min_chars: int = 250
    small_chunk_target_chars: int = 700
    small_chunk_max_chars: int = 1000
    small_chunk_overlap_chars: int = 100
    title_score_threshold: float = 2.5
    table_min_consecutive_lines: int = 2

    def validate(self) -> None:
        _validate_range("parent", self.parent_chunk_min_chars, self.parent_chunk_target_chars, self.parent_chunk_max_chars)
        _validate_range("small", self.small_chunk_min_chars, self.small_chunk_target_chars, self.small_chunk_max_chars)
        if self.parent_chunk_overlap_chars < 0 or self.small_chunk_overlap_chars < 0:
            raise ValueError("Chunk overlap must not be negative.")


def _validate_range(name: str, minimum: int, target: int, maximum: int) -> None:
    if minimum <= 0 or target <= 0 or maximum <= 0:
        raise ValueError(f"{name} chunk sizes must be positive.")
    if minimum > target or target > maximum:
        raise ValueError(f"{name} chunk sizes must satisfy min <= target <= max.")
