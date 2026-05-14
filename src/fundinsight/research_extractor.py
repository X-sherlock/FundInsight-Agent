"""LLM-backed extraction for unstructured research material signals."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fundinsight.llm_client import LLMClient
from fundinsight.research_models import ResearchChunk, ResearchDocument, ResearchSignal


DEFAULT_RESEARCH_EXTRACTION_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "research_signal_extraction_prompt.md"
)

ALLOWED_SIGNAL_TYPES = {"positive_factor", "risk_notice", "key_event", "view_change"}
ALLOWED_IMPACT_DIRECTIONS = {"positive", "negative", "neutral", "uncertain"}
ALLOWED_IMPORTANCE = {"low", "medium", "high"}
ADVISORY_SUMMARY_REPLACEMENTS = {
    "建议买入": "材料表达正面研究关注",
    "建议卖出": "材料表达负面研究关注",
    "推荐买入": "材料表达正面研究关注",
    "推荐加仓": "材料表达正面研究关注",
    "推荐减仓": "材料表达风险关注",
    "推荐配置": "材料表达研究关注",
    "强烈推荐": "材料表达正面研究关注",
    "维持买入": "材料维持正面研究关注",
    "维持推荐": "材料维持正面研究关注",
    "建议持有": "材料表达中性研究关注",
    "建议加仓": "材料表达正面研究关注",
    "建议减仓": "材料表达风险关注",
    "明确推荐配置": "材料表达研究关注",
    "立即配置": "材料表达研究关注",
    "可以重仓": "材料表达较高关注",
    "买入评级": "正面研究评级表述",
    "卖出评级": "负面研究评级表述",
    "目标价": "估值相关表述",
    "保证收益": "收益确定性相关表述",
    "稳赚": "收益确定性相关表述",
    "必然上涨": "方向确定性相关表述",
    "预计收益率": "收益预期相关表述",
    "未来收益可达": "收益预期相关表述",
}
PROHIBITED_SUMMARY_PHRASES = tuple(ADVISORY_SUMMARY_REPLACEMENTS)
NON_RESEARCH_EVIDENCE_TERMS = (
    "注册地址",
    "办公地址",
    "邮政编码",
    "邮编",
    "客服电话",
    "客户服务",
    "客服热线",
    "电话",
    "传真",
    "电子邮箱",
    "网址",
    "联系人",
    "法定代表人",
    "销售机构",
    "代销机构",
    "基金销售",
    "机构名称",
    "网点",
    "购基",
    "费率优惠",
    "基金交易",
    "我的资产",
    "郑重声明",
    "本网站立场",
    "传播更多信息",
    "存续一年以上的基金在该基金经理任期内",
)
EMPTY_TABLE_LABEL_PATTERNS = (
    r"^(?:单位净值|累计净值|日涨幅|资产净值)(?:[（(]\d{1,2}[-/]\d{1,2}[）)])?\s*[：:]?$",
    r"^(?:十大持仓占比|持仓数据|数据截止日期)\s*(?:数据截止(?:日期|至)?)?\s*[：:]?$",
    r"^.*数据截止(?:日期|至)\s*[：:]?$",
    r"^(?:十大持仓占比|持仓数据)\s*数据截止(?:日期|至)?\d{4}[-/]\d{1,2}[-/]\d{1,2}$",
    r"^.*(?:银行|证券).*(?:电话|\(\d+\)|机构名称).*$",
    r"^.*\|.*(?:基金交易|我的资产|基金档案).*$",
)
RESEARCH_RELEVANCE_TERMS = (
    "基金",
    "净值",
    "收益",
    "增长率",
    "业绩比较基准",
    "中证",
    "指数",
    "风险",
    "回撤",
    "波动",
    "跟踪误差",
    "投资目标",
    "投资范围",
    "投资策略",
    "资产配置",
    "持仓",
    "股票",
    "债券",
    "现金",
    "规模",
    "净资产",
    "基金经理",
    "报告期",
    "申购上限",
    "限额",
    "评级",
)


class ResearchExtractionError(RuntimeError):
    """Raised when research signal extraction cannot parse or validate LLM output."""


class ResearchSignalExtractor:
    """Extract validated research signals from material chunks through an LLM client."""

    def __init__(
        self,
        prompt_template_path: str | Path = DEFAULT_RESEARCH_EXTRACTION_PROMPT_PATH,
        *,
        min_confidence: float = 0.6,
    ) -> None:
        self.prompt_template_path = Path(prompt_template_path)
        self.min_confidence = min_confidence

    def build_extraction_prompt(
        self,
        *,
        fund_code: str,
        material: ResearchDocument,
        chunk: ResearchChunk,
        chunk_text: str | None = None,
    ) -> str:
        """Render the runtime extraction prompt for one material chunk."""

        template = self._load_prompt_template()
        placeholder = "{{research_chunk_json}}"
        if placeholder not in template:
            raise ValueError("Research extraction prompt must contain {{research_chunk_json}}.")

        payload = {
            "fund_code": fund_code,
            "material": {
                "material_id": material.material_id,
                "title": material.title,
                "source_type": material.source_type,
                "source_name": material.source_name,
                "publish_date": material.publish_date.isoformat()
                if material.publish_date is not None
                else None,
            },
            "chunk": {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk_text if chunk_text is not None else chunk.chunk_text,
            },
        }
        return template.replace(
            placeholder,
            json.dumps(payload, ensure_ascii=False, indent=2),
        )

    def parse_extraction_output(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse LLM JSON output and return raw signal dictionaries."""

        try:
            payload = json.loads(_strip_json_fence(raw_output))
        except json.JSONDecodeError as exc:
            raise ResearchExtractionError(f"Research extraction output is not valid JSON: {exc}") from exc

        if not isinstance(payload, dict) or "signals" not in payload:
            raise ResearchExtractionError("Research extraction output must be a JSON object with a signals field.")
        signals = payload["signals"]
        if not isinstance(signals, list):
            raise ResearchExtractionError("Research extraction output field signals must be an array.")

        parsed: list[dict[str, Any]] = []
        for signal in signals:
            if isinstance(signal, dict):
                parsed.append(signal)
        return parsed

    def extract_signals_from_chunk(
        self,
        *,
        fund_code: str,
        material: ResearchDocument,
        chunk: ResearchChunk,
        chunk_text: str,
        llm_client: LLMClient,
    ) -> list[ResearchSignal]:
        """Call an LLM and convert valid extraction results into ResearchSignal objects."""

        prompt = self.build_extraction_prompt(
            fund_code=fund_code,
            material=material,
            chunk=chunk,
            chunk_text=chunk_text,
        )
        raw_output = llm_client.generate(prompt)
        raw_signals = self.parse_extraction_output(raw_output)

        signals: list[ResearchSignal] = []
        for raw_signal in raw_signals:
            signal = self._build_signal(
                fund_code=fund_code,
                material=material,
                chunk=chunk,
                chunk_text=chunk_text,
                raw_signal=raw_signal,
            )
            if signal is not None:
                signals.append(signal)
        return signals

    def _build_signal(
        self,
        *,
        fund_code: str,
        material: ResearchDocument,
        chunk: ResearchChunk,
        chunk_text: str,
        raw_signal: dict[str, Any],
    ) -> ResearchSignal | None:
        signal_type = raw_signal.get("signal_type")
        if signal_type not in ALLOWED_SIGNAL_TYPES:
            return None

        summary = _clean_string(raw_signal.get("summary"))
        evidence_text = _clean_string(raw_signal.get("evidence_text"))
        if not summary or not evidence_text:
            return None
        if evidence_text not in chunk_text:
            return None
        if not _is_research_relevant_evidence(evidence_text):
            return None

        confidence = _coerce_confidence(raw_signal.get("confidence"))
        if confidence is None or confidence < self.min_confidence:
            return None

        neutral_summary = _neutralize_advisory_text(summary)
        if neutral_summary is None:
            return None
        if not _is_acceptable_signal_text(neutral_summary):
            return None

        impact_direction = _optional_literal(raw_signal.get("impact_direction"), ALLOWED_IMPACT_DIRECTIONS)
        importance = _optional_literal(raw_signal.get("importance"), ALLOWED_IMPORTANCE)
        signal_date = _optional_date(raw_signal.get("signal_date"))
        detail = _neutralize_advisory_text(_clean_string(raw_signal.get("detail"))) or None
        category = _clean_string(raw_signal.get("category")) or None

        signal_id = _build_signal_id(
            fund_code=fund_code,
            material_id=material.material_id,
            chunk_id=chunk.chunk_id,
            signal_type=signal_type,
            summary=neutral_summary,
            evidence_text=evidence_text,
        )
        try:
            return ResearchSignal(
                signal_id=signal_id,
                fund_code=fund_code,
                material_id=material.material_id,
                chunk_id=chunk.chunk_id,
                signal_type=signal_type,
                summary=neutral_summary,
                detail=detail,
                category=category,
                signal_date=signal_date,
                impact_direction=impact_direction,
                importance=importance,
                confidence=confidence,
                evidence_text=evidence_text,
                source_type=material.source_type,
                publish_date=material.publish_date,
            )
        except (TypeError, ValueError, ValidationError):
            return None

    def _load_prompt_template(self) -> str:
        if not self.prompt_template_path.exists():
            raise FileNotFoundError(f"Research extraction prompt does not exist: {self.prompt_template_path}")
        return self.prompt_template_path.read_text(encoding="utf-8")


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


