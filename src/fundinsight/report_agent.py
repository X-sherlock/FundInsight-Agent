"""Report orchestration for FundInsight Agent v0.2."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from fundinsight.data_loader import load_fund_metrics
from fundinsight.embeddings import EmbeddingClient
from fundinsight.llm_client import BailianLLMClient, LLMClient
from fundinsight.models import ChartSpec, FundMetricsInput, ReportPlan
from fundinsight.report_guard import GuardResult, check_chart_specs, check_report
from fundinsight.report_parser import parse_report_output
from fundinsight.report_planner import build_report_plan
from fundinsight.research_rag import (
    CORE_REPORT_SECTION_TOP_K,
    ResearchIngestionService,
    ResearchRetrievalService,
    merge_retrieved_chunks,
    select_core_report_chunks,
)
from fundinsight.research_extractor import ResearchSignalExtractor
from fundinsight.research_fusion import save_or_build_fusion_context
from fundinsight.research_interpreter import ResearchMaterialInterpreter
from fundinsight.research_models import ResearchFusionContext, RetrievedResearchChunk
from fundinsight.research_pipeline import process_research_materials
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore
from fundinsight.vector_store import VectorResearchStore


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
    fact_card: dict[str, Any] | None = None
    research_processing_error: str | None = None
    include_research: bool | None = None
    research_mode: Literal["auto", "forced_on", "forced_off"] = "auto"
    research_materials_found: bool = False
    research_material_count: int = 0
    research_used: bool = False


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
        research_material_interpreter: ResearchMaterialInterpreter | None = None,
        research_llm_client: LLMClient | None = None,
        vector_store: VectorResearchStore | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_template_path = Path(prompt_template_path)
        self.research_store = research_store
        self.research_material_service = research_material_service
        self.research_signal_extractor = research_signal_extractor
        self.research_material_interpreter = research_material_interpreter
        self.research_llm_client = research_llm_client
        self.vector_store = vector_store
        self.embedding_client = embedding_client

    def generate_report(
        self,
        input_path: str | Path,
        *,
        include_research: bool | None = None,
        research_material_ids: list[str] | None = None,
        force_reextract: bool = False,
        stage_callback: Callable[[str], None] | None = None,
    ) -> ReportResult:
        fund_metrics = load_fund_metrics(input_path)
        research_context: ResearchFusionContext | None = None
        retrieved_chunks: list[RetrievedResearchChunk] | None = None
        research_processing_error: str | None = None
        research_mode = _research_mode(include_research)
        store, material_service = self._research_dependencies()
        material_count = self._research_material_count(
            fund_code=fund_metrics.fund.code,
            material_service=material_service,
            research_material_ids=research_material_ids,
        )
        materials_found = material_count > 0
        should_process_research = include_research is True or (include_research is None and materials_found)
        if should_process_research and materials_found:
            retrieved_chunks, research_processing_error = self._prepare_rag_chunks(
                fund_code=fund_metrics.fund.code,
                fund_metrics=fund_metrics,
                research_material_ids=research_material_ids,
                force_reextract=force_reextract,
                stage_callback=stage_callback,
                store=store,
                material_service=material_service,
            )

        report_plan = build_report_plan(
            fund_metrics,
            research_context=research_context,
            retrieved_chunks=retrieved_chunks,
        )
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
            fact_card=report_plan.fact_card,
            research_processing_error=research_processing_error,
            include_research=include_research,
            research_mode=research_mode,
            research_materials_found=materials_found,
            research_material_count=material_count,
            research_used=bool(retrieved_chunks),
        )

    def _research_dependencies(self) -> tuple[ResearchStore, ResearchMaterialService]:
        store = self.research_store or (
            self.research_material_service.store
            if self.research_material_service is not None
            else ResearchStore()
        )
        material_service = self.research_material_service or ResearchMaterialService(store)
        return store, material_service

    def _research_material_count(
        self,
        *,
        fund_code: str,
        material_service: ResearchMaterialService,
        research_material_ids: list[str] | None,
    ) -> int:
        try:
            materials = material_service.list_materials(fund_code)
        except Exception:
            return 0
        if not research_material_ids:
            return len(materials)
        existing_ids = {material.material_id for material in materials}
        return sum(1 for material_id in research_material_ids if material_id in existing_ids)

    def _prepare_research_context(
        self,
        *,
        fund_code: str,
        research_material_ids: list[str] | None,
        force_reextract: bool,
        stage_callback: Callable[[str], None] | None,
        store: ResearchStore,
        material_service: ResearchMaterialService,
    ) -> tuple[ResearchFusionContext | None, str | None]:
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
            return None, message

    def _prepare_rag_chunks(
        self,
        *,
        fund_code: str,
        fund_metrics: FundMetricsInput,
        research_material_ids: list[str] | None,
        force_reextract: bool,
        stage_callback: Callable[[str], None] | None,
        store: ResearchStore,
        material_service: ResearchMaterialService,
    ) -> tuple[list[RetrievedResearchChunk] | None, str | None]:
        try:
            if stage_callback is not None:
                stage_callback("extracting_research")
            ingestion = ResearchIngestionService(
                store=store,
                vector_store=self.vector_store,
                embedding_client=self.embedding_client,
            )
            materials = _select_materials(material_service.list_materials(fund_code), research_material_ids)
            material_contents = []
            for material in materials:
                content = material_service.get_material_content(fund_code, material.material_id)
                if content:
                    material_contents.append((material, content))
                if material.vector_status == "indexed" and material.parent_chunk_count and not force_reextract:
                    continue
                if not content:
                    continue
                ingestion.import_text_material(
                    fund_code=fund_code,
                    fund_name=fund_metrics.fund.name,
                    title=material.title,
                    content=content,
                    source_type=material.source_type,
                    source_name=material.source_name,
                    source_url=material.source_url,
                    publish_date=material.publish_date,
                    file_name=material.file_name,
                )
            if stage_callback is not None:
                stage_callback("fusing_research")
            retrieval = ResearchRetrievalService(
                store=store,
                vector_store=ingestion.vector_store,
                embedding_client=self.embedding_client,
            )
            chunks = retrieval.retrieve_for_report(
                fund_metrics=fund_metrics,
                top_k=_retrieval_top_k(),
                material_ids=research_material_ids,
            )
            core_chunks = select_core_report_chunks(
                fund_metrics=fund_metrics,
                material_contents=material_contents,
                max_chunks=_core_report_section_top_k(),
            )
            chunks = merge_retrieved_chunks(
                chunks,
                core_chunks,
                limit=_retrieval_top_k() + _core_report_section_top_k(),
            )
            chunks = self._interpret_retrieved_chunks(
                fund_metrics=fund_metrics,
                chunks=chunks,
            )
            return chunks, None
        except Exception as exc:
            message = f"Research RAG processing failed; generated report from structured metrics only: {exc}"
            return None, message

    def _interpret_retrieved_chunks(
        self,
        *,
        fund_metrics: FundMetricsInput,
        chunks: list[RetrievedResearchChunk],
    ) -> list[RetrievedResearchChunk]:
        if not chunks:
            return chunks
        interpreter = self.research_material_interpreter or ResearchMaterialInterpreter()
        llm_client = self.research_llm_client or self.llm_client or BailianLLMClient()
        interpreted_chunks = interpreter.interpret_chunks(
            fund_metrics=fund_metrics,
            chunks=chunks,
            llm_client=llm_client,
        )
        return [chunk for chunk in interpreted_chunks if _has_material_interpretation(chunk)]


def _combine_guard_results(*results: GuardResult) -> GuardResult:
    issues = tuple(issue for result in results for issue in result.issues)
    return GuardResult(issues)


def _research_mode(include_research: bool | None) -> Literal["auto", "forced_on", "forced_off"]:
    if include_research is True:
        return "forced_on"
    if include_research is False:
        return "forced_off"
    return "auto"


def _has_research_signals(context: ResearchFusionContext | None) -> bool:
    if context is None:
        return False
    return any(
        (
            context.positive_factors,
            context.risk_notices,
            context.key_events,
            context.view_changes,
        )
    )


def _select_materials(materials: list[Any], material_ids: list[str] | None) -> list[Any]:
    if not material_ids:
        return materials
    selected_ids = set(material_ids)
    return [material for material in materials if material.material_id in selected_ids]


def _has_material_interpretation(chunk: RetrievedResearchChunk) -> bool:
    return bool(
        (chunk.analysis_title or "").strip()
        and (chunk.material_summary or "").strip()
        and (chunk.sentiment_label or "").strip()
        and (chunk.evidence_excerpt or "").strip()
    )


def _retrieval_top_k() -> int:
    raw = os.getenv("FUNDINSIGHT_RAG_TOP_K", "12")
    try:
        return max(1, int(raw))
    except ValueError:
        return 12


def _core_report_section_top_k() -> int:
    raw = os.getenv("FUNDINSIGHT_RAG_CORE_TOP_K", str(CORE_REPORT_SECTION_TOP_K))
    try:
        return max(0, int(raw))
    except ValueError:
        return CORE_REPORT_SECTION_TOP_K
