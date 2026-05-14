"""RAG ingestion, retrieval, and fact-card construction for fund reports."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from typing import Any, cast

from fundinsight.chunking import ChunkingConfig, build_document_blocks, build_parent_chunks, build_small_chunks
from fundinsight.embeddings import EmbeddingClient, get_default_embedding_client
from fundinsight.models import FundMetricsInput
from fundinsight.research_loader import (
    build_research_document,
    compute_content_hash,
    normalize_research_content,
    split_research_chunks,
)
from fundinsight.research_models import (
    FactCard,
    FactCardSourceMaterial,
    ResearchChunk,
    ResearchDocument,
    RetrievedResearchChunk,
    SourceType,
)
from fundinsight.research_store import ResearchStore
from fundinsight.vector_store import VectorChunkRecord, VectorResearchStore


RAG_CHUNK_MIN_CHARS = 700
RAG_CHUNK_MAX_CHARS = 1400
RAG_CHUNK_OVERLAP_CHARS = 160
RAG_CHUNKING_CONFIG = ChunkingConfig(
    parent_chunk_min_chars=800,
    parent_chunk_target_chars=1800,
    parent_chunk_max_chars=3000,
    parent_chunk_overlap_chars=0,
    small_chunk_min_chars=250,
    small_chunk_target_chars=700,
    small_chunk_max_chars=1000,
    small_chunk_overlap_chars=100,
)
DEFAULT_RETRIEVAL_TOP_K = 12
MAX_RETRIEVAL_CANDIDATES = 48
CORE_REPORT_SECTION_TOP_K = 8
CORE_REPORT_SECTION_PATTERNS = (
    (
        "product_profile",
        re.compile(r"(基金产品概况|投资目标|投资策略|业绩比较基准|风险收益特征)"),
        0.96,
    ),
    (
        "financial_indicators",
        re.compile(r"(主要财务指标|本期已实现收益|本期利润|期末基金资产净值|期末基金份额净值)"),
        0.95,
    ),
    (
        "nav_performance",
        re.compile(r"(基金净值表现|净值增长率|业绩比较基准收益率|过去三个月|过去一年)"),
        0.94,
    ),
    (
        "operation_analysis",
        re.compile(r"(投资策略和运作分析|报告期内基金的投资策略|市场.*主题|配置.*方向)"),
        0.98,
    ),
    (
        "industry_allocation",
        re.compile(r"(按行业分类的股票投资组合|行业类别|制造业|股票投资组合)"),
        0.97,
    ),
    (
        "top_holdings",
        re.compile(r"(前十名股票投资明细|股票代码|股票名称|占基金资产净值比例)"),
        0.97,
    ),
    (
        "portfolio_notes",
        re.compile(r"(投资组合报告附注|流通受限|其他资产构成|债券投资明细)"),
        0.92,
    ),
)
WEB_SHELL_MARKERS = (
    "登录",
    "手机号",
    "获取验证码",
    "忘记密码",
    "立即注册",
    "扫码登录",
    "下载APP",
    "客服电话",
    "收藏本站",
    "安全登录",
    "安全退出",
    "网站导航",
    "热点推荐",
    "帮助中心",
    "鐧诲綍",
    "鎵嬫満",
    "楠岃瘉",
    "蹇樿瀵嗙爜",
    "绔嬪嵆娉ㄥ唽",
    "涓嬭浇APP",
    "瀹夊叏鐧诲綍",
)


class ResearchIngestionService:
    def __init__(
        self,
        store: ResearchStore | None = None,
        vector_store: VectorResearchStore | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.store = store or ResearchStore()
        self.vector_store = vector_store or _vector_store_for_research_store(self.store)
        self.embedding_client = embedding_client or get_default_embedding_client()

    def import_file_material(
        self,
        *,
        fund_code: str,
        fund_name: str | None = None,
        title: str,
        file_name: str,
        content: bytes,
        source_type: SourceType,
        source_name: str | None = None,
        source_url: str | None = None,
        publish_date: date | str | None = None,
    ) -> ResearchDocument:
        text = extract_text_from_upload(file_name, content)
        return self.import_text_material(
            fund_code=fund_code,
            fund_name=fund_name,
            title=title,
            content=text,
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            publish_date=publish_date,
            file_name=file_name,
            original_bytes=content,
        )

    def import_text_material(
        self,
        *,
        fund_code: str,
        fund_name: str | None = None,
        title: str,
        content: str,
        source_type: SourceType,
        source_name: str | None = None,
        source_url: str | None = None,
        publish_date: date | str | None = None,
        file_name: str | None = None,
        original_bytes: bytes | None = None,
    ) -> ResearchDocument:
        normalized = normalize_research_content(content)
        if not normalized:
            raise ValueError("Research material content is empty after normalization.")

        content_hash = compute_content_hash(normalized)
        for existing in self.store.list_materials(fund_code):
            if (
                existing.content_hash == content_hash
                and existing.vector_status == "indexed"
                and existing.parent_chunk_count
            ):
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
        chunks, parent_count = _build_chunks(document, normalized, fund_name=fund_name)
        material_dir = self.store.material_dir(fund_code, document.material_id)
        document = document.model_copy(
            update={
                "chunk_count": len(chunks),
                "parent_chunk_count": parent_count,
                "vector_status": "pending",
                "original_file_path": str(material_dir / _stored_original_name(file_name)) if file_name else None,
                "extracted_text_path": str(material_dir / "extracted.txt"),
            }
        )
        try:
            embeddings = self.embedding_client.embed_texts([chunk.embedding_text or chunk.chunk_text for chunk in chunks])
            self.vector_store.delete_material(fund_code, document.material_id)
            self.vector_store.upsert_chunks(
                [
                    VectorChunkRecord(chunk=chunk, material=document, embedding=embedding)
                    for chunk, embedding in zip(chunks, embeddings)
                ]
            )
            document = document.model_copy(update={"vector_status": "indexed", "vector_error": None})
        except Exception as exc:
            document = document.model_copy(update={"vector_status": "failed", "vector_error": str(exc)})

        self.store.save_material(
            fund_code,
            document,
            normalized,
            original_bytes=original_bytes,
            original_file_name=_stored_original_name(file_name) if file_name else None,
        )
        return document

    def delete_material(self, fund_code: str, material_id: str) -> bool:
        self.vector_store.delete_material(fund_code, material_id)
        return self.store.delete_material(fund_code, material_id)


class ResearchRetrievalService:
    def __init__(
        self,
        store: ResearchStore | None = None,
        vector_store: VectorResearchStore | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.store = store or ResearchStore()
        self.vector_store = vector_store or _vector_store_for_research_store(self.store)
        self.embedding_client = embedding_client or get_default_embedding_client()

    def retrieve_for_report(
        self,
        *,
        fund_metrics: FundMetricsInput,
        top_k: int = DEFAULT_RETRIEVAL_TOP_K,
        material_ids: list[str] | None = None,
    ) -> list[RetrievedResearchChunk]:
        query = _report_retrieval_query(fund_metrics)
        query_embedding = self.embedding_client.embed_texts([query])[0]
        candidate_top_k = min(max(top_k * 4, top_k), MAX_RETRIEVAL_CANDIDATES)
        chunks = self.vector_store.query(
            fund_code=fund_metrics.fund.code,
            query_embedding=query_embedding,
            top_k=candidate_top_k,
            material_ids=material_ids,
        )
        deduped = _dedupe_parent_chunks(_filter_retrieved_chunks(chunks))[:top_k]
        return [
            chunk if chunk.fund_name else chunk.model_copy(update={"fund_name": fund_metrics.fund.name})
            for chunk in deduped
        ]


def select_core_report_chunks(
    *,
    fund_metrics: FundMetricsInput,
    material_contents: list[tuple[ResearchDocument, str]],
    max_chunks: int = CORE_REPORT_SECTION_TOP_K,
) -> list[RetrievedResearchChunk]:
    """Select representative quarterly-report sections beyond semantic top-k retrieval."""

    if max_chunks <= 0:
        return []

    selected_by_label: dict[str, RetrievedResearchChunk] = {}
    for material, content in material_contents:
        if material.source_type != "report":
            continue
        chunks, _ = _build_chunks(material, content, fund_name=fund_metrics.fund.name)
        parent_chunks = _unique_parent_research_chunks(chunks)
        for chunk in parent_chunks:
            text = "\n".join(
                value
                for value in (
                    chunk.section_path,
                    chunk.parent_chunk_text,
                    chunk.raw_text,
                    chunk.chunk_text,
                )
                if value
            )
            if not text.strip():
                continue
            for label, pattern, score in CORE_REPORT_SECTION_PATTERNS:
                if label in selected_by_label:
                    continue
                if pattern.search(text):
                    retrieved = _retrieved_chunk_from_research_chunk(
                        chunk=chunk,
                        material=material,
                        fund_name=fund_metrics.fund.name,
                        relevance_score=score,
                    )
                    if _is_usable_retrieved_chunk(retrieved):
                        selected_by_label[label] = retrieved
                    break

    selected = [
        selected_by_label[label]
        for label, _, _ in CORE_REPORT_SECTION_PATTERNS
        if label in selected_by_label
    ]
    return selected[:max_chunks]


def merge_retrieved_chunks(
    *chunks_groups: list[RetrievedResearchChunk],
    limit: int,
) -> list[RetrievedResearchChunk]:
    """Merge retrieved chunks by parent context while keeping strongest scores first."""

    if limit <= 0:
        return []
    merged: list[RetrievedResearchChunk] = []
    for chunks in chunks_groups:
        merged.extend(chunks)
    return _dedupe_parent_chunks(_filter_retrieved_chunks(merged))[:limit]


def build_fact_card(
    *,
    fund_metrics: FundMetricsInput,
    derived_metrics: dict[str, Any],
    metric_tables: dict[str, Any],
    missing_fields: list[str],
    data_notes: list[str],
    retrieved_chunks: list[RetrievedResearchChunk],
) -> FactCard:
    source_materials = _source_materials_from_chunks(retrieved_chunks)
    limitations: list[str] = []
    if not retrieved_chunks:
        limitations.append("未检索到可用于本次报告的相关材料片段。")
    return FactCard(
        fund_code=fund_metrics.fund.code,
        source_metrics=fund_metrics.to_prompt_payload(),
        derived_metrics=derived_metrics,
        metric_tables=metric_tables,
        missing_fields=missing_fields,
        data_notes=data_notes,
        retrieved_chunks=retrieved_chunks,
        source_materials=source_materials,
        limitations=limitations,
    )


def extract_text_from_upload(file_name: str, content: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix in {".txt", ".md"}:
        return _decode_text(content)
    if suffix == ".pdf":
        return _extract_pdf_text(content)
    raise ValueError("Unsupported material file type. Supported types: PDF, TXT, MD.")


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF text extraction requires the pypdf package.") from exc

    import io

    reader = PdfReader(io.BytesIO(content))
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if not text.strip():
        raise ValueError("PDF does not contain extractable text; OCR is not supported in this phase.")
    return text


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _build_chunks(document: ResearchDocument, content: str, *, fund_name: str | None = None) -> tuple[list[ResearchChunk], int]:
    blocks = build_document_blocks(content, RAG_CHUNKING_CONFIG)
    document_metadata = _document_metadata(document, fund_name=fund_name)
    parent_chunks = build_parent_chunks(
        blocks=blocks,
        material_id=document.material_id,
        fund_code=document.fund_code,
        document_metadata=document_metadata,
        config=RAG_CHUNKING_CONFIG,
    )
    if not parent_chunks:
        legacy_chunks = [
            ResearchChunk(
                chunk_id=f"{document.material_id}_{index:04d}",
                material_id=document.material_id,
                fund_code=document.fund_code,
                fund_name=fund_name,
                chunk_index=index,
                chunk_text=chunk_text,
                raw_text=chunk_text,
                embedding_text=chunk_text,
                document_title=document.title,
                document_type=document.source_type,
                publish_date=document.publish_date,
                source_url=document.source_url,
            )
            for index, chunk_text in enumerate(
                split_research_chunks(
                    content,
                    target_min_chars=RAG_CHUNK_MIN_CHARS,
                    target_max_chars=RAG_CHUNK_MAX_CHARS,
                    overlap_chars=RAG_CHUNK_OVERLAP_CHARS,
                )
            )
        ]
        return legacy_chunks, 0

    small_chunks = [small for parent in parent_chunks for small in build_small_chunks(parent, RAG_CHUNKING_CONFIG)]
    research_chunks: list[ResearchChunk] = []
    parent_by_id = {parent.parent_chunk_id: parent for parent in parent_chunks}
    for index, small in enumerate(small_chunks):
        parent = parent_by_id[small.parent_chunk_id]
        research_chunks.append(
            ResearchChunk(
                chunk_id=small.chunk_id,
                material_id=small.material_id,
                fund_code=small.fund_code,
                fund_name=fund_name,
                chunk_index=index,
                chunk_text=small.embedding_text,
                parent_chunk_id=small.parent_chunk_id,
                chunk_level="small",
                chunk_index_in_parent=small.chunk_index_in_parent,
                embedding_text=small.embedding_text,
                raw_text=small.raw_text,
                parent_chunk_text=parent.text,
                section_path=" / ".join(small.section_path),
                page_start=small.page_start,
                page_end=small.page_end,
                block_start_index=parent.block_start_index,
                block_end_index=parent.block_end_index,
                document_title=document.title,
                document_type=document.source_type,
                report_period=str(document_metadata.get("report_period") or "") or None,
                publish_date=document.publish_date,
                source_url=document.source_url,
            )
        )
    return research_chunks, len(parent_chunks)


def _source_materials_from_chunks(chunks: list[RetrievedResearchChunk]) -> list[FactCardSourceMaterial]:
    by_id: dict[str, FactCardSourceMaterial] = {}
    chunk_counts: dict[str, int] = {}
    for chunk in chunks:
        chunk_counts[chunk.material_id] = chunk_counts.get(chunk.material_id, 0) + 1
        by_id.setdefault(
            chunk.material_id,
            FactCardSourceMaterial(
                material_id=chunk.material_id,
                title=chunk.title,
                source_type=chunk.source_type,
                source_name=chunk.source_name,
                source_url=chunk.source_url,
                publish_date=chunk.publish_date,
                file_name=chunk.file_name,
                original_file_path=chunk.original_file_path,
                chunk_count=0,
            ),
        )
    return [
        material.model_copy(update={"chunk_count": chunk_counts.get(material.material_id, 0)})
        for material in by_id.values()
    ]


def _unique_parent_research_chunks(chunks: list[ResearchChunk]) -> list[ResearchChunk]:
    by_context_id: dict[str, ResearchChunk] = {}
    for chunk in chunks:
        context_id = chunk.parent_chunk_id or chunk.chunk_id
        by_context_id.setdefault(context_id, chunk)
    return list(by_context_id.values())


def _retrieved_chunk_from_research_chunk(
    *,
    chunk: ResearchChunk,
    material: ResearchDocument,
    fund_name: str,
    relevance_score: float,
) -> RetrievedResearchChunk:
    evidence_text = (chunk.parent_chunk_text or chunk.raw_text or chunk.chunk_text).strip()
    parent_chunk_id = chunk.parent_chunk_id or None
    return RetrievedResearchChunk(
        chunk_id=parent_chunk_id or chunk.chunk_id,
        material_id=material.material_id,
        fund_code=material.fund_code,
        fund_name=chunk.fund_name or fund_name,
        chunk_index=chunk.chunk_index,
        evidence_text=evidence_text,
        relevance_score=relevance_score,
        source_type=material.source_type,
        title=material.title,
        source_name=material.source_name,
        source_url=chunk.source_url or material.source_url,
        publish_date=chunk.publish_date or material.publish_date,
        file_name=material.file_name,
        original_file_path=material.original_file_path,
        parent_chunk_id=parent_chunk_id,
        matched_small_chunk_id=chunk.chunk_id if parent_chunk_id else None,
        section_path=chunk.section_path,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        document_type=chunk.document_type or material.source_type,
        report_period=chunk.report_period,
        raw_text=chunk.raw_text,
    )


def _filter_retrieved_chunks(chunks: list[RetrievedResearchChunk]) -> list[RetrievedResearchChunk]:
    return [chunk for chunk in chunks if _is_usable_retrieved_chunk(chunk)]


def _dedupe_parent_chunks(chunks: list[RetrievedResearchChunk]) -> list[RetrievedResearchChunk]:
    by_context_id: dict[str, RetrievedResearchChunk] = {}
    for chunk in chunks:
        context_id = chunk.parent_chunk_id or chunk.chunk_id
        current = by_context_id.get(context_id)
        if current is None or chunk.relevance_score > current.relevance_score:
            by_context_id[context_id] = chunk
    return sorted(by_context_id.values(), key=lambda chunk: chunk.relevance_score, reverse=True)


def _is_usable_retrieved_chunk(chunk: RetrievedResearchChunk) -> bool:
    text = chunk.evidence_text.strip()
    if not text:
        return False
    if _looks_like_web_shell(text):
        return False
    return True


def _looks_like_web_shell(text: str) -> bool:
    marker_count = sum(1 for marker in WEB_SHELL_MARKERS if marker in text)
    if marker_count < 4:
        return False
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    short_line_ratio = sum(1 for line in lines if len(line) <= 12) / max(len(lines), 1)
    first_section = "\n".join(lines[:40])
    first_section_marker_count = sum(1 for marker in WEB_SHELL_MARKERS if marker in first_section)
    dense_menu_words = len(re.findall(r"(登录|基金|股票|板块|课程|首页|搜索|财富|鐧诲綍|鍩洪噾|鑲＄エ)", first_section))
    return first_section_marker_count >= 3 or (short_line_ratio > 0.55 and dense_menu_words >= 8)


def _report_retrieval_query(fund_metrics: FundMetricsInput) -> str:
    benchmark = fund_metrics.resolved_benchmark.name
    return "\n".join(
        [
            fund_metrics.fund.code,
            fund_metrics.fund.name,
            fund_metrics.fund.type,
            fund_metrics.category.name,
            benchmark,
            "收益 风险 回撤 波动 持仓 行业 基金经理 公告 新闻 研报",
        ]
    )


def _document_metadata(document: ResearchDocument, *, fund_name: str | None = None) -> dict[str, Any]:
    return {
        "fund_code": document.fund_code,
        "fund_name": fund_name,
        "document_id": document.material_id,
        "document_title": document.title,
        "document_type": document.source_type,
        "report_period": _infer_report_period(document.title, document.publish_date),
        "publish_date": document.publish_date.isoformat() if document.publish_date else None,
        "source_url": document.source_url,
    }


def _infer_report_period(title: str, publish_date: date | None) -> str | None:
    match = re.search(r"(20\d{2})(?:\s*年|\s*[-/]?\s*(?:Q[1-4]|一季|半年|三季|年报|年度))?", title)
    if match:
        return match.group(0).strip()
    if publish_date is not None:
        return str(publish_date.year)
    return None


def _stored_original_name(file_name: str | None) -> str:
    if not file_name:
        return "original.txt"
    suffix = Path(file_name).suffix.lower() or ".txt"
    return cast(str, f"original{suffix}")


def _vector_store_for_research_store(store: ResearchStore) -> VectorResearchStore:
    vector_root = store.data_root / "vector_store"
    return VectorResearchStore(persist_directory=vector_root / "chroma")