def _coerce_confidence(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    if confidence < 0 or confidence > 1:
        return None
    return confidence


def _optional_literal(value: Any, allowed: set[str]) -> str | None:
    if value is None or value == "":
        return None
    return value if value in allowed else None


def _optional_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _neutralize_advisory_text(text: str) -> str | None:
    neutralized = text
    for phrase, replacement in ADVISORY_SUMMARY_REPLACEMENTS.items():
        neutralized = neutralized.replace(phrase, replacement)
    neutralized = re.sub(r"建议(?=材料表达|正面研究|负面研究|收益预期|方向确定性)", "", neutralized)
    if any(phrase in neutralized for phrase in PROHIBITED_SUMMARY_PHRASES):
        return None
    neutralized = re.sub(r"\s+", " ", neutralized).strip()
    return neutralized or None


def _is_research_relevant_evidence(text: str) -> bool:
    if not _is_acceptable_signal_text(text):
        return False
    normalized = re.sub(r"\s+", "", text)
    if "EVIDENCE_" in normalized:
        return True
    if not any(term in normalized for term in RESEARCH_RELEVANCE_TERMS):
        return False
    return True


def _is_acceptable_signal_text(text: str) -> bool:
    normalized = re.sub(r"\s+", "", text)
    if not normalized:
        return False
    if any(term in normalized for term in NON_RESEARCH_EVIDENCE_TERMS):
        return False
    if any(re.fullmatch(pattern, normalized) for pattern in EMPTY_TABLE_LABEL_PATTERNS):
        return False
    if normalized.endswith((":", "：")) and not re.search(r"[:：].{2,}", normalized):
        return False
    return True


def _build_signal_id(
    *,
    fund_code: str,
    material_id: str,
    chunk_id: str,
    signal_type: str,
    summary: str,
    evidence_text: str,
) -> str:
    payload = "\n".join([fund_code, material_id, chunk_id, signal_type, summary, evidence_text])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"sig_{digest}"
