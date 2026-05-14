"""Structure detection for heterogeneous research material text."""

from __future__ import annotations

import re
from collections.abc import Iterable

from fundinsight.chunking.config import ChunkingConfig
from fundinsight.chunking.models import DocumentBlock
from fundinsight.research_loader import normalize_research_content


_NUMBERED_TITLE_RE = re.compile(
    r"^((第[一二三四五六七八九十百千万\d]+[章节部分])|([一二三四五六七八九十]+、)|(\([一二三四五六七八九十\d]+\))|(（[一二三四五六七八九十\d]+）)|(\d+(\.\d+)*[\.、\s]))"
)
_SENTENCE_END_RE = re.compile(r"[。！？.!?；;]$")
_TABLE_SEPARATOR_RE = re.compile(r"(\t|\s{2,}|\|)")
_NUMERIC_TOKEN_RE = re.compile(r"[-+]?\d+(?:\.\d+)?%?")
_LIST_RE = re.compile(r"^(([-*•])|(\d+[.)、])|([一二三四五六七八九十]+[.)、]))\s*")


def build_document_blocks(content: str, config: ChunkingConfig | None = None) -> list[DocumentBlock]:
    """Convert raw or normalized text into ordered, lightly typed document blocks."""

    resolved_config = config or ChunkingConfig()
    resolved_config.validate()
    pages = _split_pages(content)
    blocks: list[DocumentBlock] = []
    order_index = 0
    for page_number, page_text in enumerate(pages, start=1):
        for block_text in _page_blocks(page_text, resolved_config):
            stripped = block_text.strip()
            if not stripped:
                continue
            block_type = _classify_block(stripped, resolved_config)
            level = _infer_title_level(stripped) if block_type == "title" else None
            section_path = _section_path_for_next_block(blocks, stripped, level) if block_type == "title" else None
            metadata = {"title_score": _title_score(stripped)} if block_type == "title" else {}
            if section_path:
                metadata["section_path"] = section_path
            blocks.append(
                DocumentBlock(
                    block_id=f"block_{order_index:05d}",
                    text=stripped,
                    block_type=block_type,
                    page_number=page_number,
                    order_index=order_index,
                    level=level,
                    metadata=metadata,
                )
            )
            order_index += 1
    return _attach_section_paths(blocks)


def _split_pages(content: str) -> list[str]:
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    pages = [page for page in re.split(r"\f+|\n\s*-{0,3}\s*page\s+\d+\s*-{0,3}\s*\n", text, flags=re.IGNORECASE) if page.strip()]
    return pages or [text]


def _page_blocks(page_text: str, config: ChunkingConfig) -> Iterable[str]:
    normalized = normalize_research_content(page_text)
    if not normalized:
        return []

    output: list[str] = []
    paragraph_lines: list[str] = []
    table_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            output.append("\n".join(paragraph_lines).strip())
            paragraph_lines = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            if len(table_lines) >= config.table_min_consecutive_lines:
                output.append("\n".join(table_lines).strip())
            else:
                paragraph_lines.extend(table_lines)
            table_lines = []

    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            flush_table()
            flush_paragraph()
            continue
        if _looks_like_table_line(line):
            flush_paragraph()
            table_lines.append(line)
            continue
        flush_table()
        if _title_score(line) >= config.title_score_threshold:
            flush_paragraph()
            output.append(line)
        else:
            paragraph_lines.append(line)

    flush_table()
    flush_paragraph()
    return output


def _classify_block(text: str, config: ChunkingConfig) -> str:
    if _looks_like_table_text(text):
        return "table"
    if _title_score(text) >= config.title_score_threshold:
        return "title"
    if _LIST_RE.match(text):
        return "list"
    return "paragraph"


def _title_score(text: str) -> float:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return 0.0
    line_count = len([line for line in text.splitlines() if line.strip()])
    score = 0.0
    if line_count == 1:
        score += 0.8
    if len(compact) <= 32:
        score += 0.9
    elif len(compact) <= 60:
        score += 0.4
    if _NUMBERED_TITLE_RE.match(compact):
        score += 1.2
    if not _SENTENCE_END_RE.search(compact):
        score += 0.5
    if len(_NUMERIC_TOKEN_RE.findall(compact)) <= 1:
        score += 0.2
    if _looks_like_table_text(text):
        score -= 1.2
    if len(compact) > 90:
        score -= 1.0
    return score


def _infer_title_level(text: str) -> int:
    compact = re.sub(r"\s+", "", text)
    if re.match(r"^第[一二三四五六七八九十百千万\d]+章", compact):
        return 1
    if re.match(r"^第[一二三四五六七八九十百千万\d]+节", compact):
        return 2
    if re.match(r"^[一二三四五六七八九十]+、", compact):
        return 1
    if re.match(r"^[（(][一二三四五六七八九十\d]+[）)]", compact):
        return 2
    numeric = re.match(r"^(\d+(?:\.\d+)*)", compact)
    if numeric:
        return min(numeric.group(1).count(".") + 1, 4)
    return 2 if len(compact) <= 24 else 3


def _looks_like_table_text(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    return sum(1 for line in lines if _looks_like_table_line(line)) >= max(2, len(lines) // 2)


def _looks_like_table_line(line: str) -> bool:
    if "|" in line or "\t" in line:
        return True
    if not _TABLE_SEPARATOR_RE.search(line):
        return False
    tokens = [token for token in re.split(r"\s{2,}|\t|\|", line.strip()) if token]
    if len(tokens) < 3:
        return False
    numeric_ratio = len(_NUMERIC_TOKEN_RE.findall(line)) / max(len(tokens), 1)
    return numeric_ratio >= 0.3 or len(tokens) >= 4


def _section_path_for_next_block(blocks: list[DocumentBlock], text: str, level: int | None) -> list[str]:
    if level is None:
        return [text]
    path: list[str] = []
    for block in reversed(blocks):
        if block.block_type != "title" or block.level is None:
            continue
        if block.level < level:
            previous_path = block.metadata.get("section_path")
            if isinstance(previous_path, list):
                path.extend(str(item) for item in previous_path)
            else:
                path.append(block.text)
            break
    path.append(text)
    return path[-6:]


def _attach_section_paths(blocks: list[DocumentBlock]) -> list[DocumentBlock]:
    title_stack: list[DocumentBlock] = []
    attached: list[DocumentBlock] = []
    for block in blocks:
        if block.block_type == "title":
            level = block.level or 2
            title_stack = [item for item in title_stack if (item.level or 2) < level]
            title_stack.append(block)
            path = [item.text for item in title_stack]
            attached.append(_replace_metadata(block, {"section_path": path}))
            continue
        path = [item.text for item in title_stack]
        attached.append(_replace_metadata(block, {"section_path": path}))
    return attached


def _replace_metadata(block: DocumentBlock, values: dict[str, object]) -> DocumentBlock:
    metadata = {**block.metadata, **values}
    return DocumentBlock(
        block_id=block.block_id,
        text=block.text,
        block_type=block.block_type,
        page_number=block.page_number,
        order_index=block.order_index,
        level=block.level,
        metadata=metadata,
    )
