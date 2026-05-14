import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from fundinsight.research_extractor import ResearchExtractionError, ResearchSignalExtractor
from fundinsight.research_fusion import build_research_fusion_context
from fundinsight.research_loader import build_research_document
from fundinsight.research_models import ResearchChunk
from fundinsight.research_pipeline import process_research_materials
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore


class StubLLMClient:
    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("StubLLMClient has no remaining responses.")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_extractor_extracts_normal_json() -> None:
    extractor = ResearchSignalExtractor()
    document = _document()
    chunk = _chunk("Material says risk controls improved and EVIDENCE_POS is clearly stated.")
    llm = StubLLMClient([_output([_signal(evidence_text="EVIDENCE_POS")])])

    signals = extractor.extract_signals_from_chunk(
        fund_code="000001",
        material=document,
        chunk=chunk,
        chunk_text=chunk.chunk_text,
        llm_client=llm,
    )

    assert len(signals) == 1
    assert signals[0].fund_code == "000001"
    assert signals[0].material_id == document.material_id
    assert signals[0].chunk_id == chunk.chunk_id
    assert signals[0].source_type == "report"
    assert signals[0].publish_date == date(2026, 5, 1)
    assert "EVIDENCE_POS" in llm.prompts[0]


def test_extractor_handles_empty_signals() -> None:
    extractor = ResearchSignalExtractor()
    document = _document()
    chunk = _chunk("No extractable item.")
    llm = StubLLMClient([_output([])])

    assert (
        extractor.extract_signals_from_chunk(
            fund_code="000001",
            material=document,
            chunk=chunk,
            chunk_text=chunk.chunk_text,
            llm_client=llm,
        )
        == []
    )


def test_extractor_rejects_invalid_json() -> None:
    with pytest.raises(ResearchExtractionError, match="valid JSON"):
        ResearchSignalExtractor().parse_extraction_output("{not json")


def test_extractor_rejects_missing_signals() -> None:
    with pytest.raises(ResearchExtractionError, match="signals"):
        ResearchSignalExtractor().parse_extraction_output(json.dumps({"items": []}))


def test_extractor_rejects_non_array_signals() -> None:
    with pytest.raises(ResearchExtractionError, match="array"):
        ResearchSignalExtractor().parse_extraction_output(json.dumps({"signals": {}}))


def test_extractor_filters_evidence_not_in_chunk() -> None:
    signals = _extract_one_response(_output([_signal(evidence_text="NOT_IN_TEXT")]))

    assert signals == []


def test_extractor_filters_low_confidence() -> None:
    signals = _extract_one_response(_output([_signal(confidence=0.59, evidence_text="EVIDENCE_POS")]))

    assert signals == []


def test_extractor_neutralizes_advisory_summary() -> None:
    signals = _extract_one_response(
        _output([_signal(summary="建议买入该基金", evidence_text="EVIDENCE_POS")])
    )

    assert len(signals) == 1
    assert "建议买入" not in signals[0].summary


def test_extractor_neutralizes_advisory_detail_but_keeps_original_evidence() -> None:
    signals = _extract_one_response(
        _output(
            [
                _signal(
                    summary="买入评级上调为强烈推荐",
                    detail="建议立即配置，可以重仓，未来收益可达 8%。",
                    evidence_text="买入评级",
                )
            ]
        ),
        chunk_text="Chunk text includes 买入评级 for validation.",
    )

    assert len(signals) == 1
    assert signals[0].evidence_text == "买入评级"
    assert "买入评级" not in signals[0].summary
    assert "强烈推荐" not in signals[0].summary
    assert signals[0].detail is not None
    assert "建议" not in signals[0].detail
    assert "立即配置" not in signals[0].detail
    assert "可以重仓" not in signals[0].detail
    assert "未来收益可达" not in signals[0].detail


def test_extractor_filters_invalid_signal_type() -> None:
    signals = _extract_one_response(_output([_signal(signal_type="buy_recommendation", evidence_text="EVIDENCE_POS")]))

    assert signals == []


def test_extractor_filters_operational_address_noise() -> None:
    evidence = "注册地址 北京市西城区复兴门内大街1号"

    signals = _extract_one_response(
        _output([_signal(summary="材料披露注册地址", evidence_text=evidence)]),
        chunk_text=f"Chunk text includes {evidence} for validation.",
    )

    assert signals == []


