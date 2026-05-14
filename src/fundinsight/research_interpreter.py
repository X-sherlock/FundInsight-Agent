"""LLM-backed interpretation for retrieved research chunks."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fundinsight.llm_client import LLMClient
from fundinsight.models import FundMetricsInput
from fundinsight.research_models import RetrievedResearchChunk


logger = logging.getLogger(__name__)
ALLOWED_SENTIMENT_LABELS = {"正面", "中性", "负面", "多空交织", "不确定"}
SENTIMENT_LABELS = {
    "positive": "正面",
    "neutral": "中性",
    "negative": "负面",
    "mixed": "多空交织",
    "uncertain": "不确定",
    "正面": "正面",
    "中性": "中性",
    "负面": "负面",
    "多空交织": "多空交织",
    "不确定": "不确定",
}


class ResearchInterpretationError(RuntimeError):
    """Raised when material interpretation output cannot be used."""


class ResearchMaterialInterpreter:
    """Generate structured interpretations for RAG-selected chunks."""

    def interpret_chunks(
        self,
        *,
        fund_metrics: FundMetricsInput,
        chunks: list[RetrievedResearchChunk],
        llm_client: LLMClient,
    ) -> list[RetrievedResearchChunk]:
        if not chunks:
            return []

        interpreted: list[RetrievedResearchChunk] = []
        for chunk in chunks:
            prompt = self.build_prompt(fund_metrics=fund_metrics, chunks=[chunk])
            try:
                raw_output = llm_client.generate(prompt)
                interpretations = self.parse_output(raw_output, chunks_by_id={chunk.chunk_id: chunk})
            except Exception as exc:
                logger.warning("Failed to interpret research chunk %s: %s", chunk.chunk_id, exc)
                interpreted.append(chunk)
                continue
            interpretation = interpretations.get(chunk.chunk_id)
            if interpretation is None:
                interpreted.append(chunk)
                continue
            interpreted.append(chunk.model_copy(update=interpretation))
        return interpreted

    def build_prompt(
        self,
        *,
        fund_metrics: FundMetricsInput,
        chunks: list[RetrievedResearchChunk],
    ) -> str:
        payload = {
            "fund": {
                "code": fund_metrics.fund.code,
                "name": fund_metrics.fund.name,
                "type": fund_metrics.fund.type,
                "category": fund_metrics.category.name,
                "as_of_date": fund_metrics.as_of_date.isoformat(),
            },
            "retrieved_chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "title": chunk.title,
                    "source_type": chunk.source_type,
                    "source_name": chunk.source_name,
                    "publish_date": chunk.publish_date.isoformat() if chunk.publish_date else None,
                    "source_url": chunk.source_url,
                    "original_file_path": chunk.original_file_path,
                    "relevance_score": chunk.relevance_score,
                    "evidence_text": chunk.evidence_text,
                }
                for chunk in chunks
            ],
        }
        return (
            "你是基金相关材料结构化解读助手。请只基于输入的向量检索 TOPK 材料片段，"
            "为每个 retrieved_chunks 中的 chunk 生成一条结构化解读。\n\n"
            "输出要求：只能输出 JSON，不要输出 Markdown、解释、代码块或额外文字。\n"
            "JSON 顶层字段必须是 interpretations，且必须为数组。\n"
            "interpretations 数量应与输入 retrieved_chunks 数量一致，每个 chunk_id 必须出现一次。\n\n"
            "每条 interpretation 必须包含：\n"
            "- chunk_id：原样返回输入 chunk_id。\n"
            "- analysis_title：8 到 20 个中文字符，概括该材料片段的解读主题。\n"
            "- material_summary：1 到 2 句中文摘要，只概括片段中已有事实，不编造。\n"
            "- sentiment_label：只能是 正面、中性、负面、多空交织、不确定。\n"
            "- evidence_excerpt：必须是 evidence_text 中的连续原文摘录，可以较短，但不得改写或拼接。\n\n"
            "边界要求：\n"
            "- 不得输出买入、卖出、持有、加仓、减仓、目标价、择时、仓位或配置建议。\n"
            "- 不得预测未来收益，不得保证收益。\n"
            "- 如果材料只是背景信息或制度安排，sentiment_label 通常使用 中性。\n"
            "- 如果材料同时包含正负因素，使用 多空交织；无法判断时使用 不确定。\n\n"
            "输入 JSON：\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    def parse_output(
        self,
        raw_output: str,
        *,
        chunks_by_id: dict[str, RetrievedResearchChunk],
    ) -> dict[str, dict[str, str]]:
        try:
            payload = json.loads(_strip_json_fence(raw_output))
        except json.JSONDecodeError as exc:
            raise ResearchInterpretationError(f"Material interpretation output is not valid JSON: {exc}") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("interpretations"), list):
            raise ResearchInterpretationError("Material interpretation output must contain an interpretations array.")

        parsed: dict[str, dict[str, str]] = {}
        for item in payload["interpretations"]:
            if not isinstance(item, dict):
                continue
            chunk_id = _clean_string(item.get("chunk_id"))
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                continue
            interpretation = _normalize_interpretation(item, chunk)
            if interpretation is not None:
                parsed[chunk_id] = interpretation
        return parsed


def _normalize_interpretation(
    item: dict[str, Any],
    chunk: RetrievedResearchChunk,
) -> dict[str, str] | None:
    title = _clean_string(item.get("analysis_title"))
    summary = _clean_string(item.get("material_summary"))
    sentiment = SENTIMENT_LABELS.get(_clean_string(item.get("sentiment_label")))
    excerpt = _clean_string(item.get("evidence_excerpt"))
    excerpt = _normalize_evidence_excerpt(excerpt, chunk.evidence_text)
    if not title or not summary or sentiment not in ALLOWED_SENTIMENT_LABELS or not excerpt:
        return None
    return {
        "analysis_title": title,
        "material_summary": summary,
        "sentiment_label": sentiment,
        "evidence_excerpt": excerpt,
    }


def _normalize_evidence_excerpt(excerpt: str, evidence_text: str) -> str:
    if not excerpt:
        return ""
    if excerpt in evidence_text:
        return excerpt
    stripped = excerpt.strip("“”\"'")
    if stripped and stripped in evidence_text:
        return excerpt
    return ""


def _strip_json_fence(raw_output: str) -> str:
    text = raw_output.strip()
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def _clean_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()
