"""Build fusion context from extracted research signals."""

from __future__ import annotations

import re
from datetime import date

from fundinsight.research_models import ResearchDocument, ResearchFusionContext, ResearchSignal, ResearchSignalBundle
from fundinsight.research_store import ResearchStore


EMPTY_RESEARCH_LIMITATION = "暂无可用非结构化投研材料。"
LIMITED_COVERAGE_LIMITATION = "投研材料覆盖范围有限，融合上下文仅包含部分高置信度信号。"
SIGNAL_FIELD_BY_TYPE = {
    "positive_factor": "positive_factors",
    "risk_notice": "risk_notices",
    "key_event": "key_events",
    "view_change": "view_changes",
}
IMPORTANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1, None: 0}
SOURCE_TYPE_WEIGHT = {
    "announcement": 4,
    "internal_research": 4,
    "report": 3,
    "news": 2,
}


def build_research_fusion_context(
    fund_code: str,
    bundle: ResearchSignalBundle,
    lookback_months: int = 12,
    top_n_per_type: int = 5,
) -> ResearchFusionContext:
    """Group, rank, deduplicate, and limit extracted signals for report fusion."""

    if not bundle.materials or not bundle.signals:
        return ResearchFusionContext(
            fund_code=fund_code,
            source_materials=[],
            limitations=[EMPTY_RESEARCH_LIMITATION],
        )

    reference_date = _reference_date(bundle.signals)
    selected_by_type: dict[str, list[ResearchSignal]] = {}
    filtered_count = 0

    for signal_type in SIGNAL_FIELD_BY_TYPE:
        typed = [signal for signal in bundle.signals if signal.signal_type == signal_type]
        recent = [signal for signal in typed if _is_within_lookback(signal.publish_date, reference_date, lookback_months)]
        candidates = recent if recent else typed
        filtered_count += len(typed) - len(candidates)
        deduplicated = _deduplicate_by_summary(_sort_signals(candidates))
        selected = deduplicated[:top_n_per_type]
        filtered_count += max(0, len(deduplicated) - len(selected))
        selected_by_type[signal_type] = selected

    selected_signals = [
        signal
        for signal_type in SIGNAL_FIELD_BY_TYPE
        for signal in selected_by_type.get(signal_type, [])
    ]
    if not selected_signals:
        return ResearchFusionContext(
            fund_code=fund_code,
            source_materials=[],
            limitations=[EMPTY_RESEARCH_LIMITATION],
        )

    limitations: list[str] = []
    if filtered_count > 0:
        limitations.append(LIMITED_COVERAGE_LIMITATION)

    return ResearchFusionContext(
        fund_code=fund_code,
        positive_factors=selected_by_type["positive_factor"],
        risk_notices=selected_by_type["risk_notice"],
        key_events=selected_by_type["key_event"],
        view_changes=selected_by_type["view_change"],
        source_materials=_selected_materials(bundle.materials, selected_signals),
        limitations=limitations,
    )


def save_or_build_fusion_context(
    fund_code: str,
    store: ResearchStore,
    lookback_months: int = 12,
    top_n_per_type: int = 5,
) -> ResearchFusionContext:
    """Build fusion context from saved signals and persist it."""

    bundle = store.load_signal_bundle(fund_code)
    if bundle is None:
        context = ResearchFusionContext(
            fund_code=fund_code,
            source_materials=[],
            limitations=[EMPTY_RESEARCH_LIMITATION],
        )
    else:
        context = build_research_fusion_context(
            fund_code=fund_code,
            bundle=bundle,
            lookback_months=lookback_months,
            top_n_per_type=top_n_per_type,
        )
    store.save_fusion_context(fund_code, context)
    return context


def _sort_signals(signals: list[ResearchSignal]) -> list[ResearchSignal]:
    return sorted(
        signals,
        key=lambda signal: (
            IMPORTANCE_WEIGHT.get(signal.importance, 0),
            signal.confidence,
            signal.publish_date or date.min,
            SOURCE_TYPE_WEIGHT.get(signal.source_type, 0),
        ),
        reverse=True,
    )


def _deduplicate_by_summary(signals: list[ResearchSignal]) -> list[ResearchSignal]:
    seen: set[str] = set()
    deduplicated: list[ResearchSignal] = []
    for signal in signals:
        key = _normalize_summary(signal.summary)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(signal)
    return deduplicated


def _selected_materials(
    materials: list[ResearchDocument],
    selected_signals: list[ResearchSignal],
) -> list[ResearchDocument]:
    selected_ids = {signal.material_id for signal in selected_signals}
    return [material for material in materials if material.material_id in selected_ids]


def _reference_date(signals: list[ResearchSignal]) -> date:
    dates = [signal.publish_date for signal in signals if signal.publish_date is not None]
    return max(dates) if dates else date.today()


def _is_within_lookback(
    publish_date: date | None,
    reference_date: date,
    lookback_months: int,
) -> bool:
    if publish_date is None:
        return False
    earliest_year = reference_date.year
    earliest_month = reference_date.month - lookback_months
    while earliest_month <= 0:
        earliest_year -= 1
        earliest_month += 12
    earliest_day = min(reference_date.day, 28)
    earliest = date(earliest_year, earliest_month, earliest_day)
    return publish_date >= earliest


def _normalize_summary(summary: str) -> str:
    return re.sub(r"\s+", "", summary).casefold()
