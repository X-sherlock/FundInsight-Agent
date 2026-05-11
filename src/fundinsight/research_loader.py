"""Utilities for loading and preparing unstructured research materials."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fundinsight.research_models import ResearchDocument, SourceType


def compute_content_hash(content: str) -> str:
    """Return a stable SHA-256 hash for material content."""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def normalize_research_content(content: str) -> str:
    """Normalize whitespace while preserving financial numbers and symbols."""

    text = content.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t\f\v]+", " ", raw_line).strip()
        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")

    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    normalized = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", normalized)


def split_research_chunks(
    content: str,
    target_min_chars: int = 800,
    target_max_chars: int = 1500,
) -> list[str]:
    """Split normalized research content into paragraph-oriented chunks."""

    if target_min_chars <= 0 or target_max_chars <= 0:
        raise ValueError("Chunk size targets must be positive.")
    if target_min_chars > target_max_chars:
        raise ValueError("target_min_chars must not exceed target_max_chars.")

    normalized = normalize_research_content(content)
    if not normalized:
        return []
    if len(normalized) <= target_max_chars:
        return [normalized]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        units.extend(_split_large_paragraph(paragraph, target_max_chars))

    chunks: list[str] = []
    current = ""
    for unit in units:
        if not current:
            current = unit
            continue

        candidate = f"{current}\n\n{unit}"
        if len(candidate) <= target_max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = unit

    if current:
        chunks.append(current)
    return chunks


def load_research_json(path: Path) -> str:
    """Read a JSON research material and extract its first-phase text body."""

    input_path = Path(path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Research JSON must be an object at the top level.")

    for field_name in ("content", "text", "body", "markdown", "article_content", "title"):
        value = payload.get(field_name)
        if isinstance(value, str) and value.strip():
            return value

    raise ValueError("Research JSON does not contain a supported text field.")


def build_research_document(
    *,
    fund_code: str,
    title: str,
    source_type: SourceType,
    content: str,
    source_name: str | None = None,
    publish_date: date | str | None = None,
    file_name: str | None = None,
    material_id: str | None = None,
    created_at: datetime | None = None,
) -> ResearchDocument:
    """Build a document metadata object from normalized material content."""

    content_hash = compute_content_hash(content)
    resolved_material_id = material_id or f"mat_{content_hash[:16]}"
    payload: dict[str, Any] = {
        "material_id": resolved_material_id,
        "fund_code": fund_code,
        "title": title,
        "source_type": source_type,
        "source_name": source_name,
        "publish_date": _parse_date(publish_date),
        "file_name": file_name,
        "content_hash": content_hash,
    }
    if created_at is not None:
        payload["created_at"] = created_at
    return ResearchDocument.model_validate(payload)


def _split_large_paragraph(paragraph: str, target_max_chars: int) -> list[str]:
    if len(paragraph) <= target_max_chars:
        return [paragraph]

    sentences = [
        part.strip()
        for part in re.split(r"(?<=[\u3002\uff01\uff1f.!?])\s*", paragraph)
        if part.strip()
    ]
    if len(sentences) <= 1:
        return [
            paragraph[index : index + target_max_chars]
            for index in range(0, len(paragraph), target_max_chars)
        ]

    units: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > target_max_chars:
            if current:
                units.append(current)
                current = ""
            units.extend(
                sentence[index : index + target_max_chars]
                for index in range(0, len(sentence), target_max_chars)
            )
            continue

        candidate = f"{current}{sentence}" if current else sentence
        if len(candidate) <= target_max_chars:
            current = candidate
        else:
            units.append(current)
            current = sentence

    if current:
        units.append(current)
    return units


def _parse_date(value: date | str | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)
