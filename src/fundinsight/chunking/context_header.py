"""Build lightweight retrieval context headers for embedding text."""

from __future__ import annotations

from typing import Any

from fundinsight.chunking.models import ParentChunk


def build_context_header(parent: ParentChunk, extra_metadata: dict[str, Any] | None = None) -> str:
    metadata = {**parent.metadata, **(extra_metadata or {})}
    section_path = " / ".join(parent.section_path)
    page_range = str(parent.page_start) if parent.page_start == parent.page_end else f"{parent.page_start}-{parent.page_end}"
    lines = [
        ("基金代码", parent.fund_code),
        ("基金名称", metadata.get("fund_name")),
        ("文档标题", metadata.get("document_title")),
        ("文档类型", metadata.get("document_type")),
        ("报告期", metadata.get("report_period")),
        ("发布日期", metadata.get("publish_date")),
        ("章节路径", section_path),
        ("页码", page_range),
    ]
    return "\n".join(f"{label}：{value}" for label, value in lines if value)