def test_extractor_filters_empty_table_label_noise() -> None:
    evidence = "单位净值（05-08）："

    signals = _extract_one_response(
        _output([_signal(summary="单位净值标签", evidence_text=evidence)]),
        chunk_text=f"Chunk text includes {evidence} for validation.",
    )

    assert signals == []


def test_extractor_filters_empty_holding_date_label_noise() -> None:
    evidence = "十大持仓占比 数据截止日期："

    signals = _extract_one_response(
        _output([_signal(summary="十大持仓占比数据截止日期", evidence_text=evidence)]),
        chunk_text=f"Chunk text includes {evidence} for validation.",
    )

    assert signals == []


def test_extractor_filters_nav_and_promotion_noise() -> None:
    evidence = "| 基金交易 | 我的资产"

    signals = _extract_one_response(
        _output([_signal(summary="基金档案导航项", evidence_text=evidence)]),
        chunk_text=f"Chunk text includes {evidence} for validation.",
    )

    assert signals == []


def test_extractor_filters_disclaimer_noise() -> None:
    evidence = "郑重声明：天天基金网发布此信息目的在于传播更多信息，与本网站立场无关。"

    signals = _extract_one_response(
        _output([_signal(summary="网站免责声明", evidence_text=evidence)]),
        chunk_text=f"Chunk text includes {evidence} for validation.",
    )

    assert signals == []


def test_extractor_filters_date_only_holding_noise() -> None:
    evidence = "持仓数据 数据截止至2026-03-31"

    signals = _extract_one_response(
        _output([_signal(summary="持仓数据截止日期", evidence_text=evidence)]),
        chunk_text=f"Chunk text includes {evidence} for validation.",
    )

    assert signals == []


def test_pipeline_processes_single_material_single_chunk(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    document = service.import_text_material(
        fund_code="000001",
        title="single",
        source_type="report",
        publish_date=date(2026, 5, 1),
        content="The material contains EVIDENCE_ONE for extraction.",
    )
    llm = StubLLMClient([_output([_signal(summary="single signal", evidence_text="EVIDENCE_ONE")])])

    bundle = process_research_materials("000001", store, service, ResearchSignalExtractor(), llm_client=llm)

    assert len(bundle.signals) == 1
    assert bundle.materials == [document]
    assert store.load_signal_bundle("000001") == bundle


def test_pipeline_processes_single_material_multiple_chunks(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    document = service.import_text_material(
        fund_code="000001",
        title="multi chunk",
        source_type="report",
        publish_date=date(2026, 5, 1),
        content=_long_material("EVIDENCE_ONE", "EVIDENCE_TWO"),
    )
    llm = StubLLMClient(
        [
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO"),
                ]
            ),
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO"),
                ]
            ),
        ]
    )

    bundle = process_research_materials("000001", store, service, ResearchSignalExtractor(), llm_client=llm)

    assert len(service.build_chunks_for_material("000001", document.material_id)) == 2
    assert [signal.summary for signal in bundle.signals] == ["first signal", "second signal"]


def test_pipeline_processes_multiple_materials(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    first = service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    second = service.import_text_material(
        fund_code="000001",
        title="second",
        source_type="news",
        content="Second material has EVIDENCE_TWO.",
    )
    llm = StubLLMClient(
        [
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO"),
                ]
            ),
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO"),
                ]
            ),
        ]
    )

    bundle = process_research_materials("000001", store, service, ResearchSignalExtractor(), llm_client=llm)

    assert {material.material_id for material in bundle.materials} == {first.material_id, second.material_id}
    assert len(bundle.signals) == 2


