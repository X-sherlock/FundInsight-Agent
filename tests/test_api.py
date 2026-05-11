from pathlib import Path

from fastapi.testclient import TestClient

from fundinsight.api import create_app
from fundinsight.fund_repository import FundRepository
from fundinsight.report_store import ReportStore
from fundinsight.report_tasks import ReportTaskManager
from fundinsight.research_models import ResearchFusionContext
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore
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


def test_api_ensure_supports_research_options(tmp_path: Path) -> None:
    client = _client(tmp_path)

    ensure = client.post(
        "/api/reports/ensure",
        json={
            "fund_code": "000001",
            "force_regenerate": True,
            "include_research": True,
            "research_material_ids": ["mat_1"],
            "force_reextract": True,
        },
    )

    assert ensure.status_code == 200
    task = client.get(f"/api/report-tasks/{ensure.json()['task_id']}")
    assert task.status_code == 200
    assert task.json()["include_research"] is True
    assert task.json()["research_material_ids"] == ["mat_1"]
    assert task.json()["force_reextract"] is True


def test_api_lists_and_creates_research_materials(tmp_path: Path) -> None:
    client = _client(tmp_path)

    empty = client.get("/api/funds/000001/research-materials")
    created = client.post(
        "/api/funds/000001/research-materials",
        json={
            "title": "research note",
            "content": "Fund 000001 research material body.",
            "source_type": "report",
            "source_name": "Research Desk",
            "publish_date": "2026-05-01",
        },
    )
    listed = client.get("/api/funds/000001/research-materials")

    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert created.status_code == 200
    assert created.json()["fund_code"] == "000001"
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1
    assert "content" not in listed.json()["items"][0]
    assert listed.json()["items"][0]["title"] == "research note"


def test_api_rejects_invalid_research_material_payload(tmp_path: Path) -> None:
    client = _client(tmp_path)

    empty_content = client.post(
        "/api/funds/000001/research-materials",
        json={"title": "research note", "content": "  ", "source_type": "report"},
    )
    invalid_source_type = client.post(
        "/api/funds/000001/research-materials",
        json={"title": "research note", "content": "body", "source_type": "blog"},
    )

    assert empty_content.status_code == 400
    assert empty_content.json()["detail"]["code"] == "INVALID_RESEARCH_MATERIAL"
    assert "content" in empty_content.json()["detail"]["message"]
    assert invalid_source_type.status_code == 400
    assert invalid_source_type.json()["detail"]["code"] == "INVALID_RESEARCH_MATERIAL"
    assert "source_type" in invalid_source_type.json()["detail"]["message"]


def test_api_deduplicates_research_material_content_hash(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {
        "title": "research note",
        "content": "Same research material body.",
        "source_type": "news",
    }

    first = client.post("/api/funds/000001/research-materials", json=payload)
    second = client.post("/api/funds/000001/research-materials", json={**payload, "title": "other title"})
    listed = client.get("/api/funds/000001/research-materials")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["material_id"] == first.json()["material_id"]
    assert len(listed.json()["items"]) == 1


def test_api_deletes_research_materials(tmp_path: Path) -> None:
    client = _client(tmp_path)
    created = client.post(
        "/api/funds/000001/research-materials",
        json={"title": "research note", "content": "body", "source_type": "announcement"},
    )
    material_id = created.json()["material_id"]

    deleted = client.delete(f"/api/funds/000001/research-materials/{material_id}")
    missing = client.delete(f"/api/funds/000001/research-materials/{material_id}")

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "RESEARCH_MATERIAL_NOT_FOUND"


def test_api_research_context_prefers_report_context(tmp_path: Path) -> None:
    client, report_store = _client_with_store(tmp_path)
    report_store.fund_report_dir("000001").mkdir(parents=True, exist_ok=True)
    report_store.research_context_path("000001").write_text(
        (
            '{"fund_code":"000001","positive_factors":[{"summary":"from report"}],'
            '"risk_notices":[],"key_events":[],"view_changes":[],"source_materials":[]}'
        ),
        encoding="utf-8",
    )

    response = client.get("/api/funds/000001/research-context")

    assert response.status_code == 200
    assert response.json()["positive_factors"][0]["summary"] == "from report"


def test_api_research_context_falls_back_to_fusion_context(tmp_path: Path) -> None:
    client, _, research_store = _client_with_research_store(tmp_path)
    research_store.save_fusion_context("000001", ResearchFusionContext(fund_code="000001"))

    response = client.get("/api/funds/000001/research-context")

    assert response.status_code == 200
    assert response.json()["fund_code"] == "000001"
    assert response.json()["positive_factors"] == []


def test_api_research_context_returns_empty_context_when_missing(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/funds/000001/research-context")

    assert response.status_code == 200
    assert response.json()["fund_code"] == "000001"
    assert response.json()["source_materials"] == []


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
    client, report_store, _ = _client_with_research_store(tmp_path)
    return client, report_store


def _client_with_research_store(tmp_path: Path):
    fund_repository = FundRepository(funds_root=tmp_path / "funds", sample_input_path=SAMPLE_INPUT)
    report_store = ReportStore(tmp_path / "reports")
    task_store = TaskStore(report_store.reports_root)
    research_store = ResearchStore(tmp_path / "data")
    research_service = ResearchMaterialService(research_store)
    manager = ReportTaskManager(fund_repository, report_store, task_store, report_agent_factory=FakeReportAgent)
    app = create_app(
        fund_repository=fund_repository,
        report_store=report_store,
        task_store=task_store,
        task_manager=manager,
        research_material_service=research_service,
    )
    return TestClient(app), report_store, research_store


class FakeReportAgent:
    def generate_report(self, input_path: str | Path, **kwargs):
        metrics = FundRepository(sample_input_path=SAMPLE_INPUT).get_metrics("000001")
        return _report_result(metrics)
