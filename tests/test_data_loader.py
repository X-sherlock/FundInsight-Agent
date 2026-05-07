from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_load_sample_fund_metrics() -> None:
    fund_metrics = load_fund_metrics(SAMPLE_INPUT)

    assert fund_metrics.fund.code == "000001"
    assert fund_metrics.fund.name == "示例稳健成长混合基金"
    assert fund_metrics.metrics.performance.return_1y == 0.126
    assert fund_metrics.data_quality.missing_fields == [
        "peer_percentile_1y",
        "quarterly_holding_details",
    ]


def test_load_fund_metrics_rejects_invalid_shape(tmp_path: Path) -> None:
    invalid_input = tmp_path / "invalid.json"
    invalid_input.write_text('{"fund": {"code": "000001"}}', encoding="utf-8")

    with pytest.raises(ValueError, match="schema validation"):
        load_fund_metrics(invalid_input)
