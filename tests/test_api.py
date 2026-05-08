from pathlib import Path

from fastapi.testclient import TestClient

from fundinsight.api import create_app
from fundinsight.fund_repository import FundRepository
from fundinsight.report_store import ReportStore
from fundinsight.report_tasks import ReportTaskManager
from fundinsight.task_store import TaskStore
from tests.test_report_store import SAMPLE_INPUT, _report_result


def test_api_searches_funds_and_returns_metrics(tmp_path: Path) -> None:
    client = _client(tmp_path)

    funds = client.get("/api/funds", params={"query": "000001"})
    metrics = client.get("/api/funds/000001/metrics")

    assert funds.status_code == 200
    assert funds.json()["items"][0]["code"] == "000001"
    assert metrics.status_code == 200
    assert metrics.json()["fund"]["code"] == "000001"
    assert "performance" in metrics.json()["metrics"]


def test_api_ensure_existing_report_does_not_create_task(tmp_path: Path) -> None:
    client, report_store = _client_with_store(tmp_path)
    metrics = FundRepository(sample_input_path=SAMPLE_INPUT).get_metrics("000001")
    report_store.save_generated_report(_report_result(metrics), metrics.model_dump(mode="json"))

    response = client.post("/api/reports/ensure", json={"fund_code": "000001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "existing"
    assert payload["report_id"] == "000001"


def test_api_creates_task_and_returns_report_detail(tmp_path: Path) -> None:
    client = _client(tmp_path)

    ensure = client.post("/api/reports/ensure", json={"fund_code": "000001", "force_regenerate": True})

    assert ensure.status_code == 200
    task_id = ensure.json()["task_id"]
    task = client.get(f"/api/report-tasks/{task_id}")
    report = client.get("/api/reports/000001")

    assert task.status_code == 200
    assert task.json()["status"] == "completed"
    assert report.status_code == 200
    assert report.json()["report_id"] == "000001"


def test_api_allows_configured_cors_origin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FUNDINSIGHT_CORS_ALLOW_ORIGINS", "fundinsight-agent-web.onrender.com")
    client = _client(tmp_path)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://fundinsight-agent-web.onrender.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://fundinsight-agent-web.onrender.com"


def _client(tmp_path: Path) -> TestClient:
    client, _ = _client_with_store(tmp_path)
    return client


def _client_with_store(tmp_path: Path):
    fund_repository = FundRepository(funds_root=tmp_path / "funds", sample_input_path=SAMPLE_INPUT)
    report_store = ReportStore(tmp_path / "reports")
    task_store = TaskStore(report_store.reports_root)
    manager = ReportTaskManager(fund_repository, report_store, task_store, report_agent_factory=FakeReportAgent)
    app = create_app(
        fund_repository=fund_repository,
        report_store=report_store,
        task_store=task_store,
        task_manager=manager,
    )
    return TestClient(app), report_store


class FakeReportAgent:
    def generate_report(self, input_path: str | Path):
        metrics = FundRepository(sample_input_path=SAMPLE_INPUT).get_metrics("000001")
        return _report_result(metrics)
