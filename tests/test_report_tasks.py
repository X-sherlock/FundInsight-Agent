import json
from dataclasses import replace
from datetime import date
from pathlib import Path

from fundinsight.fund_repository import FundRepository
from fundinsight.report_agent import ReportAgent
from fundinsight.report_guard import GuardIssue, GuardResult
from fundinsight.report_store import ReportStore
from fundinsight.report_tasks import ReportTaskManager
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore
from fundinsight.task_store import TaskStore
from tests.test_report_agent import FakeLLMClient, FakeResearchLLMClient, PROMPT_TEMPLATE
from tests.test_report_store import SAMPLE_INPUT, _report_result


def test_report_task_executes_and_writes_completed_report(tmp_path: Path) -> None:
    manager, task_store, report_store = _manager(tmp_path)
    response = manager.ensure_report("000001")

    assert response.mode == "created"
    assert response.task_id

    manager.execute_task(response.task_id)
    task = task_store.get(response.task_id)

    assert task.status == "completed"
    assert task.report_id == "000001"
    assert report_store.report_exists("000001")


def test_report_task_with_research_saves_context_and_manifest(tmp_path: Path) -> None:
    research_store = ResearchStore(tmp_path / "data")
    service = ResearchMaterialService(research_store)
    service.import_text_material(
        fund_code="000001",
        title="research material",
        source_type="report",
        source_name="Research Desk",
        publish_date=date(2026, 5, 1),
        content="EVIDENCE_RESEARCH appears here. FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT.",
    )
    manager, task_store, report_store = _manager(
        tmp_path,
        report_agent_factory=lambda: ReportAgent(
            llm_client=FakeLLMClient(),
            prompt_template_path=PROMPT_TEMPLATE,
            research_store=research_store,
            research_material_service=service,
            research_llm_client=FakeResearchLLMClient(),
        ),
    )

    response = manager.ensure_report("000001", force_regenerate=True, include_research=True, force_reextract=True)
    assert response.task_id
    manager.execute_task(response.task_id)

    task = task_store.get(response.task_id)
    research_context = json.loads(report_store.research_context_path("000001").read_text(encoding="utf-8"))
    manifest = json.loads(report_store.source_materials_manifest_path("000001").read_text(encoding="utf-8"))

    assert task.status == "completed"
    assert research_store.load_signal_bundle("000001") is not None
    assert research_store.load_fusion_context("000001") is not None
    assert research_context["positive_factors"][0]["summary"] == "research signal"
    assert manifest["source_materials"][0]["material_id"]
    assert "FULL ORIGINAL BODY SHOULD NOT ENTER PROMPT" not in json.dumps(research_context, ensure_ascii=False)


def test_report_task_with_research_and_no_materials_still_generates(tmp_path: Path) -> None:
    research_store = ResearchStore(tmp_path / "data")
    manager, task_store, report_store = _manager(
        tmp_path,
        report_agent_factory=lambda: ReportAgent(
            llm_client=FakeLLMClient(),
            prompt_template_path=PROMPT_TEMPLATE,
            research_store=research_store,
        ),
    )

    response = manager.ensure_report("000001", force_regenerate=True, include_research=True)
    assert response.task_id
    manager.execute_task(response.task_id)

    task = task_store.get(response.task_id)
    research_context = json.loads(report_store.research_context_path("000001").read_text(encoding="utf-8"))

    assert task.status == "completed"
    assert research_context["limitations"]
    assert research_context["positive_factors"] == []


def test_report_task_reuses_running_task_for_same_fund(tmp_path: Path) -> None:
    manager, task_store, _ = _manager(tmp_path)
    task_store.create_task("task_existing_000001", "000001")

    response = manager.ensure_report("000001", force_regenerate=True)

    assert response.mode == "running"
    assert response.task_id == "task_existing_000001"


def test_report_task_records_friendly_failure(tmp_path: Path) -> None:
    fund_repository = FundRepository(
        funds_root=tmp_path / "missing-funds",
        sample_input_path=tmp_path / "missing.json",
    )
    report_store = ReportStore(tmp_path / "reports")
    task_store = TaskStore(report_store.reports_root)
    manager = ReportTaskManager(fund_repository, report_store, task_store, report_agent_factory=FakeReportAgent)
    response = manager.ensure_report("404404")

    assert response.task_id
    manager.execute_task(response.task_id)
    task = task_store.get(response.task_id)

    assert task.status == "failed"
    assert task.error
    assert task.error.code == "FUND_NOT_FOUND"


def test_guard_issues_are_saved_as_warning_when_not_enforced(tmp_path: Path) -> None:
    manager, task_store, report_store = _manager(tmp_path, report_agent_factory=FakeGuardFailedReportAgent)
    response = manager.ensure_report("000001")

    assert response.task_id
    manager.execute_task(response.task_id)
    task = task_store.get(response.task_id)
    record = report_store.load_report_record("000001")

    assert task.status == "completed"
    assert record["status"] == "warning"
    assert record["guard_result"]["passed"] is False


def test_guard_issues_fail_task_when_enforced(tmp_path: Path) -> None:
    manager, task_store, report_store = _manager(
        tmp_path,
        report_agent_factory=FakeGuardFailedReportAgent,
        enforce_report_guard=True,
    )
    response = manager.ensure_report("000001")

    assert response.task_id
    manager.execute_task(response.task_id)
    task = task_store.get(response.task_id)

    assert task.status == "failed"
    assert task.error
    assert task.error.code == "REPORT_GUARD_FAILED"
    assert not report_store.report_exists("000001")


def _manager(tmp_path: Path, report_agent_factory=None, enforce_report_guard: bool = False):
    report_agent_factory = report_agent_factory or FakeReportAgent
    fund_repository = FundRepository(
        funds_root=tmp_path / "funds",
        sample_input_path=SAMPLE_INPUT,
    )
    report_store = ReportStore(tmp_path / "reports")
    task_store = TaskStore(report_store.reports_root)
    manager = ReportTaskManager(
        fund_repository,
        report_store,
        task_store,
        report_agent_factory=report_agent_factory,
        enforce_report_guard=enforce_report_guard,
    )
    return manager, task_store, report_store


class FakeReportAgent:
    def generate_report(self, input_path: str | Path, **kwargs):
        metrics = FundRepository(sample_input_path=SAMPLE_INPUT).get_metrics("000001")
        return _report_result(metrics)


class FakeGuardFailedReportAgent:
    def generate_report(self, input_path: str | Path, **kwargs):
        metrics = FundRepository(sample_input_path=SAMPLE_INPUT).get_metrics("000001")
        return replace(
            _report_result(metrics),
            guard_result=GuardResult((GuardIssue("prohibited_expression", "contains hold wording"),)),
        )
