import json
from pathlib import Path
from types import SimpleNamespace

from fundinsight import cli
from fundinsight.models import ChartSeries, ChartSpec
from fundinsight.report_guard import GuardResult


def test_cli_report_writes_report_and_chart_specs(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "000001_report.md"
    chart_output_path = tmp_path / "000001_chart_specs.json"

    class StubReportAgent:
        def generate_report(self, input_path: str, **kwargs):
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
                fact_card=None,
                research_processing_error=None,
                include_research=kwargs.get("include_research"),
                research_used=False,
            )

    monkeypatch.setattr(cli, "ReportAgent", StubReportAgent)

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


def test_cli_report_accepts_rag_options_and_writes_fact_card(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "000001_report.md"
    fact_card_path = tmp_path / "fact_card.json"
    calls = []

    class StubReportAgent:
        def generate_report(self, input_path: str, **kwargs):
            calls.append((input_path, kwargs))
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
                fact_card={"fund_code": "000001", "retrieved_chunks": [{"chunk_id": "mat_1_0000"}]},
                research_processing_error=None,
                include_research=kwargs.get("include_research"),
                research_used=True,
            )

    monkeypatch.setattr(cli, "ReportAgent", StubReportAgent)

    exit_code = cli.main(
        [
            "report",
            "--input",
            "data/sample/fund_metrics.json",
            "--output",
            str(output_path),
            "--include-research",
            "--research-material-id",
            "mat_1",
            "--force-reextract",
            "--fact-card-output",
            str(fact_card_path),
        ]
    )

    assert exit_code == 0
    assert calls[0][1]["include_research"] is True
    assert calls[0][1]["research_material_ids"] == ["mat_1"]
    assert calls[0][1]["force_reextract"] is True
    assert json.loads(fact_card_path.read_text(encoding="utf-8"))["fund_code"] == "000001"
