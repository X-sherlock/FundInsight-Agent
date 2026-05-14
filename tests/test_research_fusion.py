from datetime import date, datetime, timezone

from fundinsight.research_fusion import (
    EMPTY_RESEARCH_LIMITATION,
    build_research_fusion_context,
    save_or_build_fusion_context,
)
from fundinsight.research_loader import build_research_document
from fundinsight.research_models import ResearchSignal, ResearchSignalBundle
from fundinsight.research_store import ResearchStore


def test_fusion_groups_signals_by_type() -> None:
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1")],
        signals=[
            _signal("positive_factor", "positive", "mat_1"),
            _signal("risk_notice", "risk", "mat_1"),
            _signal("key_event", "event", "mat_1"),
            _signal("view_change", "view", "mat_1"),
        ],
    )

    context = build_research_fusion_context("000001", bundle)

    assert [signal.summary for signal in context.positive_factors] == ["positive"]
    assert [signal.summary for signal in context.risk_notices] == ["risk"]
    assert [signal.summary for signal in context.key_events] == ["event"]
    assert [signal.summary for signal in context.view_changes] == ["view"]


def test_fusion_applies_top_n_per_type() -> None:
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1")],
        signals=[
            _signal("positive_factor", "high one", "mat_1", importance="high", confidence=0.7),
            _signal("positive_factor", "high two", "mat_1", importance="high", confidence=0.8),
            _signal("positive_factor", "medium", "mat_1", importance="medium", confidence=0.9),
        ],
    )

    context = build_research_fusion_context("000001", bundle, top_n_per_type=2)

    assert [signal.summary for signal in context.positive_factors] == ["high two", "high one"]


def test_fusion_sorts_by_importance_confidence_publish_date_and_source_type() -> None:
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1"), _material("mat_2"), _material("mat_3"), _material("mat_4")],
        signals=[
            _signal("risk_notice", "medium high confidence", "mat_1", importance="medium", confidence=0.95),
            _signal("risk_notice", "high old report", "mat_2", importance="high", confidence=0.8, publish_date=date(2026, 4, 1), source_type="report"),
            _signal("risk_notice", "high new news", "mat_3", importance="high", confidence=0.8, publish_date=date(2026, 5, 1), source_type="news"),
            _signal("risk_notice", "high new announcement", "mat_4", importance="high", confidence=0.8, publish_date=date(2026, 5, 1), source_type="announcement"),
        ],
    )

    context = build_research_fusion_context("000001", bundle)

    assert [signal.summary for signal in context.risk_notices] == [
        "high new announcement",
        "high new news",
        "high old report",
        "medium high confidence",
    ]


def test_fusion_deduplicates_by_normalized_summary() -> None:
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1")],
        signals=[
            _signal("positive_factor", "Scale improved", "mat_1", confidence=0.9),
            _signal("positive_factor", "Scale   improved", "mat_1", confidence=0.8),
        ],
    )

    context = build_research_fusion_context("000001", bundle)

    assert [signal.summary for signal in context.positive_factors] == ["Scale improved"]


def test_fusion_keeps_only_selected_source_materials() -> None:
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1"), _material("mat_2")],
        signals=[
            _signal("positive_factor", "selected", "mat_1"),
        ],
    )

    context = build_research_fusion_context("000001", bundle)

    assert [material.material_id for material in context.source_materials] == ["mat_1"]


def test_fusion_records_all_analyzed_materials_separately_from_selected_sources() -> None:
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1"), _material("mat_2"), _material("mat_3")],
        signals=[
            _signal("positive_factor", "selected one", "mat_1"),
            _signal("risk_notice", "selected two", "mat_2"),
        ],
    )

    context = build_research_fusion_context("000001", bundle)

    assert [material.material_id for material in context.analyzed_materials] == ["mat_1", "mat_2", "mat_3"]
    assert {material.material_id for material in context.source_materials} == {"mat_1", "mat_2"}
    counts = {material.material_id: material.signal_count for material in context.analyzed_materials}
    assert counts == {"mat_1": 1, "mat_2": 1, "mat_3": 0}


def test_fusion_empty_signals_has_limitation() -> None:
    bundle = ResearchSignalBundle(fund_code="000001", materials=[_material("mat_1")], signals=[])

    context = build_research_fusion_context("000001", bundle)

    assert context.positive_factors == []
    assert [material.material_id for material in context.analyzed_materials] == ["mat_1"]
    assert context.limitations == [EMPTY_RESEARCH_LIMITATION]


def test_save_or_build_fusion_context_persists_context(tmp_path) -> None:
    store = ResearchStore(tmp_path / "data")
    bundle = ResearchSignalBundle(
        fund_code="000001",
        materials=[_material("mat_1")],
        signals=[_signal("view_change", "view changed", "mat_1")],
    )
    store.save_signal_bundle("000001", bundle)

    context = save_or_build_fusion_context("000001", store)

    assert store.load_fusion_context("000001") == context
    assert [signal.summary for signal in context.view_changes] == ["view changed"]


def _material(material_id: str):
    return build_research_document(
        material_id=material_id,
        fund_code="000001",
        title=material_id,
        source_type="report",
        publish_date=date(2026, 5, 1),
        content=f"{material_id} content",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )


def _signal(
    signal_type: str,
    summary: str,
    material_id: str,
    *,
    importance: str = "medium",
    confidence: float = 0.8,
    publish_date: date = date(2026, 5, 1),
    source_type: str = "report",
) -> ResearchSignal:
    return ResearchSignal(
        signal_id=f"sig_{signal_type}_{summary.replace(' ', '_')}_{material_id}",
        fund_code="000001",
        material_id=material_id,
        chunk_id=f"{material_id}_0000",
        signal_type=signal_type,
        summary=summary,
        detail="detail",
        category="category",
        signal_date=publish_date,
        impact_direction="neutral",
        importance=importance,
        confidence=confidence,
        evidence_text=f"evidence {summary}",
        source_type=source_type,
        publish_date=publish_date,
    )
