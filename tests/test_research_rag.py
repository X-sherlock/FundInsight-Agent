from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.embeddings import HashEmbeddingClient
from fundinsight.research_loader import build_research_document
from fundinsight.research_rag import (
    ResearchIngestionService,
    ResearchRetrievalService,
    extract_text_from_upload,
    select_core_report_chunks,
)
from fundinsight.research_store import ResearchStore
from fundinsight.vector_store import VectorResearchStore


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


def test_ingestion_indexes_text_material_and_retrieves_chunks(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    vector_store = VectorResearchStore(tmp_path / "chroma")
    embedding = HashEmbeddingClient()
    ingestion = ResearchIngestionService(store, vector_store, embedding)

    document = ingestion.import_file_material(
        fund_code="000001",
        title="Fund 000001 news",
        file_name="news.txt",
        content=b"Fund 000001 return improved, while drawdown risk remains visible in the latest material.",
        source_type="news",
        source_name="Example News",
        source_url="https://example.com/news",
        publish_date="2026-05-01",
    )
    chunks = ResearchRetrievalService(store, vector_store, embedding).retrieve_for_report(
        fund_metrics=load_fund_metrics(SAMPLE_INPUT),
        top_k=3,
    )

    assert document.vector_status == "indexed"
    assert document.chunk_count == 1
    assert store.read_material_content("000001", document.material_id)
    assert chunks[0].material_id == document.material_id
    assert chunks[0].source_url == "https://example.com/news"
    assert "drawdown" in chunks[0].evidence_text


def test_retrieval_filters_noisy_web_shell_chunks(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    vector_store = VectorResearchStore(tmp_path / "chroma")
    embedding = HashEmbeddingClient()
    ingestion = ResearchIngestionService(store, vector_store, embedding)
    noisy_content = "\n".join(
        [
            "Fund 000001 login shell",
            "登录",
            "手机号",
            "获取验证码",
            "忘记密码",
            "立即注册",
            "扫码登录",
            "下载APP",
            "首页",
            "基金",
            "股票",
            "板块",
            "课程",
            "Fund 000001 return drawdown manager risk content appears after navigation.",
        ]
    )
    ingestion.import_text_material(
        fund_code="000001",
        title="Noisy web page",
        content=noisy_content,
        source_type="news",
    )
    ingestion.import_text_material(
        fund_code="000001",
        title="Clean research note",
        content="Fund 000001 drawdown risk and manager context are discussed in a clean research note.",
        source_type="report",
    )

    chunks = ResearchRetrievalService(store, vector_store, embedding).retrieve_for_report(
        fund_metrics=load_fund_metrics(SAMPLE_INPUT),
        top_k=3,
    )

    assert chunks
    assert all("获取验证码" not in chunk.evidence_text for chunk in chunks)
    assert any(chunk.title == "Clean research note" for chunk in chunks)


def test_delete_material_removes_vector_records(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    vector_store = VectorResearchStore(tmp_path / "chroma")
    embedding = HashEmbeddingClient()
    ingestion = ResearchIngestionService(store, vector_store, embedding)
    document = ingestion.import_text_material(
        fund_code="000001",
        title="Research note",
        content="Fund 000001 manager and risk note.",
        source_type="report",
    )

    assert ingestion.delete_material("000001", document.material_id) is True
    chunks = ResearchRetrievalService(store, vector_store, embedding).retrieve_for_report(
        fund_metrics=load_fund_metrics(SAMPLE_INPUT),
        top_k=3,
    )
    assert chunks == []


def test_core_report_section_selection_adds_quarterly_report_coverage() -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)
    content = "\n\n".join(
        [
            _long_section(
                "§2 基金产品概况\n投资目标 本基金主要投资于高端制造行业相关上市公司股票。\n"
                "投资策略 本基金在宏观经济分析基础上进行资产配置。\n"
                "业绩比较基准 中证高端装备制造指数收益率×90%+中证全债指数收益率×10%。"
            ),
            _long_section(
                "§3 主要财务指标和基金净值表现\n3.1 主要财务指标\n"
                "本期已实现收益 396,511,487.76，本期利润 101,092,039.64，期末基金资产净值 3,686,694,931.53。"
            ),
            _long_section(
                "4.4 报告期内基金的投资策略和运作分析\n"
                "本报告期内，本基金围绕全球缺电方向配置较多标的，包括储能、海上风电、燃气轮机等方向。"
            ),
            _long_section(
                "5.2 报告期末按行业分类的股票投资组合\n"
                "行业类别 制造业 公允价值 3,117,351,022.95 占基金资产净值比例 71.72%。"
            ),
            _long_section(
                "5.3 报告期末按公允价值占基金资产净值比例大小排序的前十名股票投资明细\n"
                "股票代码 股票名称 数量 公允价值 占基金资产净值比例。"
            ),
        ]
    )
    document = build_research_document(
        fund_code="000001",
        title="示例基金 2026 年第 1 季度报告",
        source_type="report",
        file_name="quarterly.pdf",
        content=content,
    )

    chunks = select_core_report_chunks(
        fund_metrics=metrics,
        material_contents=[(document, content)],
        max_chunks=8,
    )
    evidence = "\n".join(chunk.evidence_text for chunk in chunks)

    assert len(chunks) >= 4
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert "基金产品概况" in evidence
    assert "主要财务指标" in evidence
    assert "投资策略和运作分析" in evidence
    assert "前十名股票投资明细" in evidence
    assert all(chunk.analysis_title is None for chunk in chunks)


def test_extract_text_from_upload_supports_utf8_and_rejects_unknown_type() -> None:
    assert extract_text_from_upload("material.md", "材料正文".encode("utf-8")) == "材料正文"
    try:
        extract_text_from_upload("material.docx", b"body")
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Expected unsupported upload type to fail.")


def _long_section(text: str) -> str:
    return "\n".join([text] + ["本段为季度报告正文，用于保持章节独立分块。"] * 80)
