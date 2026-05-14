import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from fundinsight.research_loader import (
    build_research_document,
    load_research_json,
    normalize_research_content,
    split_research_chunks,
)
from fundinsight.research_models import (
    ResearchChunk,
    ResearchDocument,
    ResearchFusionContext,
    ResearchSignal,
    ResearchSignalBundle,
)
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore


def test_research_models_validate_and_serialize() -> None:
    document = _document()
    chunk = ResearchChunk(
        chunk_id="mat_001_0000",
        material_id=document.material_id,
        fund_code="000001",
        chunk_index=0,
        chunk_text="基金代码 000001 近一年收益为 5.2%。",
    )
    signal = ResearchSignal(
        signal_id="sig_001",
        fund_code="000001",
        material_id=document.material_id,
        chunk_id=chunk.chunk_id,
        signal_type="risk_notice",
        summary="波动风险提示",
        detail="材料提示权益仓位变化可能带来波动。",
        category="risk",
        signal_date=date(2026, 5, 1),
        impact_direction="negative",
        importance="medium",
        confidence=0.8,
        evidence_text="权益仓位变化可能带来净值波动。",
        source_type="report",
        publish_date=date(2026, 5, 1),
    )
    bundle = ResearchSignalBundle(fund_code="000001", signals=[signal], materials=[document])
    context = ResearchFusionContext(
        fund_code="000001",
        risk_notices=[signal],
        source_materials=[document],
        limitations=["仅覆盖导入材料。"],
    )

    payload = bundle.model_dump(mode="json")

    assert payload["generated_at"]
    assert payload["signals"][0]["confidence"] == 0.8
    assert payload["materials"][0]["source_url"] == "https://example.com/material"
    assert context.model_dump(mode="json")["source_materials"][0]["publish_date"] == "2026-05-01"


def test_research_signal_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        ResearchSignal(
            signal_id="sig_001",
            fund_code="000001",
            material_id="mat_001",
            signal_type="positive_factor",
            summary="规模变化",
            confidence=1.1,
            evidence_text="基金规模环比增长。",
            source_type="news",
        )


def test_research_signal_rejects_empty_evidence_text() -> None:
    with pytest.raises(ValidationError):
        ResearchSignal(
            signal_id="sig_001",
            fund_code="000001",
            material_id="mat_001",
            signal_type="positive_factor",
            summary="规模变化",
            confidence=0.5,
            evidence_text="   ",
            source_type="news",
        )


