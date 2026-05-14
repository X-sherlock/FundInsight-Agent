"""Local report directory storage for API report retrieval."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fundinsight.api_models import FundBriefResponse
from fundinsight.models import FundMetricsInput
from fundinsight.report_agent import ReportResult
from fundinsight.report_planner import sanitize_research_context


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_ROOT = PROJECT_ROOT / "reports"


class ReportNotFoundError(LookupError):
    """Raised when a report markdown file is not available."""


class ReportStore:
    def __init__(self, reports_root: str | Path = DEFAULT_REPORTS_ROOT) -> None:
        self.reports_root = Path(reports_root)

    def report_id_for_fund(self, fund_code: str) -> str:
        return fund_code.strip()

    def fund_report_dir(self, fund_code: str) -> Path:
        return self.reports_root / "funds" / self.report_id_for_fund(fund_code)

    def report_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "report.md"

    def chart_specs_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "chart_specs.json"

    def metadata_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "metadata.json"

    def source_metrics_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "source_metrics.json"

    def research_context_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "research_context.json"

    def fact_card_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "fact_card.json"

    def source_materials_manifest_path(self, fund_code: str) -> Path:
        return self.fund_report_dir(fund_code) / "source_materials_manifest.json"

    def report_exists(self, fund_code: str) -> bool:
        return self.report_path(fund_code).is_file()

    def save_report_json(self, fund_code: str, file_name: str, payload: dict[str, Any]) -> Path:
        output_dir = self.fund_report_dir(fund_code)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / file_name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def save_generated_report(self, result: ReportResult, source_metrics: dict[str, Any]) -> str:
        fund_code = result.fund_metrics.fund.code
        output_dir = self.fund_report_dir(fund_code)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.report_path(fund_code).write_text(result.markdown, encoding="utf-8")
        self.chart_specs_path(fund_code).write_text(
            json.dumps(
                {"charts": [chart.model_dump(mode="json") for chart in result.chart_specs]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.source_metrics_path(fund_code).write_text(
            json.dumps(source_metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        research_context_payload = sanitize_research_context(result.research_context)
        fact_card_payload = result.fact_card
        if fact_card_payload is not None:
            self.fact_card_path(fund_code).write_text(
                json.dumps(fact_card_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if research_context_payload is not None:
            self.research_context_path(fund_code).write_text(
                json.dumps(research_context_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.source_materials_manifest_path(fund_code).write_text(
                json.dumps(
                    {
                        "source_materials": research_context_payload.get("source_materials", []),
                        "analyzed_materials": research_context_payload.get("analyzed_materials", []),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        elif fact_card_payload is not None:
            self.source_materials_manifest_path(fund_code).write_text(
                json.dumps(
                    {
                        "source_materials": fact_card_payload.get("source_materials", []),
                        "retrieved_chunks": fact_card_payload.get("retrieved_chunks", []),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        else:
            for stale_path in (
                self.research_context_path(fund_code),
                self.source_materials_manifest_path(fund_code),
                self.fact_card_path(fund_code),
            ):
                if stale_path.exists():
                    stale_path.unlink()
        metadata = {
            "report_id": self.report_id_for_fund(fund_code),
            "fund_code": fund_code,
            "created_at": datetime.now().astimezone().isoformat(),
            "status": "passed" if result.guard_result.passed else "warning",
            "guard_passed": result.guard_result.passed,
            "guard_issues": [
                {"code": issue.code, "message": issue.message}
                for issue in result.guard_result.issues
            ],
            "research": {
                "mode": result.research_mode,
                "materials_found": result.research_materials_found,
                "used": result.research_used,
                "material_count": result.research_material_count,
                "processing_error": result.research_processing_error,
                "included": result.include_research,
                "context_saved": research_context_payload is not None or fact_card_payload is not None,
                "fact_card_saved": fact_card_payload is not None,
            },
        }
        self.metadata_path(fund_code).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.report_id_for_fund(fund_code)

    def load_report_record(self, report_id: str) -> dict[str, Any]:
        fund_code = report_id.strip()
        if not self.report_exists(fund_code):
            raise ReportNotFoundError(f"Report does not exist: {report_id}")

        source_metrics = self._read_json(self.source_metrics_path(fund_code))
        metadata = self._read_json(self.metadata_path(fund_code))
        chart_specs = self._read_json(self.chart_specs_path(fund_code), default={"charts": []})
        research_context = self._read_json(self.research_context_path(fund_code), default={})
        fact_card = self._read_json(self.fact_card_path(fund_code), default={})
        markdown = self.report_path(fund_code).read_text(encoding="utf-8")
        fact_card = self._enrich_fact_card_with_material_interpretations(fact_card, markdown)
        metrics = FundMetricsInput.model_validate(source_metrics)
        guard_issues = metadata.get("guard_issues", [])
        guard_passed = bool(metadata.get("guard_passed", not guard_issues))

        return {
            "report_id": self.report_id_for_fund(fund_code),
            "status": "passed" if guard_passed else "warning",
            "fund": self._fund_brief(metrics),
            "as_of_date": metrics.as_of_date.isoformat(),
            "created_at": metadata.get("created_at", ""),
            "core_conclusions": self._extract_core_conclusions(markdown),
            "key_metrics": self._key_metrics(metrics),
            "markdown": markdown,
            "chart_specs": chart_specs,
            "research_context": research_context or None,
            "fact_card": fact_card or None,
            "guard_result": {"passed": guard_passed, "issues": guard_issues},
            "data_quality": {
                "missing_fields": metrics.data_quality.missing_fields,
                "notes": self._data_quality_notes(metrics),
            },
        }

    def list_report_records(self) -> list[dict[str, Any]]:
        funds_root = self.reports_root / "funds"
        if not funds_root.exists():
            return []
        records = []
        for report_path in sorted(funds_root.glob("*/report.md")):
            try:
                records.append(self.load_report_record(report_path.parent.name))
            except (ReportNotFoundError, ValueError, json.JSONDecodeError):
                continue
        return records

    def _read_json(self, path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
        if not path.exists():
            if default is not None:
                return default
            raise ReportNotFoundError(f"Report metadata is missing: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object: {path}")
        return payload

    def _fund_brief(self, metrics: FundMetricsInput) -> dict[str, str]:
        brief = FundBriefResponse(
            code=metrics.fund.code,
            name=metrics.fund.name,
            type=metrics.fund.type,
            company=metrics.fund.fund_company,
            benchmark=metrics.resolved_benchmark.name,
            as_of_date=metrics.as_of_date.isoformat(),
            category=metrics.category.name,
        )
        return brief.model_dump(mode="json")

    def _extract_core_conclusions(self, markdown: str) -> list[str]:
        match = re.search(r"##\s*2\..*?\n(?P<body>.*?)(?:\n##\s*3\.|\Z)", markdown, flags=re.DOTALL)
        if not match:
            return []
        lines = []
        for raw_line in match.group("body").splitlines():
            line = raw_line.strip()
            line = re.sub(r"^\d+[.)]\s*", "", line)
            line = re.sub(r"^[-*]\s+", "", line)
            if line:
                lines.append(line)
            if len(lines) == 5:
                break
        return lines

    def _key_metrics(self, metrics: FundMetricsInput) -> list[dict[str, str]]:
        return [
            {
                "label": "近一年收益",
                "value": self._format_percent(metrics.metrics.performance.return_1y),
                "tone": "neutral",
                "helper": "metrics.performance.return_1y",
            },
            {
                "label": "近一年超额收益",
                "value": self._format_percent(metrics.metrics.performance.excess_return_1y),
                "tone": "neutral",
                "helper": "metrics.performance.excess_return_1y",
            },
            {
                "label": "近一年波动率",
                "value": self._format_percent(metrics.metrics.risk.volatility_1y),
                "tone": "neutral",
                "helper": "metrics.risk.volatility_1y",
            },
            {
                "label": "近一年最大回撤",
                "value": self._format_percent(metrics.metrics.drawdown.max_drawdown_1y),
                "tone": "warning",
                "helper": "metrics.drawdown.max_drawdown_1y",
            },
            {
                "label": "夏普比率",
                "value": self._format_number(metrics.metrics.risk_adjusted.sharpe_1y),
                "tone": "neutral",
                "helper": "metrics.risk_adjusted.sharpe_1y",
            },
            {
                "label": "同类分位",
                "value": self._format_percent(
                    metrics.peer_summary.peer_rank_percentile if metrics.peer_summary else None
                ),
                "tone": "neutral",
                "helper": "peer_summary.peer_rank_percentile",
            },
        ]

    def _format_percent(self, value: float | None) -> str:
        if value is None:
            return "缺失"
        return f"{value * 100:.2f}%"

    def _format_number(self, value: float | None) -> str:
        if value is None:
            return "缺失"
        return f"{value:.2f}"

    def _data_quality_notes(self, metrics: FundMetricsInput) -> list[str]:
        notes = list(metrics.data_notes)
        if metrics.data_quality.notes:
            notes.insert(0, metrics.data_quality.notes)
        return notes

    def _enrich_fact_card_with_material_interpretations(
        self,
        fact_card: dict[str, Any],
        markdown: str,
    ) -> dict[str, Any]:
        chunks = fact_card.get("retrieved_chunks")
        if not isinstance(chunks, list):
            return fact_card

        interpretations = _extract_material_interpretations(markdown)
        if not interpretations:
            return fact_card

        enriched_chunks: list[Any] = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                enriched_chunks.append(chunk)
                continue
            chunk_id = str(chunk.get("chunk_id") or "")
            interpretation = interpretations.get(chunk_id)
            if interpretation is None:
                enriched_chunks.append(chunk)
                continue
            enriched_chunks.append(_fill_missing_interpretation_fields(chunk, interpretation))
        return {**fact_card, "retrieved_chunks": enriched_chunks}


def _extract_material_interpretations(markdown: str) -> dict[str, dict[str, str]]:
    """Parse the generated report's related-material section by chunk_id."""

    section = _extract_related_material_section(markdown)
    if not section:
        return {}

    heading_pattern = re.compile(
        r"^\s*(?:#{3,6}\s*)?\*\*?\s*解读\s*\d+\s*[：:]\s*(?P<title>.+?)\s*\*\*?\s*$",
        flags=re.MULTILINE,
    )
    matches = list(heading_pattern.finditer(section))
    interpretations: dict[str, dict[str, str]] = {}
    for index, match in enumerate(matches):
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        block = section[block_start:block_end]
        chunk_id = _extract_chunk_id(block)
        if not chunk_id:
            continue
        interpretation = {
            "analysis_title": _strip_markdown(match.group("title")),
            "material_summary": _extract_markdown_field(block, "材料摘要"),
            "sentiment_label": _extract_markdown_field(block, "情绪标签"),
            "evidence_excerpt": _extract_markdown_field(block, "证据原文摘录"),
        }
        interpretations[chunk_id] = {
            key: value
            for key, value in interpretation.items()
            if value
        }
    return interpretations


