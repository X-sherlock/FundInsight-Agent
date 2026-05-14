"""Build parent chunks from structured document blocks."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from fundinsight.chunking.config import ChunkingConfig
from fundinsight.chunking.models import DocumentBlock, ParentChunk


def build_parent_chunks(
    *,
    blocks: Sequence[DocumentBlock],
    material_id: str,
    fund_code: str,
    document_metadata: dict[str, Any] | None = None,
    config: ChunkingConfig | None = None,
) -> list[ParentChunk]:
    resolved_config = config or ChunkingConfig()
    resolved_config.validate()
    metadata = document_metadata or {}
    if not blocks:
        return []

    groups = _initial_groups(list(blocks), resolved_config)
    split_groups = [group for item in groups for group in _split_group(item, resolved_config)]
    merged_groups = _merge_short_groups(split_groups, resolved_config)

    parents: list[ParentChunk] = []
    for index, group in enumerate(merged_groups):
        text = _join_blocks(group)
        if not text.strip():
            continue
        page_numbers = [block.page_number for block in group]
        section_path = _section_path(group)
        parents.append(
            ParentChunk(
                parent_chunk_id=f"{material_id}_parent_{len(parents):04d}",
                material_id=material_id,
                fund_code=fund_code,
                text=text,
                chunk_index=len(parents),
                blocks=tuple(group),
                section_path=tuple(section_path),
                page_start=min(page_numbers),
                page_end=max(page_numbers),
                block_start_index=group[0].order_index,
                block_end_index=group[-1].order_index,
                metadata={**metadata, "chunk_level": "parent"},
            )
        )
    return parents


def _initial_groups(blocks: list[DocumentBlock], config: ChunkingConfig) -> list[list[DocumentBlock]]:
    groups: list[list[DocumentBlock]] = []
    current: list[DocumentBlock] = []
    current_title_level: int | None = None

    for block in blocks:
        if block.block_type == "title":
            if current and _group_len(current) >= config.parent_chunk_min_chars:
                groups.append(current)
                current = []
            elif current and current_title_level is not None and block.level is not None and block.level <= current_title_level:
                groups.append(current)
                current = []
            current_title_level = block.level
            current.append(block)
            continue

        if block.block_type == "table" and current and _group_len(current) >= config.parent_chunk_target_chars:
            groups.append(current)
            current = []

        candidate = current + [block]
        if current and _group_len(candidate) > config.parent_chunk_target_chars and block.block_type != "table":
            groups.append(current)
            current = [block]
            current_title_level = None
        else:
            current = candidate

    if current:
        groups.append(current)
    return groups


def _split_group(group: list[DocumentBlock], config: ChunkingConfig) -> list[list[DocumentBlock]]:
    if _group_len(group) <= config.parent_chunk_max_chars:
        return [group]

    split: list[list[DocumentBlock]] = []
    current: list[DocumentBlock] = []
    title_prefix = [block for block in group[:1] if block.block_type == "title"]

    for block in group:
        if len(block.text) > config.parent_chunk_max_chars:
            if current:
                split.append(current)
                current = []
            for text in _split_long_block_text(block.text, config.parent_chunk_max_chars, block.block_type == "table"):
                split.append([_clone_block(block, text)])
            continue

        candidate = current + [block]
        if current and _group_len(candidate) > config.parent_chunk_max_chars:
            split.append(current)
            current = [*title_prefix, block] if title_prefix and block.block_type != "title" else [block]
        else:
            current = candidate

    if current:
        split.append(current)
    return split


def _merge_short_groups(groups: list[list[DocumentBlock]], config: ChunkingConfig) -> list[list[DocumentBlock]]:
    if len(groups) <= 1:
        return groups
    merged: list[list[DocumentBlock]] = []
    index = 0
    while index < len(groups):
        group = groups[index]
        if _group_len(group) >= config.parent_chunk_min_chars:
            merged.append(group)
            index += 1
            continue
        if index + 1 < len(groups) and _group_len(group + groups[index + 1]) <= config.parent_chunk_max_chars:
            merged.append(group + groups[index + 1])
            index += 2
            continue
        if merged and _group_len(merged[-1] + group) <= config.parent_chunk_max_chars:
            merged[-1] = merged[-1] + group
        else:
            merged.append(group)
        index += 1
    return merged


def _split_long_block_text(text: str, max_chars: int, is_table: bool) -> list[str]:
    if is_table:
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) <= 2:
            return _split_sentences(text, max_chars)
        header = lines[0]
        parts: list[str] = []
        current = header
        for line in lines[1:]:
            candidate = f"{current}\n{line}"
            if len(candidate) <= max_chars:
                current = candidate
            else:
                parts.append(current)
                current = f"{header}\n{line}"
        if current:
            parts.append(current)
        return parts
    return _split_sentences(text, max_chars)


def _split_sentences(text: str, max_chars: int) -> list[str]:
    sentences = [part for part in re.split(r"(?<=[。！？.!?])\s*", text) if part.strip()]
    if len(sentences) <= 1:
        return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
        elif len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            parts.append(current)
            current = sentence
    if current:
        parts.append(current)
    return parts


def _clone_block(block: DocumentBlock, text: str) -> DocumentBlock:
    return DocumentBlock(
        block_id=block.block_id,
        text=text,
        block_type=block.block_type,
        page_number=block.page_number,
        order_index=block.order_index,
        level=block.level,
        metadata=block.metadata,
    )


def _group_len(group: Sequence[DocumentBlock]) -> int:
    return len(_join_blocks(group))


def _join_blocks(group: Sequence[DocumentBlock]) -> str:
    return "\n\n".join(block.text.strip() for block in group if block.text.strip())


def _section_path(group: Sequence[DocumentBlock]) -> list[str]:
    for block in group:
        path = block.metadata.get("section_path")
        if isinstance(path, list) and path:
            return [str(item) for item in path]
    return []
