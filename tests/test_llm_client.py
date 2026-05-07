from fundinsight.llm_client import BAILIAN_BASE_URL, OpenAICompatibleLLMClient


def test_bailian_client_uses_dashscope_environment(monkeypatch) -> None:
    monkeypatch.setenv("FUNDINSIGHT_LLM_PROVIDER", "bailian")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")
    monkeypatch.delenv("DASHSCOPE_MODEL", raising=False)
    monkeypatch.delenv("BAILIAN_MODEL", raising=False)

    client = OpenAICompatibleLLMClient()

    assert client.provider == "bailian"
    assert client.api_key == "test-dashscope-key"
    assert client.model == "qwen-plus"
    assert client.base_url == BAILIAN_BASE_URL


def test_openai_client_keeps_existing_environment(monkeypatch) -> None:
    monkeypatch.delenv("FUNDINSIGHT_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("ALIYUN_BAILIAN_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    client = OpenAICompatibleLLMClient()

    assert client.provider == "openai"
    assert client.api_key == "test-openai-key"
    assert client.model == "gpt-4o-mini"
    assert client.base_url is None


def test_dashscope_key_selects_bailian_when_provider_is_unset(monkeypatch) -> None:
    monkeypatch.delenv("FUNDINSIGHT_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")

    client = OpenAICompatibleLLMClient()

    assert client.provider == "bailian"
    assert client.api_key == "test-dashscope-key"
    assert client.model == "qwen-plus"
    assert client.base_url == BAILIAN_BASE_URL
