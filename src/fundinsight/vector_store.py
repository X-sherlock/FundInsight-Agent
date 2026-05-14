"""Vector storage abstraction for fund research material chunks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fundinsight.research_models import ResearchChunk, ResearchDocument, RetrievedResearchChunk
from fundinsight.research_store import DEFAULT_DATA_ROOT


DEFAULT_VECTOR_ROOT = DEFAULT_DATA_ROOT / "vector_store"
DEFAULT_CHROMA_ROOT = DEFAULT_VECTOR_ROOT / "chroma"
COLLECTION_NAME = "fund_research_chunks"


@dataclass(frozen=True)
class VectorChunkRecord:
    chunk: ResearchChunk
    material: ResearchDocument
    embedding: list[float]


class VectorStoreError(RuntimeError):
    """Raised when the required vector store backend is unavailable."""


class VectorResearchStore:
    """Persist and query research chunks with ChromaDB."""

    def __init__(
        self,
        persist_directory: str | Path = DEFAULT_CHROMA_ROOT,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self._collection: Any = self._load_chroma_collection()

    @property
    def using_chroma(self) -> bool:
        return True

    def upsert_chunks(self, records: list[VectorChunkRecord]) -> None:
        if not records:
            return
        self._upsert_chroma(records)

    def delete_material(self, fund_code: str, material_id: str) -> None:
        try:
            self._collection.delete(where={"$and": [{"fund_code": fund_code}, {"material_id": material_id}]})
        except Exception:
            self._collection.delete(where={"material_id": material_id})

    def query(
        self,
        *,
        fund_code: str,
        query_embedding: list[float],
        top_k: int = 12,
        material_ids: list[str] | None = None,
    ) -> list[RetrievedResearchChunk]:
        if top_k <= 0:
            return []
        return self._query_chroma(
            fund_code=fund_code,
            query_embedding=query_embedding,
            top_k=top_k,
            material_ids=material_ids,
        )

    def _load_chroma_collection(self) -> Any:
        try:
            import chromadb
        except ImportError:
            raise VectorStoreError("ChromaDB is required for vector storage. Install the chromadb package.") from None
        try:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self.persist_directory))
            return client.get_or_create_collection(COLLECTION_NAME)
        except Exception as exc:
            raise VectorStoreError(f"Failed to initialize Chroma vector store at {self.persist_directory}: {exc}") from exc

    def _upsert_chroma(self, records: list[VectorChunkRecord]) -> None:
        ids = [record.chunk.chunk_id for record in records]
        documents = [record.chunk.embedding_text or record.chunk.chunk_text for record in records]
        embeddings = [record.embedding for record in records]
        metadatas = [_metadata(record.chunk, record.material) for record in records]
        self._collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def _query_chroma(
        self,
        *,
        fund_code: str,
        query_embedding: list[float],
        top_k: int,
        material_ids: list[str] | None,
    ) -> list[RetrievedResearchChunk]:
        where: dict[str, Any] = {"fund_code": fund_code}
        if material_ids:
            where = {"$and": [{"fund_code": fund_code}, {"material_id": {"$in": material_ids}}]}
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        chunks: list[RetrievedResearchChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            chunks.append(_retrieved_chunk(metadata, document, _distance_to_score(distance)))
        return chunks

def _metadata(chunk: ResearchChunk, material: ResearchDocument) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "material_id": material.material_id,
        "fund_code": material.fund_code,
        "fund_name": chunk.fund_name or "",
        "chunk_index": chunk.chunk_index,
        "parent_chunk_id": chunk.parent_chunk_id or "",
        "chunk_level": chunk.chunk_level,
        "chunk_index_in_parent": chunk.chunk_index_in_parent if chunk.chunk_index_in_parent is not None else -1,
        "raw_text": chunk.raw_text or "",
        "parent_chunk_text": chunk.parent_chunk_text or "",
        "section_path": chunk.section_path or "",
        "page_start": chunk.page_start or 0,
        "page_end": chunk.page_end or 0,
        "block_start_index": chunk.block_start_index if chunk.block_start_index is not None else -1,
        "block_end_index": chunk.block_end_index if chunk.block_end_index is not None else -1,
        "document_title": chunk.document_title or material.title,
        "document_type": chunk.document_type or material.source_type,
        "report_period": chunk.report_period or "",
        "source_type": material.source_type,
        "title": material.title,
        "source_name": material.source_name or "",
        "source_url": chunk.source_url or material.source_url or "",
        "publish_date": (chunk.publish_date or material.publish_date).isoformat() if (chunk.publish_date or material.publish_date) else "",
        "file_name": material.file_name or "",
        "original_file_path": material.original_file_path or "",
    }


def _retrieved_chunk(metadata: dict[str, Any], document: str, score: float) -> RetrievedResearchChunk:
    publish_date = metadata.get("publish_date") or None
    parent_text = str(metadata.get("parent_chunk_text") or "").strip()
    raw_text = str(metadata.get("raw_text") or "").strip() or None
    evidence_text = parent_text or raw_text or document
    parent_chunk_id = str(metadata.get("parent_chunk_id") or "").strip() or None
    page_start = _positive_int_or_none(metadata.get("page_start"))
    page_end = _positive_int_or_none(metadata.get("page_end"))
    return RetrievedResearchChunk(
        chunk_id=parent_chunk_id or str(metadata.get("chunk_id") or ""),
        material_id=str(metadata.get("material_id") or ""),
        fund_code=str(metadata.get("fund_code") or ""),
        fund_name=str(metadata.get("fund_name") or "") or None,
        chunk_index=int(metadata.get("chunk_index") or 0),
        evidence_text=evidence_text,
        relevance_score=score,
        source_type=metadata.get("source_type") or "report",
        title=str(metadata.get("title") or ""),
        source_name=metadata.get("source_name") or None,
        source_url=metadata.get("source_url") or None,
        publish_date=publish_date,
        file_name=metadata.get("file_name") or None,
        original_file_path=metadata.get("original_file_path") or None,
        parent_chunk_id=parent_chunk_id,
        matched_small_chunk_id=str(metadata.get("chunk_id") or "") or None,
        section_path=str(metadata.get("section_path") or "") or None,
        page_start=page_start,
        page_end=page_end,
        document_type=str(metadata.get("document_type") or "") or None,
        report_period=str(metadata.get("report_period") or "") or None,
        raw_text=raw_text,
    )


def _positive_int_or_none(value: Any) -> int | None:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return None
    return resolved if resolved > 0 else None


def _distance_to_score(distance: float | int | None) -> float:
    if distance is None:
        return 0.0
    try:
        return max(0.0, 1.0 - float(distance))
    except (TypeError, ValueError):
        return 0.0
