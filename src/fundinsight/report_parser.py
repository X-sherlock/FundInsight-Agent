"""Parse the tagged LLM output required by the v0.2 prompt."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter, ValidationError

from fundinsight.models import ChartSpec


_TAG_PATTERN_TEMPLATE = r"<{tag}>\s*(.*?)\s*</{tag}>"


@dataclass(frozen=True)
class ParsedReportOutput:
    report_markdown: str
    chart_specs: list[ChartSpec]


def parse_report_output(raw_output: str) -> ParsedReportOutput:
    """Extract Markdown and chart specs from the LLM response."""

    if not raw_output or not raw_output.strip():
        raise ValueError("LLM output is empty.")

    markdown = _extract_tag(raw_output, "report_markdown")
    chart_specs_payload = _extract_tag(raw_output, "chart_specs_json")
    chart_specs = _parse_chart_specs(chart_specs_payload)
    return ParsedReportOutput(report_markdown=markdown, chart_specs=chart_specs)


def _extract_tag(raw_output: str, tag: str) -> str:
    pattern = _TAG_PATTERN_TEMPLATE.format(tag=re.escape(tag))
    match = re.search(pattern, raw_output, flags=re.DOTALL)
    if not match:
        raise ValueError(f"LLM output is missing <{tag}> section.")
    content = match.group(1).strip()
    if not content:
        raise ValueError(f"LLM output <{tag}> section is empty.")
    return content


def _parse_chart_specs(payload: str) -> list[ChartSpec]:
    payload = _strip_json_code_fence(payload)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("chart_specs_json is not valid JSON.") from exc

    charts_payload: Any
    if isinstance(parsed, dict) and "charts" in parsed:
        charts_payload = parsed["charts"]
    else:
        charts_payload = parsed

    try:
        return TypeAdapter(list[ChartSpec]).validate_python(charts_payload)
    except ValidationError as exc:
        raise ValueError("chart_specs_json does not match ChartSpec schema.") from exc


def _strip_json_code_fence(payload: str) -> str:
    stripped = payload.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped
