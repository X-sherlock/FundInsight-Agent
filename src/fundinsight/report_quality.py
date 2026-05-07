"""Lightweight report depth checks that avoid fund-quality judgment."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class QualityIssue:
    code: str
    message: str


def check_report_depth(report_markdown: str) -> tuple[QualityIssue, ...]:
    """Check whether the report has enough analytical structure.

    This module checks writing depth signals only. It does not classify whether
    a fund is attractive, poor, suitable, or unsuitable.
    """

    issues: list[QualityIssue] = []
    table_count = _count_markdown_tables(report_markdown)
    if table_count < 3:
        issues.append(QualityIssue("too_few_tables", "Report should include at least 3 tables."))

    core_section = _section_text(report_markdown, "## 2. 核心结论", "## 3. 基金基本信息")
    bullet_count = sum(
        1
        for line in core_section.splitlines()
        if line.lstrip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5."))
    )
    if bullet_count < 5:
        issues.append(
            QualityIssue("too_few_core_conclusions", "Report should include at least 5 core conclusions.")
        )

    chain_terms = ("数据", "比较", "解释", "含义", "限制")
    chain_term_hits = sum(1 for term in chain_terms if term in core_section)
    if chain_term_hits < 4:
        issues.append(
            QualityIssue(
                "missing_analysis_chain_language",
                "Report should contain explicit analytical interpretation language.",
            )
        )

    if _looks_like_data_restatement(core_section):
        issues.append(
            QualityIssue(
                "data_restatement_risk",
                "Core conclusions look too close to metric restatement and need interpretation.",
            )
        )

    return tuple(issues)


def _section_text(markdown: str, start_heading: str, end_heading: str) -> str:
    start = markdown.find(start_heading)
    if start < 0:
        return ""
    end = markdown.find(end_heading, start + len(start_heading))
    if end < 0:
        return markdown[start:]
    return markdown[start:end]


def _count_markdown_tables(markdown: str) -> int:
    """Count Markdown tables by separator rows, allowing alignment markers."""

    separator_pattern = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
    return sum(1 for line in markdown.splitlines() if separator_pattern.match(line))


def _looks_like_data_restatement(text: str) -> bool:
    if not text.strip():
        return False

    conclusion_lines = [
        line
        for line in text.splitlines()
        if line.lstrip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5."))
    ]
    if not conclusion_lines:
        return False

    interpretive_terms = (
        "解释",
        "含义",
        "限制",
        "说明",
        "意味着",
        "反映",
        "提示",
        "受限",
        "观察",
        "比较",
    )
    weak_lines = [
        line
        for line in conclusion_lines
        if sum(1 for term in interpretive_terms if term in line) < 2
    ]
    return len(weak_lines) >= max(3, len(conclusion_lines) // 2 + 1)