def _extract_related_material_section(markdown: str) -> str:
    match = re.search(
        r"^##\s*14\.\s*相关材料解读\s*\n(?P<body>.*?)(?=^##\s*\d+\.|\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group("body").strip() if match else ""


def _extract_markdown_field(block: str, field_name: str) -> str:
    pattern = re.compile(
        rf"^\s*[-*]\s*\*\*{re.escape(field_name)}\*\*\s*[：:]\s*(?P<value>.+?)\s*$",
        flags=re.MULTILINE,
    )
    match = pattern.search(block)
    return _strip_markdown(match.group("value")) if match else ""


def _extract_chunk_id(block: str) -> str:
    match = re.search(r"chunk_id\s*[：:]\s*(?P<chunk_id>[^，,；;\s)）]+)", block)
    return match.group("chunk_id").strip() if match else ""


def _strip_markdown(value: str) -> str:
    text = value.strip()
    text = re.sub(r"^\*\*", "", text)
    text = re.sub(r"\*\*$", "", text)
    return text.strip()


def _fill_missing_interpretation_fields(
    chunk: dict[str, Any],
    interpretation: dict[str, str],
) -> dict[str, Any]:
    enriched = dict(chunk)
    for field_name in ("analysis_title", "material_summary", "sentiment_label", "evidence_excerpt"):
        if not str(enriched.get(field_name) or "").strip() and interpretation.get(field_name):
            enriched[field_name] = interpretation[field_name]
    return enriched
