from types import SimpleNamespace

from fundinsight.embeddings import BailianEmbeddingClient


def test_bailian_embedding_client_batches_requests(monkeypatch) -> None:
    calls: list[list[str]] = []

    class FakeEmbeddings:
        def create(self, *, model: str, input: list[str]):
            calls.append(input)
            return SimpleNamespace(
                data=[
                    SimpleNamespace(embedding=[float(len(calls)), float(index)])
                    for index, _ in enumerate(input)
                ]
            )

    class FakeOpenAI:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            self.embeddings = FakeEmbeddings()

    monkeypatch.setitem(__import__("sys").modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    client = BailianEmbeddingClient(api_key="key", batch_size=10)
    embeddings = client.embed_texts([f"text {index}" for index in range(23)])

    assert [len(call) for call in calls] == [10, 10, 3]
    assert len(embeddings) == 23
