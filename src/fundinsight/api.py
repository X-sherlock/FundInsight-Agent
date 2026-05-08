"""FastAPI entry point for FundInsight frontend/backend integration."""

from __future__ import annotations

import argparse
import os
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fundinsight.api_models import (
    EnsureReportRequest,
    EnsureReportResponse,
    FundMetricsResponse,
    FundSearchResponse,
    ReportTaskResponse,
)
from fundinsight.fund_repository import FundNotFoundError, FundRepository
from fundinsight.report_store import ReportNotFoundError, ReportStore
from fundinsight.report_tasks import ReportTaskManager
from fundinsight.task_store import TaskNotFoundError, TaskStore


def create_app(
    *,
    fund_repository: FundRepository | None = None,
    report_store: ReportStore | None = None,
    task_store: TaskStore | None = None,
    task_manager: ReportTaskManager | None = None,
    enforce_report_guard: bool | None = None,
) -> FastAPI:
    repository = fund_repository or FundRepository()
    reports = report_store or ReportStore()
    tasks = task_store or TaskStore(reports.reports_root)
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

    @app.post("/api/reports/ensure", response_model=EnsureReportResponse)
    def ensure_report(request: EnsureReportRequest, background_tasks: BackgroundTasks) -> EnsureReportResponse:
        response = manager.ensure_report(
            request.fund_code,
            force_regenerate=request.force_regenerate,
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
                {"label": "LLM Provider", "value": "Configured by environment", "status": "ok"},
                {"label": "后端接口", "value": "FastAPI", "status": "ok"},
            ],
        }

    return app


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


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
