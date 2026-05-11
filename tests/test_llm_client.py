import pytest

from fundinsight.llm_client import (
    BAILIAN_BASE_URL,
    BailianLLMClient,
    DEFAULT_BAILIAN_MODEL,
    LLMConfigurationError,
)


def test_client_uses_bailian_deepseek_flash_by_default(monkeypatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")

    client = BailianLLMClient()

    assert client.provider == "bailian"
    assert client.api_key == "test-dashscope-key"
    assert client.model == DEFAULT_BAILIAN_MODEL
    assert client.base_url == BAILIAN_BASE_URL


def test_client_ignores_legacy_provider_and_model_selection(monkeypatch) -> None:
    monkeypatch.setenv("FUNDINSIGHT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")
    monkeypatch.setenv("DASHSCOPE_MODEL", "qwen-plus")
    monkeypatch.setenv("BAILIAN_MODEL", "qwen-turbo")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    client = BailianLLMClient()

    assert client.provider == "bailian"
    assert client.api_key == "test-dashscope-key"
    assert client.model == DEFAULT_BAILIAN_MODEL
    assert client.base_url == BAILIAN_BASE_URL


def test_client_accepts_aliyun_bailian_key(monkeypatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("ALIYUN_BAILIAN_API_KEY", "test-bailian-key")

    client = BailianLLMClient()

    assert client.provider == "bailian"
    assert client.api_key == "test-bailian-key"
    assert client.model == DEFAULT_BAILIAN_MODEL


def test_client_requires_bailian_api_key(monkeypatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("ALIYUN_BAILIAN_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    with pytest.raises(LLMConfigurationError, match="Bailian"):
        BailianLLMClient()