def test_pipeline_processes_three_materials_and_fusion_records_analyzed_sources(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    first = service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    second = service.import_text_material(
        fund_code="000001",
        title="second",
        source_type="announcement",
        content="Second material has EVIDENCE_TWO.",
    )
    third = service.import_text_material(
        fund_code="000001",
        title="third",
        source_type="news",
        content="Third material has EVIDENCE_THREE.",
    )
    llm = StubLLMClient(
        [
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO", signal_type="risk_notice"),
                    _signal(summary="third signal", evidence_text="EVIDENCE_THREE", signal_type="key_event"),
                ]
            ),
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO", signal_type="risk_notice"),
                    _signal(summary="third signal", evidence_text="EVIDENCE_THREE", signal_type="key_event"),
                ]
            ),
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="second signal", evidence_text="EVIDENCE_TWO", signal_type="risk_notice"),
                    _signal(summary="third signal", evidence_text="EVIDENCE_THREE", signal_type="key_event"),
                ]
            ),
        ]
    )

    bundle = process_research_materials("000001", store, service, ResearchSignalExtractor(), llm_client=llm)
    context = build_research_fusion_context("000001", bundle)

    assert {material.material_id for material in bundle.materials} == {
        first.material_id,
        second.material_id,
        third.material_id,
    }
    assert {signal.material_id for signal in bundle.signals} == {
        first.material_id,
        second.material_id,
        third.material_id,
    }
    assert {material.material_id for material in context.analyzed_materials} == {
        first.material_id,
        second.material_id,
        third.material_id,
    }
    assert {material.material_id for material in context.source_materials} == {
        first.material_id,
        second.material_id,
        third.material_id,
    }


