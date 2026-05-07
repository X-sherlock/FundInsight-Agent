"""Guard checks for generated Markdown reports."""

from __future__ import annotations

import re
from dataclasses import dataclass

from fundinsight.models import ChartSpec
from fundinsight.report_quality import check_report_depth


REQUIRED_SECTIONS = (
    "## 1. 报告说明",
    "## 2. 核心结论",
    "## 3. 基金基本信息",
    "## 4. 关键指标总览",
    "## 5. 收益分析",
    "## 6. 收益质量分析",
    "## 7. 风险控制分析",
    "## 8. 同类竞争力分析",
    "## 9. 基准比较分析",
    "## 10. 图表解读",
    "## 11. 主要优势",
    "## 12. 主要风险",
    "## 13. 适合关注的场景",
    "## 14. 数据局限性",
    "## 15. 风险提示",
)

PROHIBITED_RECOMMENDATION_PATTERNS = (
    r"(买入|卖出|持有|加仓|减仓|清仓|建仓|抄底|止盈|止损)",
    r"(仓位建议|仓位配置建议|配置比例建议|建议配置比例|适合购买|不适合购买)",
    r"(核心配置|底仓配置|组合配置|适合作为.*配置|作为.*配置之一|配置为.*核心)",
)

PROHIBITED_PREDICTION_PATTERNS = (
    r"(未来收益将|预计收益|必然上涨|必然下跌|保证收益|承诺收益|稳赚|无风险|确定跑赢|一定跑赢)",
)

NEGATED_BOUNDARY_MARKERS = (
    "不",
    "不得",
    "不能",
    "不会",
    "无法",
    "并非",
    "并不",
    "未",
    "非",
    "不是",
    "不构成",
    "不代表",
    "不保证",
    "不承诺",
    "不含",
    "不提供",
    "不涉及",
    "避免",
    "禁止",
)

