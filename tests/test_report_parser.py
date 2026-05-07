import json

import pytest

from fundinsight.report_parser import parse_report_output
from tests.test_report_agent import _chart_specs_payload
from tests.test_report_guard import valid_v02_report


def test_parse_report_output_extracts_markdown_and_chart_specs() -> None:
    raw_output = (
        "<report_markdown>\n"
        + valid_v02_report()
        + "\n</report_markdown>\n"
        + "<chart_specs_json>\n"
        + json.dumps(_chart_specs_payload(), ensure_ascii=False)
        + "\n</chart_specs_json>"
    )

    parsed = parse_report_output(raw_output)

    assert parsed.report_markdown.startswith("# 示例稳健成长混合基金")
    assert len(parsed.chart_specs) == 6


def test_parse_report_output_rejects_missing_tags() -> None:
    with pytest.raises(ValueError, match="report_markdown"):
        parse_report_output("<chart_specs_json>[]</chart_specs_json>")


def test_parse_report_output_accepts_fenced_chart_json() -> None:
    raw_output = (
        "<report_markdown>\n"
        + valid_v02_report()
        + "\n</report_markdown>\n"
        + "<chart_specs_json>\n```json\n"
        + json.dumps(_chart_specs_payload(), ensure_ascii=False)
        + "\n```\n</chart_specs_json>"
    )

    parsed = parse_report_output(raw_output)

    assert len(parsed.chart_specs) == 6
