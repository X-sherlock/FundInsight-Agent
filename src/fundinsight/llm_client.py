"""OpenAI LLM client wrapper for report generation."""

from __future__ import annotations

import os
from typing import Any, Protocol


class LLMClient(Protocol):
    """Minimal interface used by the report agent."""

    def generate(self, prompt: str) -> str:
        """Generate Markdown text from a rendered prompt."""


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM client cannot be configured."""


class OpenAILLMClient:
    """OpenAI chat completions client configured from environment variables."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        temperature: float = 0.2,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature

        if not self.api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required to call OpenAI.")
        if not self.model:
            raise LLMConfigurationError("OPENAI_MODEL must not be empty.")

    def generate(self, prompt: str) -> str:
        """Call OpenAI and return the generated report text."""

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                "The openai package is not installed. Install project dependencies first."
            ) from exc

        client = OpenAI(api_key=self.api_key)
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
        raise RuntimeError("OpenAI response did not contain report text.")
    return text