ALLOWED_TERMS = (
    "无风险利率",
    "无风险收益率",
    "持仓",
    "持有者",
    "长期持有者",
    "持有人",
    "持有期",
    "持有份额",
    "股票配置比例",
    "债券配置比例",
    "现金配置比例",
    "资产配置结构",
    "适合关注的场景",
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
    if len(stripped) < 800:
        issues.append(GuardIssue("too_short", "Report is too short to be a complete v0.2 analysis."))

    for section in REQUIRED_SECTIONS:
        if section not in stripped:
            issues.append(GuardIssue("missing_section", f"Required section is missing: {section}"))

    _check_chart_placeholders(stripped, issues)
    _check_required_metric_language(stripped, issues)
    _check_prohibited_patterns(stripped, issues)

    for quality_issue in check_report_depth(stripped):
        issues.append(GuardIssue(quality_issue.code, quality_issue.message))

    return GuardResult(tuple(issues))


def check_chart_specs(report_markdown: str, chart_specs: list[ChartSpec]) -> GuardResult:
    """Check that chart JSON can support the Markdown placeholders."""

    issues: list[GuardIssue] = []
    placeholder_ids = _extract_chart_placeholder_ids(report_markdown)
    spec_ids = [chart.id for chart in chart_specs]

    if not chart_specs:
        return GuardResult((GuardIssue("missing_chart_specs", "chart_specs_json is empty."),))

    duplicated_ids = sorted({chart_id for chart_id in spec_ids if spec_ids.count(chart_id) > 1})
    for chart_id in duplicated_ids:
        issues.append(GuardIssue("duplicate_chart_spec", f"Duplicate chart spec id: {chart_id}"))

    missing_specs = sorted(set(placeholder_ids) - set(spec_ids))
    for chart_id in missing_specs:
        issues.append(
            GuardIssue(
                "missing_chart_spec",
                f"Markdown chart placeholder has no matching chart spec: {chart_id}",
            )
        )

    unused_specs = sorted(set(spec_ids) - set(placeholder_ids))
    for chart_id in unused_specs:
        issues.append(
            GuardIssue(
                "unused_chart_spec",
                f"chart_specs_json contains id not used by Markdown placeholders: {chart_id}",
            )
        )

    for chart in chart_specs:
        if not chart.source_fields:
            issues.append(GuardIssue("invalid_chart_spec", f"Chart has no source fields: {chart.id}"))
        if not chart.series:
            issues.append(GuardIssue("invalid_chart_spec", f"Chart has no series: {chart.id}"))
        if not chart.encoding.model_dump(exclude_none=True):
            issues.append(
                GuardIssue("invalid_chart_spec", f"Chart has no encoding metadata: {chart.id}")
            )
        if not chart.x_axis:
            issues.append(GuardIssue("invalid_chart_spec", f"Chart has no x_axis: {chart.id}"))
        if chart.type != "pie" and not chart.y_axis:
            issues.append(GuardIssue("invalid_chart_spec", f"Chart has no y_axis: {chart.id}"))
        if not chart.value_unit:
            issues.append(GuardIssue("invalid_chart_spec", f"Chart has no value_unit: {chart.id}"))
        if not any(
            value
            for series in chart.series
            for point in series.values
            for value in point.values()
            if value is not None
        ):
            issues.append(
                GuardIssue("invalid_chart_spec", f"Chart has no non-null data values: {chart.id}")
            )

    return GuardResult(tuple(issues))


def _check_chart_placeholders(text: str, issues: list[GuardIssue]) -> None:
    chart_matches = list(_iter_chart_placeholders(text))
    if len(chart_matches) < 5:
        issues.append(
            GuardIssue(
                "too_few_chart_placeholders",
                "Report must contain at least 5 chart placeholders.",
            )
        )
        return

    for index, match in enumerate(chart_matches):
        chart_id = match.group(1)
        next_chart_start = (
            chart_matches[index + 1].start()
            if index + 1 < len(chart_matches)
            else len(text)
        )
        next_heading_start = text.find("\n## ", match.end(), next_chart_start)
        next_start = next_heading_start if next_heading_start >= 0 else next_chart_start
        interpretation = text[match.end() : next_start].strip()
        if not _has_chart_interpretation(interpretation):
            issues.append(
                GuardIssue(
                    "missing_chart_interpretation",
                    f"Chart placeholder lacks nearby interpretation: {chart_id}",
                )
            )


def _extract_chart_placeholder_ids(text: str) -> list[str]:
    return [match.group(1) for match in _iter_chart_placeholders(text)]


def _iter_chart_placeholders(text: str) -> list[re.Match[str]]:
    return list(re.finditer(r"<!--\s*chart:\s*([a-zA-Z0-9_-]+)\s*-->", text))


def _has_chart_interpretation(text: str) -> bool:
    if not text:
        return False
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    if not cleaned:
        return False
    interpretation_terms = (
        "解读",
        "说明",
        "展示",
        "呈现",
        "观察",
        "反映",
        "体现",
        "对比",
        "用于",
        "该图",
        "图中",
        "可见",
        "可以看到",
    )
    if any(term in cleaned for term in interpretation_terms):
        return True
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", cleaned)
    return len(cjk_chars) >= 20


def _check_required_metric_language(text: str, issues: list[GuardIssue]) -> None:
    required_term_groups = (
        (
            "收益分析",
            (
                ("基金收益", "本基金收益", "基金收益率", "基金回报", "本基金回报"),
                ("基准收益", "业绩比较基准", "基准收益率", "比较基准"),
                ("超额收益", "相对基准收益", "相对收益", "超额回报"),
            ),
        ),
        (
            "风险控制分析",
            (
                ("最大回撤", "回撤"),
                ("波动率", "波动水平", "年化波动"),
                ("夏普", "Sharpe", "sharpe_1y"),
            ),
        ),
        (
            "同类竞争力分析",
            (
                ("peer_rank_percentile", "同类分位", "同类排名", "同类百分位"),
            ),
        ),
    )
    for section_name, term_groups in required_term_groups:
        if not all(any(term in text for term in group) for group in term_groups):
            issues.append(
                GuardIssue(
                    "missing_required_metric_discussion",
                    f"Report should discuss {section_name} with required metric language.",
                )
            )

    if not any(term in text for term in ("数据局限", "数据限制", "局限性", "缺少", "缺失")):
        issues.append(GuardIssue("missing_data_limitations", "Report must include data limitations."))


def _check_prohibited_patterns(text: str, issues: list[GuardIssue]) -> None:
    for pattern in PROHIBITED_RECOMMENDATION_PATTERNS + PROHIBITED_PREDICTION_PATTERNS:
        match_context = _find_non_negated_match_context(pattern, text)
        if match_context:
            issues.append(
                GuardIssue(
                    "prohibited_expression",
                    "Report contains prohibited expression matching: "
                    f"{pattern}; context: {match_context}",
                )
            )


def _find_non_negated_match_context(pattern: str, text: str) -> str | None:
    for match in re.finditer(pattern, text):
        context = text[max(0, match.start() - 35) : match.end() + 35]
        if _is_allowed_non_advisory_match(match.group(0), context):
            continue

        prefix = _same_sentence_prefix(text, match.start())
        if not any(marker in prefix for marker in NEGATED_BOUNDARY_MARKERS):
            return " ".join(context.split())
    return None


def _is_allowed_non_advisory_match(matched_text: str, context: str) -> bool:
    if matched_text in {"无风险"}:
        return any(term in context for term in ("无风险利率", "无风险收益率"))
    if matched_text == "持有":
        return any(
            term in context
            for term in ("持有者", "长期持有者", "持有人", "持有期", "持有份额")
        )
    if matched_text in {"配置比例", "仓位"}:
        return any(
            term in context
            for term in (
                "股票配置比例",
                "债券配置比例",
                "现金配置比例",
                "资产配置结构",
            )
        )
    return False


def _same_sentence_prefix(text: str, match_start: int) -> str:
    prefix_start = max(0, match_start - 35)
    for delimiter in ("。", "；", "，", "\n", ";", ","):
        delimiter_index = text.rfind(delimiter, prefix_start, match_start)
        if delimiter_index >= 0:
            prefix_start = max(prefix_start, delimiter_index + 1)
    return text[prefix_start:match_start]
