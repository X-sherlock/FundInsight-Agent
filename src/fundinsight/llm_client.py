"""Bailian OpenAI-compatible LLM client wrapper for report generation."""

from __future__ import annotations

import os
from typing import Any, Protocol


BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_BAILIAN_MODEL = "deepseek-v4-flash"


class LLMClient(Protocol):
    """Minimal interface used by the report agent."""

    def generate(self, prompt: str) -> str:
        """Generate Markdown text from a rendered prompt."""


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM client cannot be configured."""


class BailianLLMClient:
    """Chat completions client fixed to Bailian's preferred report model."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        temperature: float = 0.2,
    ) -> None:
        self.provider = "bailian"
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv(
            "ALIYUN_BAILIAN_API_KEY"
        )
        self.model = DEFAULT_BAILIAN_MODEL
        self.base_url = (
            base_url
            or os.getenv("DASHSCOPE_BASE_URL")
            or os.getenv("BAILIAN_BASE_URL")
            or BAILIAN_BASE_URL
        )
        self.temperature = temperature

        if not self.api_key:
            raise LLMConfigurationError(
                "DASHSCOPE_API_KEY or ALIYUN_BAILIAN_API_KEY is required for Bailian."
            )

    def generate(self, prompt: str) -> str:
        """Call the configured provider and return the generated report text."""

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                "The openai package is not installed. Install project dependencies first."
            ) from exc

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=self.temperature,
        )
        return _extract_response_text(response)


def _extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    chunks: list[str] = []
    for output_item in getattr(response, "output", []) or []:
        for content_item in getattr(output_item, "content", []) or []:
            text = getattr(content_item, "text", None)
            if isinstance(text, str):
                chunks.append(text)

    text = "\n".join(chunks).strip()
    if not text:
        raise RuntimeError("LLM response did not contain report text.")
    return text
