"""JSON-backed report task state storage."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fundinsight.api_models import ApiError, ReportTaskResponse, ReportTaskStatusValue
from fundinsight.report_store import DEFAULT_REPORTS_ROOT


STAGE_MESSAGES: dict[str, tuple[str, str]] = {
    "queued": ("已加入报告生成队列", "系统正在准备处理该基金的报告请求。"),
    "loading_data": ("正在读取基金指标", "正在加载后端保存的基金基础信息、收益、风险、持仓和数据质量字段。"),
    "planning_context": ("正在整理分析上下文", "正在组织指标表格、缺失字段、图表草案和可解释的分析线索。"),
    "llm_generating": ("正在生成分析报告", "模型正在基于结构化指标生成非投顾性质的 Markdown 分析内容。"),
    "parsing_charts": ("正在解析图表信息", "正在提取报告正文中的图表占位和对应 chart specs。"),
    "quality_checking": ("正在进行质量检查", "正在检查必需章节、图表一致性和明显边界风险。"),
    "saving_report": ("正在保存报告", "正在写入报告正文、图表规格和生成元数据。"),
    "completed": ("报告已生成", "即将打开报告详情页。"),
    "failed": ("报告生成未完成", "可根据错误提示重试，或返回检查基金指标数据。"),
}

RUNNING_STATUSES = {
    "queued",
    "loading_data",
    "planning_context",
    "llm_generating",
    "parsing_charts",
    "quality_checking",
    "saving_report",
}


class TaskNotFoundError(LookupError):
    """Raised when a task JSON file does not exist."""


STAGE_MESSAGES.update(
    {
        "extracting_research": (
            "正在提取投研材料信号",
            "正在从已保存的投研材料中提取正面因素、风险提示、关键事件和观点变化。",
        ),
        "fusing_research": (
            "正在融合投研上下文",
            "正在将投研材料信号整理为报告可用的结构化上下文。",
        ),
    }
)
RUNNING_STATUSES.update({"extracting_research", "fusing_research"})


class TaskStore:
    def __init__(self, reports_root: str | Path = DEFAULT_REPORTS_ROOT) -> None:
        self.tasks_root = Path(reports_root) / "tasks"

    def create_task(
        self,
        task_id: str,
        fund_code: str,
        *,
        include_research: bool | None = None,
        research_material_ids: list[str] | None = None,
        force_reextract: bool = False,
    ) -> ReportTaskResponse:
        now = self._now()
        task = ReportTaskResponse(
            task_id=task_id,
            fund_code=fund_code,
            status="queued",
            stage="queued",
            stage_label=STAGE_MESSAGES["queued"][0],
            message=STAGE_MESSAGES["queued"][1],
            report_id=None,
            error=None,
            include_research=include_research,
            research_material_ids=research_material_ids,
            force_reextract=force_reextract,
            created_at=now,
            updated_at=now,
        )
        self.save(task)
        return task

    def get(self, task_id: str) -> ReportTaskResponse:
        path = self._task_path(task_id)
        if not path.exists():
            raise TaskNotFoundError(f"Task does not exist: {task_id}")
        return ReportTaskResponse.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, task: ReportTaskResponse) -> None:
        self.tasks_root.mkdir(parents=True, exist_ok=True)
        self._task_path(task.task_id).write_text(
            json.dumps(task.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update_stage(
        self,
        task_id: str,
        stage: ReportTaskStatusValue,
        *,
        report_id: str | None = None,
        error: ApiError | None = None,
        message: str | None = None,
    ) -> ReportTaskResponse:
        task = self.get(task_id)
        label, default_message = STAGE_MESSAGES[stage]
        status = "failed" if stage == "failed" else "completed" if stage == "completed" else stage
        updated = task.model_copy(
            update={
                "status": status,
                "stage": stage,
                "stage_label": label,
                "message": message or default_message,
                "report_id": report_id if report_id is not None else task.report_id,
                "error": error,
                "updated_at": self._now(),
            }
        )
        self.save(updated)
        return updated

    def find_running_task(self, fund_code: str) -> ReportTaskResponse | None:
        if not self.tasks_root.exists():
            return None
        running: list[ReportTaskResponse] = []
        for path in sorted(self.tasks_root.glob("*.json")):
            try:
                task = ReportTaskResponse.model_validate(json.loads(path.read_text(encoding="utf-8")))
            except (ValueError, json.JSONDecodeError):
                continue
            if task.fund_code == fund_code and task.status in RUNNING_STATUSES:
                running.append(task)
        if not running:
            return None
        return sorted(running, key=lambda task: task.updated_at)[-1]

    def _task_path(self, task_id: str) -> Path:
        return self.tasks_root / f"{task_id}.json"

    def _now(self) -> str:
        return datetime.now().astimezone().isoformat()
