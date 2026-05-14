import json
from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics
from fundinsight.research_models import ResearchFusionContext, ResearchSignalBundle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_FUND_CODES = ("110022", "161725")


def test_real_fund_metrics_validate_without_synthetic_source() -> None:
    for fund_code in REAL_FUND_CODES:
        metrics = load_fund_metrics(PROJECT_ROOT / "data" / "funds" / fund_code / "metrics.json")

        assert metrics.fund.code == fund_code
        assert metrics.data_quality.source
        assert "synthetic" not in metrics.data_quality.source.lower()
        assert metrics.data_quality.missing_fields
        assert any("不使用虚构值补齐" in note for note in [metrics.data_quality.notes, *metrics.data_notes] if note)


def test_real_research_signals_validate_and_keep_original_evidence() -> None:
    validated_count = 0
    for fund_code in REAL_FUND_CODES:
        research_dir = PROJECT_ROOT / "data" / "funds" / fund_code / "research"
        signal_path = research_dir / "extracted_signals.json"
        context_path = research_dir / "fusion_context.json"
        if not signal_path.exists() or not context_path.exists():
            continue
        bundle = ResearchSignalBundle.model_validate(
            json.loads(signal_path.read_text(encoding="utf-8"))
        )
        context = ResearchFusionContext.model_validate(
            json.loads(context_path.read_text(encoding="utf-8"))
        )
        material_texts = {
            path.stem: path.read_text(encoding="utf-8")
            for path in (research_dir / "materials").glob("*.txt")
        }

        assert bundle.signals
        assert context.source_materials
        assert context.analyzed_materials
        for signal in bundle.signals:
            assert signal.evidence_text in material_texts[signal.material_id]
        validated_count += 1

    if validated_count == 0:
        pytest.skip("Real LLM research artifacts have not been generated in this workspace.")
