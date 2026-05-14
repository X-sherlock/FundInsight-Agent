"""Embedding clients used by local RAG ingestion and retrieval."""

from __future__ import annotations

import hashlib
import math
import os
from typing import Protocol

from fundinsight.llm_client import BAILIAN_BASE_URL, LLMConfigurationError


DEFAULT_BAILIAN_EMBEDDING_MODEL = "text-embedding-v4"
DEFAULT_BAILIAN_EMBEDDING_BATCH_SIZE = 10


class EmbeddingClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


class HashEmbeddingClient:
    """Deterministic local embedding fallback for tests and offline development."""

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive.")
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_normalize(_hash_embedding(text, self.dimensions)) for text in texts]


class BailianEmbeddingClient:
    """Bailian OpenAI-compatible embeddings client."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIYUN_BAILIAN_API_KEY")
        self.base_url = base_url or os.getenv("DASHSCOPE_BASE_URL") or os.getenv("BAILIAN_BASE_URL") or BAILIAN_BASE_URL
        self.model = model or os.getenv("FUNDINSIGHT_EMBEDDING_MODEL") or DEFAULT_BAILIAN_EMBEDDING_MODEL
        self.batch_size = batch_size or _embedding_batch_size()
        if not self.api_key:
            raise LLMConfigurationError("DASHSCOPE_API_KEY or ALIYUN_BAILIAN_API_KEY is required for Bailian embeddings.")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError("The openai package is not installed.") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        embeddings: list[list[float]] = []
        for batch in _batches(texts, self.batch_size):
            response = client.embeddings.create(model=self.model, input=batch)
            embeddings.extend(list(item.embedding) for item in response.data)
        return embeddings


def get_default_embedding_client() -> EmbeddingClient:
    provider = os.getenv("FUNDINSIGHT_EMBEDDING_PROVIDER", "auto").strip().lower()
    if provider == "hash":
        return HashEmbeddingClient()
    if provider in {"auto", "bailian", "dashscope"}:
        if provider == "auto" and not (os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIYUN_BAILIAN_API_KEY")):
            return HashEmbeddingClient()
        return BailianEmbeddingClient()
    raise ValueError(f"Unsupported embedding provider: {provider}")


def _embedding_batch_size() -> int:
    raw = os.getenv("FUNDINSIGHT_EMBEDDING_BATCH_SIZE", str(DEFAULT_BAILIAN_EMBEDDING_BATCH_SIZE))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_BAILIAN_EMBEDDING_BATCH_SIZE
    return min(max(value, 1), DEFAULT_BAILIAN_EMBEDDING_BATCH_SIZE)


def _batches(texts: list[str], batch_size: int) -> list[list[str]]:
    return [texts[index : index + batch_size] for index in range(0, len(texts), batch_size)]


def _hash_embedding(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    normalized = text.casefold()
    for token in _tokens(normalized):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = -1.0 if digest[4] % 2 else 1.0
        vector[index] += sign
    if not any(vector):
        vector[0] = 1.0
    return vector


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    current = ""
    for char in text:
        if char.isalnum():
            current += char
        else:
            if current:
                tokens.append(current)
                current = ""
            if "\u4e00" <= char <= "\u9fff":
                tokens.append(char)
    if current:
        tokens.append(current)
    if not tokens:
        tokens = [text[:128] or "empty"]
    return tokens


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
