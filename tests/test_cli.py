import json
from pathlib import Path
from types import SimpleNamespace

from fundinsight import cli
from fundinsight.models import ChartSeries, ChartSpec
from fundinsight.report_guard import GuardResult


def test_cli_report_writes_report_and_chart_specs(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "000001_report.md"
    chart_output_path = tmp_path / "000001_chart_specs.json"

    class FakeReportAgent:
        def generate_report(self, input_path: str):
            return SimpleNamespace(
                markdown="# report\n\ncontent",
                chart_specs=[
                    ChartSpec(
                        id="returns_by_period",
                        title="多周期收益表现",
                        type="bar",
                        description="展示收益。",
                        source_fields=["metrics.performance.return_1y"],
                        series=[
                            ChartSeries(
                                name="基金收益",
                                values=[{"period": "1Y", "value": 0.126}],
                            )
                        ],
                        notes=["样例"],
                    )
                ],
                guard_result=GuardResult(tuple()),
            )

    monkeypatch.setattr(cli, "ReportAgent", FakeReportAgent)

    exit_code = cli.main(
        [
            "report",
            "--input",
            "data/sample/fund_metrics.json",
            "--output",
            str(output_path),
            "--chart-output",
            str(chart_output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.read_text(encoding="utf-8") == "# report\n\ncontent"
    chart_payload = json.loads(chart_output_path.read_text(encoding="utf-8"))
    assert chart_payload["charts"][0]["id"] == "returns_by_period"
