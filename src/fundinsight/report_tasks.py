"""Background report task orchestration for the API layer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fundinsight.api_models import ApiError, EnsureReportResponse
from fundinsight.fund_repository import FundNotFoundError, FundRepository
from fundinsight.report_agent import ReportAgent, ReportResult
from fundinsight.report_store import ReportStore
from fundinsight.research_service import ResearchMaterialService
from fundinsight.task_store import TaskStore


ReportAgentFactory = Callable[[], ReportAgent]


class ReportTaskManager:
    def __init__(
        self,
        fund_repository: FundRepository,
        report_store: ReportStore,
        task_store: TaskStore,
        report_agent_factory: ReportAgentFactory | None = None,
        *,
        enforce_report_guard: bool = False,
        research_material_service: ResearchMaterialService | None = None,
    ) -> None:
        self.fund_repository = fund_repository
        self.report_store = report_store
        self.task_store = task_store
        self.enforce_report_guard = enforce_report_guard
        self.research_material_service = research_material_service or ResearchMaterialService()
        self.report_agent_factory = report_agent_factory or (
            lambda: ReportAgent(research_material_service=self.research_material_service)
        )

    def ensure_report(
        self,
        fund_code: str,
        *,
        force_regenerate: bool = False,
        include_research: bool | None = None,
        research_material_ids: list[str] | None = None,
        force_reextract: bool = False,
    ) -> EnsureReportResponse:
        normalized_code = fund_code.strip()
        if (
            not force_regenerate
            and include_research is not True
            and self.report_store.report_exists(normalized_code)
            and not self._should_refresh_existing_report_for_auto_research(normalized_code, include_research)
        ):
            report_id = self.report_store.report_id_for_fund(normalized_code)
            return EnsureReportResponse(
                mode="existing",
                status="ready",
                report_id=report_id,
                report_url=f"/api/reports/{report_id}",
            )

        running_task = self.task_store.find_running_task(normalized_code)
        if running_task:
            return EnsureReportResponse(
                mode="running",
                status=running_task.status,
                task_id=running_task.task_id,
                status_url=f"/api/report-tasks/{running_task.task_id}",
            )

        task_id = self._new_task_id(normalized_code)
        self.task_store.create_task(
            task_id,
            normalized_code,
            include_research=include_research,
            research_material_ids=research_material_ids,
            force_reextract=force_reextract,
        )
        return EnsureReportResponse(
            mode="created",
            status="queued",
            task_id=task_id,
            status_url=f"/api/report-tasks/{task_id}",
        )

    def execute_task(self, task_id: str) -> None:
        task = self.task_store.get(task_id)
        current_stage = "queued"
        try:
            current_stage = "loading_data"
            self.task_store.update_stage(task_id, "loading_data")
            input_path = self.fund_repository.get_metrics_path(task.fund_code)
            source_metrics = self.fund_repository.get_raw_metrics(task.fund_code)

            current_stage = "planning_context"
            self.task_store.update_stage(task_id, "planning_context")
            current_stage = "llm_generating"
            self.task_store.update_stage(task_id, "llm_generating")
            result = self.report_agent_factory().generate_report(
                input_path,
                include_research=task.include_research,
                research_material_ids=task.research_material_ids,
                force_reextract=task.force_reextract,
                stage_callback=lambda stage: self.task_store.update_stage(task_id, stage),
            )

            current_stage = "parsing_charts"
            self.task_store.update_stage(task_id, "parsing_charts")
            if not result.chart_specs:
                raise ReportTaskError("REPORT_PARSE_FAILED", "报告图表信息解析失败，请稍后重试。")

            current_stage = "quality_checking"
            self.task_store.update_stage(task_id, "quality_checking")
            if self.enforce_report_guard and not result.guard_result.passed:
                issue_text = "; ".join(issue.message for issue in result.guard_result.issues[:3])
                raise ReportTaskError(
                    "REPORT_GUARD_FAILED",
                    f"报告未通过结构或边界检查，系统未保存为可用报告。{issue_text}",
                )

            current_stage = "saving_report"
            self.task_store.update_stage(task_id, "saving_report")
            report_id = self._save_report(result, source_metrics)
            self.task_store.update_stage(task_id, "completed", report_id=report_id)
        except FundNotFoundError:
            self._fail(task_id, "FUND_NOT_FOUND", "未找到该基金的后端指标数据，请确认基金代码或数据文件是否已准备。")
        except ValueError as exc:
            if current_stage in {"loading_data", "planning_context"}:
                self._fail(task_id, "INVALID_METRICS", f"该基金指标数据暂不满足报告生成格式要求：{exc}")
            else:
                self._fail(task_id, "REPORT_PARSE_FAILED", f"报告输出解析失败，请稍后重试：{exc}")
        except ReportTaskError as exc:
            self._fail(task_id, exc.code, exc.message)
        except OSError as exc:
            self._fail(task_id, "REPORT_SAVE_FAILED", f"报告文件写入失败：{exc}")
        except Exception as exc:  # pragma: no cover - defensive boundary for provider failures
            self._fail(task_id, "LLM_GENERATION_FAILED", f"模型服务暂时不可用或报告生成失败：{exc}")

    def _save_report(self, result: ReportResult, source_metrics: dict) -> str:
        return self.report_store.save_generated_report(result, source_metrics)

    def _fail(self, task_id: str, code: str, message: str) -> None:
        self.task_store.update_stage(
            task_id,
            "failed",
            error=ApiError(code=code, message=message),
            message=message,
        )

    def _new_task_id(self, fund_code: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = uuid4().hex[:8]
        return f"task_{timestamp}_{fund_code}_{suffix}"

    def _should_refresh_existing_report_for_auto_research(
        self,
        fund_code: str,
        include_research: bool | None,
    ) -> bool:
        if include_research is not None:
            return False
        try:
            material_count = len(self.research_material_service.list_materials(fund_code))
        except Exception:
            return False
        if material_count == 0:
            return False
        try:
            metadata = self.report_store._read_json(self.report_store.metadata_path(fund_code))
        except Exception:
            return False
        research_metadata = metadata.get("research")
        if not isinstance(research_metadata, dict):
            return True
        return not bool(research_metadata.get("used") or research_metadata.get("context_saved"))


class ReportTaskError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
