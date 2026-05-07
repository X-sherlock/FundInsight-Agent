"""Local fund metrics repository used by the API layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fundinsight.api_models import FundBriefResponse
from fundinsight.data_loader import load_json, load_fund_metrics
from fundinsight.models import FundMetricsInput


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FUNDS_ROOT = PROJECT_ROOT / "data" / "funds"
DEFAULT_SAMPLE_INPUT = PROJECT_ROOT / "data" / "sample" / "fund_metrics.json"


class FundNotFoundError(LookupError):
    """Raised when no local metrics JSON can be found for a fund code."""


class FundRepository:
    def __init__(
        self,
        funds_root: str | Path = DEFAULT_FUNDS_ROOT,
        sample_input_path: str | Path = DEFAULT_SAMPLE_INPUT,
    ) -> None:
        self.funds_root = Path(funds_root)
        self.sample_input_path = Path(sample_input_path)

    def list_funds(self, query: str = "") -> list[FundBriefResponse]:
        normalized_query = query.strip().lower()
        funds: list[FundBriefResponse] = []
        seen_codes: set[str] = set()
        for input_path in self._iter_metric_paths():
            try:
                metrics = load_fund_metrics(input_path)
            except ValueError:
                continue
            brief = self.to_fund_brief(metrics)
            if brief.code in seen_codes:
                continue
            seen_codes.add(brief.code)
            if not normalized_query or normalized_query in brief.code.lower() or normalized_query in brief.name.lower():
                funds.append(brief)
        return sorted(funds, key=lambda fund: fund.code)

    def get_metrics_path(self, fund_code: str) -> Path:
        normalized_code = fund_code.strip()
        candidate = self.funds_root / normalized_code / "metrics.json"
        if candidate.exists():
            return candidate

        if self.sample_input_path.exists():
            try:
                sample_metrics = load_fund_metrics(self.sample_input_path)
            except ValueError:
                sample_metrics = None
            if sample_metrics and sample_metrics.fund.code == normalized_code:
                return self.sample_input_path

        raise FundNotFoundError(f"Fund metrics not found for code: {normalized_code}")

    def get_metrics(self, fund_code: str) -> FundMetricsInput:
        return load_fund_metrics(self.get_metrics_path(fund_code))

    def get_raw_metrics(self, fund_code: str) -> dict[str, Any]:
        return load_json(self.get_metrics_path(fund_code))

    def get_metrics_response(self, fund_code: str) -> dict[str, Any]:
        metrics = self.get_metrics(fund_code)
        raw = self.get_raw_metrics(fund_code)
        return {
            "fund": self.to_fund_brief(metrics).model_dump(mode="json"),
            "metrics": metrics.metrics.model_dump(mode="json"),
            "raw": raw,
        }

    def to_fund_brief(self, metrics: FundMetricsInput) -> FundBriefResponse:
        return FundBriefResponse(
            code=metrics.fund.code,
            name=metrics.fund.name,
            type=metrics.fund.type,
            company=metrics.fund.fund_company,
            benchmark=metrics.resolved_benchmark.name,
            as_of_date=metrics.as_of_date.isoformat(),
            category=metrics.category.name,
        )

    def _iter_metric_paths(self) -> list[Path]:
        paths: list[Path] = []
        if self.funds_root.exists():
            paths.extend(sorted(self.funds_root.glob("*/metrics.json")))
        if self.sample_input_path.exists():
            paths.append(self.sample_input_path)
        unique_paths = []
        seen: set[Path] = set()
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen:
                unique_paths.append(path)
                seen.add(resolved)
        return unique_paths
