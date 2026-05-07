from pathlib import Path
from types import SimpleNamespace

from fundinsight import cli
from fundinsight.report_guard import GuardResult


def test_cli_report_writes_output(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "000001_report.md"

    class FakeReportAgent:
        def generate_report(self, input_path: str):
            return SimpleNamespace(
                markdown="# report\n\ncontent",
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
        ]
    )

    assert exit_code == 0
    assert output_path.read_text(encoding="utf-8") == "# report\n\ncontent"
