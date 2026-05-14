from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_rag_fixture_funds_load_metrics_and_materials() -> None:
    for fund_code in ("004997", "003095", "163406"):
        metrics = load_fund_metrics(PROJECT_ROOT / "data" / "funds" / fund_code / "metrics.json")
        materials = ResearchMaterialService(ResearchStore(PROJECT_ROOT / "data")).list_materials(fund_code)

        assert metrics.fund.code == fund_code
        assert metrics.data_quality.source == "fixture_from_public_pages"
        assert len(materials) >= 1
        assert all(material.source_url or material.original_file_path for material in materials)