def test_pipeline_processes_selected_material_ids(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    first = service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    second = service.import_text_material(
        fund_code="000001",
        title="second",
        source_type="news",
        content="Second material has EVIDENCE_TWO.",
    )
    llm = StubLLMClient([_output([_signal(summary="second signal", evidence_text="EVIDENCE_TWO")])])

    bundle = process_research_materials(
        "000001",
        store,
        service,
        ResearchSignalExtractor(),
        material_ids=[second.material_id],
        llm_client=llm,
    )

    assert [material.material_id for material in bundle.materials] == [second.material_id]
    assert first.material_id not in {signal.material_id for signal in bundle.signals}


def test_pipeline_processes_only_two_selected_material_ids(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    first = service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    second = service.import_text_material(
        fund_code="000001",
        title="second",
        source_type="announcement",
        content="Second material has EVIDENCE_TWO.",
    )
    third = service.import_text_material(
        fund_code="000001",
        title="third",
        source_type="news",
        content="Third material has EVIDENCE_THREE.",
    )
    llm = StubLLMClient(
        [
            _output([_signal(summary="first signal", evidence_text="EVIDENCE_ONE")]),
            _output([_signal(summary="third signal", evidence_text="EVIDENCE_THREE")]),
        ]
    )

    bundle = process_research_materials(
        "000001",
        store,
        service,
        ResearchSignalExtractor(),
        material_ids=[first.material_id, third.material_id],
        llm_client=llm,
    )

    assert {material.material_id for material in bundle.materials} == {first.material_id, third.material_id}
    assert second.material_id not in {signal.material_id for signal in bundle.signals}


def test_pipeline_skips_missing_material_ids(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    document = service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    llm = StubLLMClient([_output([_signal(summary="first signal", evidence_text="EVIDENCE_ONE")])])

    bundle = process_research_materials(
        "000001",
        store,
        service,
        ResearchSignalExtractor(),
        material_ids=["missing", document.material_id],
        llm_client=llm,
    )

    assert len(bundle.signals) == 1


def test_pipeline_reuses_existing_bundle_when_not_forced(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    first = process_research_materials(
        "000001",
        store,
        service,
        ResearchSignalExtractor(),
        force_reextract=True,
        llm_client=StubLLMClient([_output([_signal(summary="first signal", evidence_text="EVIDENCE_ONE")])]),
    )

    reused = process_research_materials(
        "000001",
        store,
        service,
        ResearchSignalExtractor(),
        llm_client=StubLLMClient([RuntimeError("should not be called")]),
    )

    assert reused == first


def test_pipeline_continues_when_one_chunk_fails(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    service.import_text_material(
        fund_code="000001",
        title="multi chunk",
        source_type="report",
        content=_long_material("EVIDENCE_ONE", "EVIDENCE_TWO"),
    )
    llm = StubLLMClient(
        [
            RuntimeError("chunk failed"),
            _output([_signal(summary="second signal", evidence_text="EVIDENCE_TWO")]),
        ]
    )

    bundle = process_research_materials("000001", store, service, ResearchSignalExtractor(), llm_client=llm)

    assert [signal.summary for signal in bundle.signals] == ["second signal"]


def test_pipeline_continues_when_one_material_content_is_broken(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    first = service.import_text_material(
        fund_code="000001",
        title="first",
        source_type="report",
        content="First material has EVIDENCE_ONE.",
    )
    broken = service.import_text_material(
        fund_code="000001",
        title="broken",
        source_type="news",
        content="Broken material has EVIDENCE_BROKEN.",
    )
    third = service.import_text_material(
        fund_code="000001",
        title="third",
        source_type="announcement",
        content="Third material has EVIDENCE_THREE.",
    )
    (store.materials_dir("000001") / f"{broken.material_id}.txt").unlink()
    llm = StubLLMClient(
        [
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="third signal", evidence_text="EVIDENCE_THREE"),
                ]
            ),
            _output(
                [
                    _signal(summary="first signal", evidence_text="EVIDENCE_ONE"),
                    _signal(summary="third signal", evidence_text="EVIDENCE_THREE"),
                ]
            ),
        ]
    )

    bundle = process_research_materials("000001", store, service, ResearchSignalExtractor(), llm_client=llm)

    assert {material.material_id for material in bundle.materials} == {first.material_id, third.material_id}
    assert {signal.material_id for signal in bundle.signals} == {first.material_id, third.material_id}


def test_store_skips_corrupt_material_metadata(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)
    document = service.import_text_material(
        fund_code="000001",
        title="valid",
        source_type="report",
        content="Valid material has EVIDENCE_ONE.",
    )
    corrupt_path = store.materials_dir("000001") / "mat_corrupt.json"
    corrupt_path.write_text("{not json", encoding="utf-8")

    materials = store.list_materials("000001")

    assert [material.material_id for material in materials] == [document.material_id]


def test_pipeline_returns_empty_bundle_without_materials(tmp_path: Path) -> None:
    store, service = _store_and_service(tmp_path)

    bundle = process_research_materials(
        "000001",
        store,
        service,
        ResearchSignalExtractor(),
        llm_client=StubLLMClient([RuntimeError("should not be called")]),
    )

    assert bundle.signals == []
    assert bundle.materials == []


def _extract_one_response(raw_output: str, chunk_text: str = "Chunk text includes EVIDENCE_POS for validation."):
    extractor = ResearchSignalExtractor()
    document = _document()
    chunk = _chunk(chunk_text)
    return extractor.extract_signals_from_chunk(
        fund_code="000001",
        material=document,
        chunk=chunk,
        chunk_text=chunk.chunk_text,
        llm_client=StubLLMClient([raw_output]),
    )


def _output(signals: list[dict]) -> str:
    return json.dumps({"signals": signals}, ensure_ascii=False)


def _signal(
    *,
    signal_type: str = "positive_factor",
    summary: str = "risk controls improved",
    detail: str = "detail",
    category: str = "operations",
    signal_date: str | None = "2026-05-01",
    impact_direction: str = "positive",
    importance: str = "medium",
    confidence: float = 0.8,
    evidence_text: str = "EVIDENCE_POS",
) -> dict:
    return {
        "signal_type": signal_type,
        "summary": summary,
        "detail": detail,
        "category": category,
        "signal_date": signal_date,
        "impact_direction": impact_direction,
        "importance": importance,
        "confidence": confidence,
        "evidence_text": evidence_text,
    }


def _store_and_service(tmp_path: Path) -> tuple[ResearchStore, ResearchMaterialService]:
    store = ResearchStore(tmp_path / "data")
    return store, ResearchMaterialService(store)


def _document():
    return build_research_document(
        material_id="mat_001",
        fund_code="000001",
        title="material",
        source_type="report",
        publish_date=date(2026, 5, 1),
        content="Chunk text includes EVIDENCE_POS for validation.",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )


def _chunk(text: str) -> ResearchChunk:
    return ResearchChunk(
        chunk_id="mat_001_0000",
        material_id="mat_001",
        fund_code="000001",
        chunk_index=0,
        chunk_text=text,
    )


def _long_material(first_evidence: str, second_evidence: str) -> str:
    first = f"First paragraph {first_evidence}. " + ("alpha " * 350)
    second = f"Second paragraph {second_evidence}. " + ("beta " * 420)
    return f"{first}\n\n{second}"
