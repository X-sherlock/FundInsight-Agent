"""Application service for the unstructured research material lifecycle."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fundinsight.research_loader import (
    build_research_document,
    compute_content_hash,
    load_research_json,
    normalize_research_content,
    split_research_chunks,
)
from fundinsight.research_models import ResearchChunk, ResearchDocument, SourceType
from fundinsight.research_store import ResearchStore


EXTRACTION_CHUNK_MIN_CHARS = 1200
EXTRACTION_CHUNK_MAX_CHARS = 2800
EXTRACTION_CHUNK_OVERLAP_CHARS = 350


class ResearchMaterialService:
    def __init__(self, store: ResearchStore | None = None) -> None:
        self.store = store or ResearchStore()

    def import_text_material(
        self,
        *,
        fund_code: str,
        title: str,
        content: str,
        source_type: SourceType,
        source_name: str | None = None,
        source_url: str | None = None,
        publish_date: date | str | None = None,
        file_name: str | None = None,
    ) -> ResearchDocument:
        normalized = normalize_research_content(content)
        if not normalized:
            raise ValueError("Research material content is empty after normalization.")

        content_hash = compute_content_hash(normalized)
        for existing in self.store.list_materials(fund_code):
            if existing.content_hash == content_hash:
                return existing

        document = build_research_document(
            fund_code=fund_code,
            title=title,
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            publish_date=publish_date,
            file_name=file_name,
            content=normalized,
        )
        self.store.save_material(fund_code, document, normalized)
        return document

    def import_json_material(
        self,
        *,
        fund_code: str,
        path: str | Path,
        title: str,
        source_type: SourceType,
        source_name: str | None = None,
        source_url: str | None = None,
        publish_date: date | str | None = None,
    ) -> ResearchDocument:
        input_path = Path(path)
        return self.import_text_material(
            fund_code=fund_code,
            title=title,
            content=load_research_json(input_path),
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            publish_date=publish_date,
            file_name=input_path.name,
        )

    def list_materials(self, fund_code: str) -> list[ResearchDocument]:
        return self.store.list_materials(fund_code)

    def get_material_content(self, fund_code: str, material_id: str) -> str | None:
        return self.store.read_material_content(fund_code, material_id)

    def delete_material(self, fund_code: str, material_id: str) -> bool:
        return self.store.delete_material(fund_code, material_id)

    def build_chunks_for_material(self, fund_code: str, material_id: str) -> list[ResearchChunk]:
        content = self.store.read_material_content(fund_code, material_id)
        if content is None:
            raise ValueError(f"Research material does not exist: {material_id}")

        chunk_texts = split_research_chunks(
            content,
            target_min_chars=EXTRACTION_CHUNK_MIN_CHARS,
            target_max_chars=EXTRACTION_CHUNK_MAX_CHARS,
            overlap_chars=EXTRACTION_CHUNK_OVERLAP_CHARS,
        )
        return [
            ResearchChunk(
                chunk_id=f"{material_id}_{chunk_index:04d}",
                material_id=material_id,
                fund_code=fund_code,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
            )
            for chunk_index, chunk_text in enumerate(chunk_texts)
        ]
