"""Report orchestration for FundInsight Agent v0.2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fundinsight.data_loader import load_fund_metrics
from fundinsight.llm_client import BailianLLMClient, LLMClient
from fundinsight.models import ChartSpec, FundMetricsInput, ReportPlan
from fundinsight.report_guard import GuardResult, check_chart_specs, check_report
from fundinsight.report_parser import parse_report_output
from fundinsight.report_planner import build_report_plan
from fundinsight.research_extractor import ResearchSignalExtractor
from fundinsight.research_fusion import save_or_build_fusion_context
from fundinsight.research_models import ResearchFusionContext
from fundinsight.research_pipeline import process_research_materials
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore


DEFAULT_PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "fund_report_prompt.md"


@dataclass(frozen=True)
class ReportResult:
    fund_metrics: FundMetricsInput
    report_plan: ReportPlan
    prompt: str
    markdown: str
    chart_specs: list[ChartSpec]
    guard_result: GuardResult
    research_context: ResearchFusionContext | None = None
    research_processing_error: str | None = None
    include_research: bool = False


def load_prompt_template(path: str | Path = DEFAULT_PROMPT_TEMPLATE_PATH) -> str:
    template_path = Path(path)
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template does not exist: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_prompt(template: str, report_plan: ReportPlan) -> str:
    payload = json.dumps(report_plan.to_prompt_payload(), ensure_ascii=False, indent=2)
    placeholder = "{{report_context_json}}"
    if placeholder not in template:
        raise ValueError("Prompt template must contain {{report_context_json}} placeholder.")
    return template.replace(placeholder, payload)


class ReportAgent:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_template_path: str | Path = DEFAULT_PROMPT_TEMPLATE_PATH,
        *,
        research_store: ResearchStore | None = None,
        research_material_service: ResearchMaterialService | None = None,
        research_signal_extractor: ResearchSignalExtractor | None = None,
        research_llm_client: LLMClient | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_template_path = Path(prompt_template_path)
        self.research_store = research_store
        self.research_material_service = research_material_service
        self.research_signal_extractor = research_signal_extractor
        self.research_llm_client = research_llm_client

    def generate_report(
        self,
        input_path: str | Path,
        *,
        include_research: bool = False,
        research_material_ids: list[str] | None = None,
        force_reextract: bool = False,
        stage_callback: Callable[[str], None] | None = None,
    ) -> ReportResult:
        fund_metrics = load_fund_metrics(input_path)
        research_context: ResearchFusionContext | None = None
        research_processing_error: str | None = None
        if include_research:
            research_context, research_processing_error = self._prepare_research_context(
                fund_code=fund_metrics.fund.code,
                research_material_ids=research_material_ids,
                force_reextract=force_reextract,
                stage_callback=stage_callback,
            )

        report_plan = build_report_plan(fund_metrics, research_context=research_context)
        template = load_prompt_template(self.prompt_template_path)
        prompt = render_prompt(template, report_plan)
        llm_client = self.llm_client or BailianLLMClient()
        if stage_callback is not None:
            stage_callback("llm_generating")
        raw_output = llm_client.generate(prompt)
        parsed_output = parse_report_output(raw_output)
        guard_result = _combine_guard_results(
            check_report(parsed_output.report_markdown),
            check_chart_specs(parsed_output.report_markdown, parsed_output.chart_specs),
        )
        return ReportResult(
            fund_metrics=fund_metrics,
            report_plan=report_plan,
            prompt=prompt,
            markdown=parsed_output.report_markdown,
            chart_specs=parsed_output.chart_specs,
            guard_result=guard_result,
            research_context=research_context,
            research_processing_error=research_processing_error,
            include_research=include_research,
        )

    def _prepare_research_context(
        self,
        *,
        fund_code: str,
        research_material_ids: list[str] | None,
        force_reextract: bool,
        stage_callback: Callable[[str], None] | None,
    ) -> tuple[ResearchFusionContext, str | None]:
        store = self.research_store or (
            self.research_material_service.store
            if self.research_material_service is not None
            else ResearchStore()
        )
        material_service = self.research_material_service or ResearchMaterialService(store)
        extractor = self.research_signal_extractor or ResearchSignalExtractor()

        try:
            if stage_callback is not None:
                stage_callback("extracting_research")
            process_research_materials(
                fund_code=fund_code,
                store=store,
                material_service=material_service,
                extractor=extractor,
                material_ids=research_material_ids,
                force_reextract=force_reextract,
                llm_client=self.research_llm_client,
            )
            if stage_callback is not None:
                stage_callback("fusing_research")
            return save_or_build_fusion_context(fund_code=fund_code, store=store), None
        except Exception as exc:
            message = f"Research processing failed; generated report from structured metrics only: {exc}"
            return ResearchFusionContext(fund_code=fund_code, limitations=[message]), message


def _combine_guard_results(*results: GuardResult) -> GuardResult:
    issues = tuple(issue for result in results for issue in result.issues)
    return GuardResult(issues)