def test_research_store_saves_reads_lists_and_deletes_material(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    document = _document()
    content = "基金代码 000001 的材料正文，包含收益率 5.2%。"

    store.save_material("000001", document, content)

    assert store.read_material_content("000001", "mat_001") == content
    assert store.list_materials("000001") == [document]
    assert store.list_materials("000002") == []
    assert store.load_signal_bundle("000001") is None
    assert store.load_fusion_context("000001") is None

    bundle = ResearchSignalBundle(fund_code="000001", materials=[document])
    context = ResearchFusionContext(fund_code="000001", source_materials=[document])
    store.save_signal_bundle("000001", bundle)
    store.save_fusion_context("000001", context)

    assert store.load_signal_bundle("000001") == bundle
    assert store.load_fusion_context("000001") == context
    assert store.delete_material("000001", "mat_001") is True
    assert store.read_material_content("000001", "mat_001") is None
    assert store.delete_material("000001", "mat_001") is False


def test_research_store_rejects_material_id_path_traversal(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    document = _document(material_id="../evil")

    with pytest.raises(ValueError, match="material_id"):
        store.save_material("000001", document, "content")

    with pytest.raises(ValueError, match="material_id"):
        store.read_material_content("000001", "../evil")


def test_research_service_deduplicates_by_content_hash(tmp_path: Path) -> None:
    service = ResearchMaterialService(ResearchStore(tmp_path / "data"))

    first = service.import_text_material(
        fund_code="000001",
        title="材料一",
        source_type="report",
        source_name="测试来源",
        content="第一段：基金代码 000001，收益率 5.2%。\r\n\r\n第二段：风险暴露保持稳定。",
    )
    second = service.import_text_material(
        fund_code="000001",
        title="材料二",
        source_type="report",
        source_name="测试来源",
        content=" 第一段：基金代码 000001，收益率 5.2%。\n\n第二段：风险暴露保持稳定。 ",
    )

    assert second == first
    assert len(service.list_materials("000001")) == 1
    assert service.get_material_content("000001", first.material_id) == (
        "第一段：基金代码 000001，收益率 5.2%。\n\n第二段：风险暴露保持稳定。"
    )


def test_research_service_rejects_empty_text_import(tmp_path: Path) -> None:
    service = ResearchMaterialService(ResearchStore(tmp_path / "data"))

    with pytest.raises(ValueError, match="empty"):
        service.import_text_material(
            fund_code="000001",
            title="空材料",
            source_type="internal_research",
            content=" \n\t ",
        )


def test_research_content_split_short_and_long_text() -> None:
    short_text = "基金代码 000001 的收益率为 5.2%，回撤为 -3.1%。"
    long_text = "\n\n".join(
        f"第{index}段：基金代码 000001 在本段中保留收益率 {index}.5%，并描述风险暴露变化。"
        for index in range(12)
    )

    assert split_research_chunks(short_text) == [short_text]
    chunks = split_research_chunks(long_text, target_min_chars=80, target_max_chars=160)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 160 for chunk in chunks)
    assert "000001" in chunks[0]
    assert "%" in chunks[0]
    assert normalize_research_content("收益率  5.2%\r\n基金代码\t000001") == "收益率 5.2%\n基金代码 000001"


def test_research_content_split_can_add_overlap_context() -> None:
    text = "\n\n".join(
        f"第{index}段：基金代码 000001 在本段中保留收益率 {index}.5%，并描述风险暴露变化。"
        for index in range(12)
    )

    chunks_without_overlap = split_research_chunks(text, target_min_chars=80, target_max_chars=160)
    chunks_with_overlap = split_research_chunks(text, target_min_chars=80, target_max_chars=160, overlap_chars=30)

    assert len(chunks_with_overlap) == len(chunks_without_overlap)
    assert chunks_with_overlap[1].endswith(chunks_without_overlap[1])
    assert len(chunks_with_overlap[1]) > len(chunks_without_overlap[1])


@pytest.mark.parametrize("field_name", ["content", "text", "body"])
def test_load_research_json_reads_common_text_fields(tmp_path: Path, field_name: str) -> None:
    path = tmp_path / f"{field_name}.json"
    path.write_text(json.dumps({field_name: "材料正文", "title": "标题"}, ensure_ascii=False), encoding="utf-8")

    assert load_research_json(path) == "材料正文"


def test_build_chunks_for_material_uses_stable_chunk_ids(tmp_path: Path) -> None:
    service = ResearchMaterialService(ResearchStore(tmp_path / "data"))
    document = service.import_text_material(
        fund_code="000001",
        title="长材料",
        source_type="announcement",
        content="\n\n".join(f"第{index}段：基金代码 000001 的公告内容。" for index in range(180)),
    )

    chunks = service.build_chunks_for_material("000001", document.material_id)

    assert len(chunks) > 1
    assert chunks[0].chunk_id == f"{document.material_id}_0000"
    assert chunks[0].chunk_index == 0
    assert chunks[0].material_id == document.material_id


def _document(material_id: str = "mat_001") -> ResearchDocument:
    return build_research_document(
        material_id=material_id,
        fund_code="000001",
        title="示例投研材料",
        source_type="report",
        source_name="测试来源",
        source_url="https://example.com/material",
        publish_date=date(2026, 5, 1),
        file_name="material.txt",
        content="基金代码 000001 的材料正文。",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
