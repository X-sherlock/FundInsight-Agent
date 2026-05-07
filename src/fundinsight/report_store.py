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

    def report_exists(self, fund_code: str) -> bool:
        return self.report_path(fund_code).is_file()

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
        markdown = self.report_path(fund_code).read_text(encoding="utf-8")
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
            line = re.sub(r"^[-*]\s*", "", line)
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
