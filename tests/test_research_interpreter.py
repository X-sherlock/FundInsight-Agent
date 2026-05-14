import json
from pathlib import Path

import pytest

from fundinsight.data_loader import load_fund_metrics
from fundinsight.research_interpreter import ResearchInterpretationError, ResearchMaterialInterpreter
from fundinsight.research_models import RetrievedResearchChunk


SAMPLE_INPUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "fund_metrics.json"


class StubInterpretationLLM:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.payload, ensure_ascii=False)


def test_research_material_interpreter_enriches_retrieved_chunks() -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)
    chunk = _chunk("mat_1", "基金过去一年收益为13.07%，同期基准收益率为3.47%。")
    llm = StubInterpretationLLM(
        {
            "interpretations": [
                {
                    "chunk_id": "mat_1",
                    "analysis_title": "历史收益表现",
                    "material_summary": "材料披露基金过去一年收益和同期基准收益。",
                    "sentiment_label": "positive",
                    "evidence_excerpt": "基金过去一年收益为13.07%",
                }
            ]
        }
    )

    interpreted = ResearchMaterialInterpreter().interpret_chunks(
        fund_metrics=metrics,
        chunks=[chunk],
        llm_client=llm,
    )

    assert interpreted[0].analysis_title == "历史收益表现"
    assert interpreted[0].material_summary == "材料披露基金过去一年收益和同期基准收益。"
    assert interpreted[0].sentiment_label == "正面"
    assert interpreted[0].evidence_excerpt == "基金过去一年收益为13.07%"
    assert "基金相关材料结构化解读助手" in llm.prompts[0]


def test_research_material_interpreter_rejects_non_original_excerpt() -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)
    chunk = _chunk("mat_1", "原文只包含这一句话。")
    llm = StubInterpretationLLM(
        {
            "interpretations": [
                {
                    "chunk_id": "mat_1",
                    "analysis_title": "材料主题",
                    "material_summary": "材料摘要。",
                    "sentiment_label": "中性",
                    "evidence_excerpt": "不存在于原文的摘录",
                }
            ]
        }
    )

    interpreted = ResearchMaterialInterpreter().interpret_chunks(
        fund_metrics=metrics,
        chunks=[chunk],
        llm_client=llm,
    )

    assert interpreted[0].analysis_title is None


def test_research_material_interpreter_drops_missing_or_invalid_interpretations() -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)
    chunks = [
        _chunk("mat_1", "原文只包含这一句话。"),
        _chunk("mat_2", "另一段原文。"),
    ]
    llm = StubInterpretationLLM(
        {
            "interpretations": [
                {
                    "chunk_id": "mat_1",
                    "analysis_title": "材料主题",
                    "material_summary": "材料摘要。",
                    "sentiment_label": "中性",
                    "evidence_excerpt": "不存在于原文的摘录",
                }
            ]
        }
    )

    interpreted = ResearchMaterialInterpreter().interpret_chunks(
        fund_metrics=metrics,
        chunks=chunks,
        llm_client=llm,
    )

    assert len(interpreted) == 2
    assert all(chunk.analysis_title is None for chunk in interpreted)
    assert len(llm.prompts) == 2


def test_research_material_interpreter_skips_invalid_json_without_fallback() -> None:
    metrics = load_fund_metrics(SAMPLE_INPUT)

    class InvalidLLM:
        def generate(self, prompt: str) -> str:
            return "not json"

    interpreted = ResearchMaterialInterpreter().interpret_chunks(
        fund_metrics=metrics,
        chunks=[_chunk("mat_1", "基金材料原文。")],
        llm_client=InvalidLLM(),
    )

    assert interpreted[0].analysis_title is None


def test_research_material_interpreter_parse_output_raises_on_invalid_json() -> None:
    with pytest.raises(ResearchInterpretationError):
        ResearchMaterialInterpreter().parse_output("not json", chunks_by_id={})


def _chunk(chunk_id: str, evidence_text: str) -> RetrievedResearchChunk:
    return RetrievedResearchChunk(
        chunk_id=chunk_id,
        material_id="mat",
        fund_code="000001",
        chunk_index=0,
        evidence_text=evidence_text,
        relevance_score=0.8,
        source_type="report",
        title="年度报告",
    )
