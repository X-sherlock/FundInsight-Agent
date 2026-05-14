import json
from pathlib import Path

from fundinsight.research_service import ResearchMaterialService
from fundinsight.research_store import ResearchStore
from tools.validation.run_real_fund_smoke_test import (
    FundRunResult,
    FundScenario,
    MaterialSource,
    import_material_source,
    load_source_text,
    write_data_sources,
)


def test_validation_loader_reads_local_txt_md_and_json(tmp_path: Path) -> None:
    txt = tmp_path / "material.txt"
    md = tmp_path / "material.md"
    js = tmp_path / "material.json"
    txt.write_text("txt body", encoding="utf-8")
    md.write_text("# title\n\nmd body", encoding="utf-8")
    js.write_text(json.dumps({"body": "json body"}, ensure_ascii=False), encoding="utf-8")

    assert load_source_text(path=str(txt))[0] == "txt body"
    assert "md body" in load_source_text(path=str(md))[0]
    assert load_source_text(path=str(js))[0] == "json body"


def test_validation_import_uses_research_material_service(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    service = ResearchMaterialService(store)
    material = tmp_path / "material.md"
    material.write_text("真实公开材料正文。", encoding="utf-8")

    result = import_material_source(
        "005827",
        MaterialSource(
            title="local md",
            source_type="announcement",
            source_name="local",
            publish_date="2026-05-01",
            path=str(material),
        ),
        service,
    )

    assert result.status == "success"
    assert result.material_id
    assert len(service.list_materials("005827")) == 1
    assert store.read_material_content("005827", result.material_id) == "真实公开材料正文。"


def test_validation_import_records_parse_failure_without_creating_material(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "data")
    service = ResearchMaterialService(store)
    material = tmp_path / "bad.json"
    material.write_text(json.dumps({"items": []}), encoding="utf-8")

    result = import_material_source(
        "005827",
        MaterialSource(
            title="bad json",
            source_type="news",
            source_name="local",
            publish_date=None,
            path=str(material),
        ),
        service,
    )

    assert result.status == "parse_failed"
    assert service.list_materials("005827") == []


def test_validation_data_sources_records_sources_and_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("tools.validation.run_real_fund_smoke_test.PROJECT_ROOT", tmp_path)
    scenario = FundScenario(
        fund_code="005827",
        fund_name="易方达蓝筹精选混合",
        metrics_sources=("https://example.com/metrics",),
        material_sources=(
            MaterialSource(
                title="公告",
                source_type="announcement",
                source_name="example",
                publish_date="2026-05-01",
                url="https://example.com/material",
            ),
        ),
    )
    result = FundRunResult(fund_code="005827", fund_name="易方达蓝筹精选混合")
    result.failed_sources.append({"url": "https://example.com/material", "reason": "download_failed"})

    path = write_data_sources(
        scenario,
        {"missing_fields": ["metrics.performance.return_1y"]},
        result,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["fund_code"] == "005827"
    assert payload["material_sources"][0]["url"] == "https://example.com/material"
    assert payload["failed_sources"][0]["reason"] == "download_failed"
    assert payload["whether_any_synthetic_data_used"] is False
