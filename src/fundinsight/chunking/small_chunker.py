"""Build small retrieval chunks from parent chunks."""

from __future__ import annotations

import re
from collections.abc import Sequence

from fundinsight.chunking.config import ChunkingConfig
from fundinsight.chunking.context_header import build_context_header
from fundinsight.chunking.models import DocumentBlock, ParentChunk, SmallChunk


def build_small_chunks(parent: ParentChunk, config: ChunkingConfig | None = None) -> list[SmallChunk]:
    resolved_config = config or ChunkingConfig()
    resolved_config.validate()
    units = _units_from_parent(parent, resolved_config)
    grouped = _group_units(units, resolved_config)
    grouped = _merge_short_units(grouped, resolved_config)

    chunks: list[SmallChunk] = []
    previous_raw = ""
    for index, unit_group in enumerate(grouped):
        raw_text = "\n\n".join(unit_group).strip()
        if not raw_text:
            continue
        if previous_raw and resolved_config.small_chunk_overlap_chars:
            overlap = _overlap_text(previous_raw, resolved_config.small_chunk_overlap_chars)
            if overlap and overlap not in raw_text[: len(overlap) + 20]:
                raw_for_embedding = f"{overlap}\n\n{raw_text}"
            else:
                raw_for_embedding = raw_text
        else:
            raw_for_embedding = raw_text
        header = build_context_header(parent)
        embedding_text = f"{header}\n正文：\n{raw_for_embedding}" if header else raw_for_embedding
        chunks.append(
            SmallChunk(
                chunk_id=f"{parent.parent_chunk_id}_small_{len(chunks):03d}",
                parent_chunk_id=parent.parent_chunk_id,
                material_id=parent.material_id,
                fund_code=parent.fund_code,
                raw_text=raw_text,
                embedding_text=embedding_text,
                chunk_index=parent.chunk_index * 1000 + len(chunks),
                chunk_index_in_parent=len(chunks),
                section_path=parent.section_path,
                page_start=parent.page_start,
                page_end=parent.page_end,
                metadata={**parent.metadata, "chunk_level": "small"},
            )
        )
        previous_raw = raw_text
    return chunks


def _units_from_parent(parent: ParentChunk, config: ChunkingConfig) -> list[str]:
    units: list[str] = []
    for block in parent.blocks:
        if block.block_type == "table":
            units.extend(_split_table(block.text, config.small_chunk_max_chars))
        elif len(block.text) > config.small_chunk_max_chars:
            units.extend(_split_sentences(block.text, config.small_chunk_max_chars))
        else:
            units.append(block.text)

    if len(units) >= 2 and _looks_like_title(units[0]):
        units[1] = f"{units[0]}\n\n{units[1]}"
        units = units[1:]
    return units or [parent.text]


def _group_units(units: Sequence[str], config: ChunkingConfig) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for unit in units:
        candidate = current + [unit]
        if current and len("\n\n".join(candidate)) > config.small_chunk_target_chars:
            groups.append(current)
            current = [unit]
        else:
            current = candidate
    if current:
        groups.append(current)
    return groups


def _merge_short_units(groups: list[list[str]], config: ChunkingConfig) -> list[list[str]]:
    if len(groups) <= 1:
        return groups
    merged: list[list[str]] = []
    for group in groups:
        if not merged:
            merged.append(group)
            continue
        candidate = merged[-1] + group
        current_len = len("\n\n".join(group))
        if current_len < config.small_chunk_min_chars and len("\n\n".join(candidate)) <= config.small_chunk_max_chars:
            merged[-1] = candidate
        else:
            merged.append(group)
    return merged


def _split_table(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
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


def _overlap_text(text: str, overlap_chars: int) -> str:
    if len(text) <= overlap_chars:
        return text
    tail = text[-overlap_chars:]
    sentence_start = max(tail.rfind("。"), tail.rfind("."), tail.rfind("\n"))
    if sentence_start > 0 and sentence_start + 1 < len(tail):
        return tail[sentence_start + 1 :].strip()
    return tail.strip()


def _looks_like_title(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return len(compact) <= 40 and not re.search(r"[。！？.!?；;]$", compact)
