"""Guard checks for generated Markdown reports."""

from __future__ import annotations

import re
from dataclasses import dataclass


REQUIRED_SECTIONS = (
    "## 1. 报告说明",
    "## 2. 基金基本信息",
    "## 3. 核心指标概览",
    "## 4. 收益表现分析",
    "## 5. 风险与回撤分析",
    "## 6. 风险调整后表现",
    "## 7. 基准与同类对照",
    "## 8. 管理人与运作观察",
    "## 9. 数据缺口与解读限制",
    "## 10. 非投资建议声明",
)

PROHIBITED_PATTERNS = (
    r"建议\s*(买入|卖出|持有|加仓|减仓|清仓|建仓|抄底|止盈|止损)",
    r"(推荐|应当|应该|可以|可考虑)\s*(买入|卖出|持有|加仓|减仓|清仓|建仓|抄底|止盈|止损)",
    r"(适合购买|不适合购买|适合重仓|仓位建议|配置比例建议|建议配置比例)",
    r"(未来收益将|预计收益|必然上涨|必然下跌|保证收益|稳赚|无风险|确定跑赢|一定跑输)",
)


@dataclass(frozen=True)
class GuardIssue:
    code: str
    message: str


@dataclass(frozen=True)
class GuardResult:
    issues: tuple[GuardIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


def check_report(report_markdown: str) -> GuardResult:
    """Check obvious safety and formatting issues without judging fund quality."""

    issues: list[GuardIssue] = []
    if not report_markdown or not report_markdown.strip():
        issues.append(GuardIssue("empty_report", "Report is empty."))
        return GuardResult(tuple(issues))

    stripped = report_markdown.strip()
    if len(stripped) < 100:
        issues.append(GuardIssue("too_short", "Report is too short to be a complete analysis."))

    for section in REQUIRED_SECTIONS:
        if section not in stripped:
            issues.append(
                GuardIssue("missing_section", f"Required section is missing: {section}")
            )

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, stripped):
            issues.append(
                GuardIssue(
                    "prohibited_expression",
                    f"Report contains prohibited expression matching: {pattern}",
                )
            )

    return GuardResult(tuple(issues))
