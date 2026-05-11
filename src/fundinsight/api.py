"""FastAPI entry point for FundInsight frontend/backend integration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, cast

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fundinsight.api_models import (
    EnsureReportRequest,
    EnsureReportResponse,
    FundMetricsResponse,
    FundSearchResponse,
    ResearchMaterialCreateRequest,
    ResearchMaterialListResponse,
    ResearchMaterialSummaryResponse,
    ReportTaskResponse,
)
from fundinsight.fund_repository import FundNotFoundError, FundRepository
from fundinsight.llm_client import DEFAULT_BAILIAN_MODEL
from fundinsight.report_store import ReportNotFoundError, ReportStore
from fundinsight.report_tasks import ReportTaskManager
from fundinsight.research_models import ResearchDocument, SourceType
from fundinsight.research_service import ResearchMaterialService
from fundinsight.task_store import TaskNotFoundError, TaskStore

ALLOWED_SOURCE_TYPES: set[str] = {"report", "announcement", "news", "internal_research"}


def create_app(
    *,
    fund_repository: FundRepository | None = None,
    report_store: ReportStore | None = None,
    task_store: TaskStore | None = None,
    task_manager: ReportTaskManager | None = None,
    research_material_service: ResearchMaterialService | None = None,
    enforce_report_guard: bool | None = None,
) -> FastAPI:
    repository = fund_repository or FundRepository()
    reports = report_store or ReportStore()
    tasks = task_store or TaskStore(reports.reports_root)
    research_service = research_material_service or ResearchMaterialService()
    guard_enforced = _resolve_enforce_report_guard(enforce_report_guard)
    manager = task_manager or ReportTaskManager(
        repository,
        reports,
        tasks,
        enforce_report_guard=guard_enforced,
    )

    app = FastAPI(title="FundInsight Agent API", version="0.4.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/funds", response_model=FundSearchResponse)
    def search_funds(query: str = "") -> FundSearchResponse:
        return FundSearchResponse(items=repository.list_funds(query))

    @app.get("/api/funds/{fund_code}/metrics", response_model=FundMetricsResponse)
    def get_fund_metrics(fund_code: str) -> FundMetricsResponse:
        try:
            return FundMetricsResponse.model_validate(repository.get_metrics_response(fund_code))
        except FundNotFoundError as exc:
            raise _http_error(404, "FUND_NOT_FOUND", str(exc)) from exc
        except ValueError as exc:
            raise _http_error(422, "INVALID_METRICS", str(exc)) from exc

    @app.get("/api/funds/{fund_code}/research-materials", response_model=ResearchMaterialListResponse)
    def list_research_materials(fund_code: str) -> ResearchMaterialListResponse:
        try:
            return ResearchMaterialListResponse(
                items=[
                    _research_material_summary(document)
                    for document in research_service.list_materials(fund_code)
                ]
            )
        except ValueError as exc:
            raise _http_error(400, "INVALID_RESEARCH_MATERIAL", str(exc)) from exc

    @app.post("/api/funds/{fund_code}/research-materials", response_model=ResearchDocument)
    def create_research_material(
        fund_code: str,
        request: ResearchMaterialCreateRequest,
    ) -> ResearchDocument:
        if not request.title.strip():
            raise _http_error(400, "INVALID_RESEARCH_MATERIAL", "Research material title must not be empty.")
        if not request.content.strip():
            raise _http_error(400, "INVALID_RESEARCH_MATERIAL", "Research material content must not be empty.")
        if request.source_type not in ALLOWED_SOURCE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_SOURCE_TYPES))
            raise _http_error(
                400,
                "INVALID_RESEARCH_MATERIAL",
                f"Invalid source_type: {request.source_type}. Allowed values: {allowed}.",
            )
        try:
            return research_service.import_text_material(
                fund_code=fund_code,
                title=request.title.strip(),
                content=request.content,
                source_type=cast(SourceType, request.source_type),
                source_name=request.source_name.strip() if request.source_name else None,
                publish_date=request.publish_date,
            )
        except ValueError as exc:
            raise _http_error(400, "INVALID_RESEARCH_MATERIAL", str(exc)) from exc

    @app.delete("/api/funds/{fund_code}/research-materials/{material_id}")
    def delete_research_material(fund_code: str, material_id: str) -> dict[str, Any]:
        try:
            deleted = research_service.delete_material(fund_code, material_id)
        except ValueError as exc:
            raise _http_error(400, "INVALID_RESEARCH_MATERIAL", str(exc)) from exc
        if not deleted:
            raise _http_error(404, "RESEARCH_MATERIAL_NOT_FOUND", f"Research material does not exist: {material_id}")
        return {"deleted": True, "material_id": material_id}

    @app.get("/api/funds/{fund_code}/research-context")
    def get_research_context(fund_code: str) -> dict[str, Any]:
        try:
            research_service.store.research_dir(fund_code)
            report_context_path = reports.research_context_path(fund_code)
            if report_context_path.exists():
                return _read_json_object(report_context_path)
            context = research_service.store.load_fusion_context(fund_code)
            if context is not None:
                return context.model_dump(mode="json")
        except ValueError as exc:
            raise _http_error(400, "INVALID_RESEARCH_CONTEXT", str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise _http_error(500, "RESEARCH_CONTEXT_READ_FAILED", str(exc)) from exc
        return _empty_research_context(fund_code)

    @app.post("/api/reports/ensure", response_model=EnsureReportResponse)
    def ensure_report(request: EnsureReportRequest, background_tasks: BackgroundTasks) -> EnsureReportResponse:
        response = manager.ensure_report(
            request.fund_code,
            force_regenerate=request.force_regenerate,
            include_research=request.include_research,
            research_material_ids=request.research_material_ids,
            force_reextract=request.force_reextract,
        )
        if response.mode == "created" and response.task_id:
            background_tasks.add_task(manager.execute_task, response.task_id)
        return response

    @app.get("/api/report-tasks/{task_id}", response_model=ReportTaskResponse)
    def get_report_task(task_id: str) -> ReportTaskResponse:
        try:
            return tasks.get(task_id)
        except TaskNotFoundError as exc:
            raise _http_error(404, "TASK_NOT_FOUND", str(exc)) from exc

    @app.get("/api/reports/{report_id}")
    def get_report(report_id: str) -> dict[str, Any]:
        try:
            return reports.load_report_record(report_id)
        except ReportNotFoundError as exc:
            raise _http_error(404, "REPORT_NOT_FOUND", str(exc)) from exc
        except ValueError as exc:
            raise _http_error(500, "REPORT_READ_FAILED", str(exc)) from exc

    @app.get("/api/reports")
    def list_reports() -> dict[str, Any]:
        return {"items": reports.list_report_records()}

    @app.get("/api/dashboard")
    def dashboard() -> dict[str, Any]:
        report_records = reports.list_report_records()
        passed = [report for report in report_records if report["status"] == "passed"]
        warning = [report for report in report_records if report["status"] == "warning"]
        guard_is_enforced = bool(getattr(manager, "enforce_report_guard", False))
        return {
            "total_reports": len(report_records),
            "passed_reports": len(passed),
            "warning_reports": len(warning),
            "mock_mode": False,
            "latest_report": report_records[0] if report_records else None,
            "recent_reports": report_records[:8],
            "system_status": [
                {"label": "数据模式", "value": "Local JSON", "status": "ok"},
                {
                    "label": "报告 Guard",
                    "value": "Enforced" if guard_is_enforced else "Warning only",
                    "status": "ok" if guard_is_enforced else "warning",
                },
                {"label": "LLM Provider", "value": f"Bailian / {DEFAULT_BAILIAN_MODEL}", "status": "ok"},
                {"label": "后端接口", "value": "FastAPI", "status": "ok"},
            ],
        }

    return app


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _research_material_summary(document: ResearchDocument) -> ResearchMaterialSummaryResponse:
    return ResearchMaterialSummaryResponse.model_validate(document.model_dump(mode="json"))


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _empty_research_context(fund_code: str) -> dict[str, Any]:
    return {
        "fund_code": fund_code,
        "positive_factors": [],
        "risk_notices": [],
        "key_events": [],
        "view_changes": [],
        "source_materials": [],
        "limitations": [],
    }


def _resolve_enforce_report_guard(value: bool | None = None) -> bool:
    if value is not None:
        return value
    raw = os.getenv("FUNDINSIGHT_ENFORCE_REPORT_GUARD", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_cors_allow_origins() -> list[str]:
    defaults = ["http://localhost:5173", "http://127.0.0.1:5173"]
    raw = os.getenv("FUNDINSIGHT_CORS_ALLOW_ORIGINS", "")
    configured = [_normalize_origin(origin) for origin in raw.split(",") if origin.strip()]
    return defaults + configured


def _normalize_origin(origin: str) -> str:
    value = origin.strip().rstrip("/")
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


app = create_app()


def run() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(prog="fundinsight-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--enforce-report-guard",
        action="store_true",
        help="Fail report tasks when report_guard finds structure or boundary issues.",
    )
    args = parser.parse_args()

    os.environ["FUNDINSIGHT_ENFORCE_REPORT_GUARD"] = "true" if args.enforce_report_guard else "false"
    uvicorn.run("fundinsight.api:app", host=args.host, port=args.port, reload=True)
