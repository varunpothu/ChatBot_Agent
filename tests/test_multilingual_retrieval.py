import pytest
from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever

def make_chunk(text):
    return DocumentChunk("doc-1",DocumentMetadata("doc-1","Fees.pdf","v1","fees","ACTIVE"),1,"Fees",text)

def test_hash_retriever_remains_default(monkeypatch):
    monkeypatch.setenv("MULTILINGUAL_EMBEDDING_PROVIDER","hash")
    retriever=HybridRetriever([make_chunk("The course fee is £2800.")])
    assert retriever.multilingual_provider is None

def test_e5_provider_is_optional(monkeypatch):
    monkeypatch.setenv("MULTILINGUAL_EMBEDDING_PROVIDER","local_e5")
    pytest.importorskip("sentence_transformers")
    retriever=HybridRetriever([make_chunk("The course fee is £2800.")])
    assert retriever.multilingual_provider is not None
    assert retriever.embedding_provider.dimensions == 384
