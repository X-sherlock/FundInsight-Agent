from pathlib import Path

from fundinsight.chunking import ChunkingConfig, build_document_blocks, build_parent_chunks, build_small_chunks
from fundinsight.data_loader import load_fund_metrics
from fundinsight.embeddings import HashEmbeddingClient
from fundinsight.research_loader import build_research_document
from fundinsight.research_rag import ResearchIngestionService, ResearchRetrievalService
from fundinsight.research_store import ResearchStore
from fundinsight.vector_store import VectorResearchStore


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_two_level_chunking_uses_detected_title_hierarchy() -> None:
    document = _document()
    text = "\n\n".join(
        [
            "一、整体情况",
            _paragraph("本章节说明基金的阶段性运作情况。", 18),
            "（一）资产配置变化",
            _paragraph("股票和债券仓位在报告期内存在变化。", 18),
        ]
    )

    parents = _parents(document, text)
    small_chunks = [small for parent in parents for small in build_small_chunks(parent, _config())]

    assert len(parents) >= 1
    assert any("整体情况" in " / ".join(parent.section_path) for parent in parents)
    assert small_chunks
    assert all(small.parent_chunk_id for small in small_chunks)
    assert all("章节路径" in small.embedding_text for small in small_chunks)


def test_two_level_chunking_falls_back_to_paragraph_groups_without_titles() -> None:
    document = _document()
    text = "\n\n".join(_paragraph(f"自然段 {index} 描述基金材料中的连续研究内容。", 8) for index in range(10))

    parents = _parents(document, text)

    assert parents
    assert all(parent.text.strip() for parent in parents)
    assert all(parent.page_start >= 1 for parent in parents)


def test_table_like_text_is_kept_together_with_header() -> None:
    document = _document()
    text = "\n\n".join(
        [
            "1. 组合数据",
            "项目    本期数    上期数    变化\n股票仓位    65.20%    61.00%    4.20%\n债券仓位    20.10%    22.00%    -1.90%",
            "表后文字说明这些数据仅用于历史观察。",
        ]
    )

    parents = _parents(document, text)
    small_chunks = [small for parent in parents for small in build_small_chunks(parent, _config())]

    assert any("项目" in parent.text and "股票仓位" in parent.text for parent in parents)
    assert any("项目" in small.raw_text and "股票仓位" in small.raw_text for small in small_chunks)


def test_long_section_is_split_under_parent_max_chars() -> None:
    document = _document()
    text = "\n\n".join(["一、超长章节", _paragraph("这一段用于模拟很长的章节内容。", 420)])
    config = _config(parent_max=900, parent_target=650, parent_min=300)

    parents = _parents(document, text, config)

    assert len(parents) > 1
    assert all(len(parent.text) <= config.parent_chunk_max_chars for parent in parents)


def test_short_sections_merge_with_adjacent_content() -> None:
    document = _document()
    text = "\n\n".join(["一、短节", "很短。", "二、相邻短节", "也很短。", _paragraph("后续内容用于补足上下文。", 20)])
    config = _config(parent_min=300, parent_target=700, parent_max=1200)

    parents = _parents(document, text, config)

    assert len(parents) == 1
    assert "短节" in parents[0].text
    assert "相邻短节" in parents[0].text


def test_retrieval_deduplicates_multiple_small_hits_to_one_parent(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    vector_store = VectorResearchStore(tmp_path / "chroma")
    embedding = HashEmbeddingClient()
    ingestion = ResearchIngestionService(store, vector_store, embedding)
    content = "\n\n".join(["一、重复命中章节", _paragraph("Fund 000001 return drawdown manager risk context.", 120)])

    document = ingestion.import_text_material(
        fund_code="000001",
        title="Fund 000001 annual report 2025",
        content=content,
        source_type="report",
        source_url="https://example.com/report",
    )
    chunks = ResearchRetrievalService(store, vector_store, embedding).retrieve_for_report(
        fund_metrics=load_fund_metrics(SAMPLE_INPUT),
        top_k=12,
    )

    parent_ids = [chunk.parent_chunk_id for chunk in chunks if chunk.material_id == document.material_id]
    assert parent_ids
    assert len(parent_ids) == len(set(parent_ids))
    assert chunks[0].matched_small_chunk_id
    assert chunks[0].fund_name == "示例稳健成长混合基金"
    assert chunks[0].source_url == "https://example.com/report"


def _document():
    return build_research_document(
        fund_code="000001",
        title="Fund 000001 annual report 2025",
        source_type="report",
        source_url="https://example.com/report",
        publish_date="2026-05-01",
        content="content",
    )


def _parents(document, text: str, config: ChunkingConfig | None = None):
    resolved = config or _config()
    blocks = build_document_blocks(text, resolved)
    return build_parent_chunks(
        blocks=blocks,
        material_id=document.material_id,
        fund_code=document.fund_code,
        document_metadata={
            "document_title": document.title,
            "document_type": document.source_type,
            "publish_date": document.publish_date.isoformat() if document.publish_date else None,
            "source_url": document.source_url,
        },
        config=resolved,
    )


def _config(parent_min: int = 220, parent_target: int = 520, parent_max: int = 1000) -> ChunkingConfig:
    return ChunkingConfig(
        parent_chunk_min_chars=parent_min,
        parent_chunk_target_chars=parent_target,
        parent_chunk_max_chars=parent_max,
        small_chunk_min_chars=120,
        small_chunk_target_chars=260,
        small_chunk_max_chars=420,
        small_chunk_overlap_chars=60,
    )


def _paragraph(seed: str, repeat: int) -> str:
    return "".join(f"{seed}{index}。" for index in range(repeat))
