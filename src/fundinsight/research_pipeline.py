"""Processing pipeline for extracting and storing research material signals."""

from __future__ import annotations

import logging
import re

from fundinsight.llm_client import BailianLLMClient, LLMClient
from fundinsight.research_extractor import ResearchSignalExtractor
from fundinsight.research_models import ResearchDocument, ResearchSignal, ResearchSignalBundle
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore


logger = logging.getLogger(__name__)


def process_research_materials(
    fund_code: str,
    store: ResearchStore,
    material_service: ResearchMaterialService,
    extractor: ResearchSignalExtractor,
    material_ids: list[str] | None = None,
    force_reextract: bool = False,
    llm_client: LLMClient | None = None,
) -> ResearchSignalBundle:
    """Extract signals from saved materials, deduplicate them, and persist the bundle."""

    if not force_reextract:
        existing = store.load_signal_bundle(fund_code)
        if existing is not None:
            return existing

    materials = store.list_materials(fund_code)
    selected_materials = _select_materials(fund_code, materials, material_ids)
    if not selected_materials:
        bundle = ResearchSignalBundle(fund_code=fund_code, signals=[], materials=[])
        store.save_signal_bundle(fund_code, bundle)
        return bundle

    resolved_llm_client = llm_client or BailianLLMClient()
    extracted_signals: list[ResearchSignal] = []
    processed_materials: list[ResearchDocument] = []

    for material in selected_materials:
        try:
            chunks = material_service.build_chunks_for_material(fund_code, material.material_id)
        except Exception as exc:
            logger.warning("Failed to build chunks for material %s: %s", material.material_id, exc)
            continue

        processed_materials.append(material)
        for chunk in chunks:
            try:
                extracted_signals.extend(
                    extractor.extract_signals_from_chunk(
                        fund_code=fund_code,
                        material=material,
                        chunk=chunk,
                        chunk_text=chunk.chunk_text,
                        llm_client=resolved_llm_client,
                    )
                )
            except Exception as exc:
                logger.warning(
                    "Failed to extract signals for material %s chunk %s: %s",
                    material.material_id,
                    chunk.chunk_id,
                    exc,
                )

    bundle = ResearchSignalBundle(
        fund_code=fund_code,
        signals=_deduplicate_signals(extracted_signals),
        materials=processed_materials,
    )
    store.save_signal_bundle(fund_code, bundle)
    return bundle


def _select_materials(
    fund_code: str,
    materials: list[ResearchDocument],
    material_ids: list[str] | None,
) -> list[ResearchDocument]:
    if not material_ids:
        return materials

    by_id = {material.material_id: material for material in materials}
    selected: list[ResearchDocument] = []
    for material_id in material_ids:
        material = by_id.get(material_id)
        if material is None:
            logger.warning("Research material %s does not exist for fund %s; skipped.", material_id, fund_code)
            continue
        selected.append(material)
    return selected


def _deduplicate_signals(signals: list[ResearchSignal]) -> list[ResearchSignal]:
    seen: set[tuple[str, str, str]] = set()
    deduplicated: list[ResearchSignal] = []
    for signal in signals:
        key = (
            signal.signal_type,
            _normalize_summary(signal.summary),
            signal.evidence_text.strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(signal)
    return deduplicated


def _normalize_summary(summary: str) -> str:
    return re.sub(r"\s+", "", summary).casefold()
