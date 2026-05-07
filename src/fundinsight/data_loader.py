"""Local JSON loading and validation for fund metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fundinsight.models import FundMetricsInput


def load_json(path: str | Path) -> dict[str, Any]:
    """Read a local JSON object from disk."""

    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input file is not valid JSON: {input_path}") from exc

    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object at the top level.")
    return data


def load_fund_metrics(path: str | Path) -> FundMetricsInput:
    """Read and validate a fund metrics JSON file."""

    data = load_json(path)
    try:
        return FundMetricsInput.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Fund metrics input failed schema validation: {exc}") from exc
