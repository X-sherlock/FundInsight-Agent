from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics
from fundinsight.fund_repository import FundRepository


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_load_sample_fund_metrics() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)

    assert fund_metrics.fund.code == "000001"
    assert fund_metrics.fund.name == "示例稳健成长混合基金"
    assert fund_metrics.metrics.performance.return_1y == 0.126
    assert fund_metrics.metrics.excess_return.excess_return_1y == 0.035
    assert fund_metrics.peer_summary is not None
    assert fund_metrics.peer_summary.peer_rank_percentile == 0.32
    assert fund_metrics.resolved_benchmark.name == "沪深300指数"
    assert fund_metrics.data_quality.missing_fields == [
        "quarterly_holding_details",
        "daily_nav_series",
        "full_peer_distribution",
    ]


def test_load_fund_metrics_rejects_invalid_shape(tmp_path: Path) -> None:
    invalid_input = tmp_path / "invalid.json"
    invalid_input.write_text('{"fund": {"code": "000001"}}', encoding="utf-8")

    with pytest.raises(ValueError, match="schema validation"):
        load_fund_metrics(invalid_input)


def test_default_repository_lists_synthetic_sample_funds() -> None:
    funds = FundRepository().list_funds()
    codes = {fund.code for fund in funds}

    assert {"000001", "000002", "000003", "000004", "000005"}.issubset(codes)
