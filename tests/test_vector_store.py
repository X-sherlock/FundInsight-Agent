import builtins

import pytest

from fundinsight.vector_store import VectorResearchStore, VectorStoreError


def test_vector_store_requires_chromadb(monkeypatch, tmp_path):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "chromadb":
            raise ImportError("missing chromadb")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(VectorStoreError, match="ChromaDB is required"):
        VectorResearchStore(tmp_path / "chroma")
