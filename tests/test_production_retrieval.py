from datetime import date
from rag.models import DocumentStatus
from rag.retrieval import PostgresHybridRetriever


class FakeProvider:
    model_id = "fake-model"
    dimensions = 512

    def __init__(self):
        self.calls = 0

    def embed_query(self, text: str):
        self.calls += 1
        return [1.0] + [0.0] * 511


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, *_args, **_kwargs):
        return FakeResult(self.rows)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeEngine:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def connect(self):
        self.calls += 1
        return FakeConnection(self.rows)


class FakeStore:
    def __init__(self, rows):
        self.engine = FakeEngine(rows)


def row(text: str, semantic: float = 0.9):
    return {
        "chunk_id": "11111111-1111-1111-1111-111111111111",
        "document_id": "22222222-2222-2222-2222-222222222222",
        "content": text,
        "page": 1,
        "section": "policy",
        "name": "handbook.pdf",
        "version": "v1",
        "category": "general",
        "status": "ACTIVE",
        "effective_from": date(2026, 1, 1),
        "effective_until": None,
        "semantic_score": semantic,
    }


def test_postgres_retriever_combines_vector_and_keyword_signals():
    provider = FakeProvider()
    retriever = PostgresHybridRetriever(
        FakeStore([row("The refund policy allows a full refund within 14 days.")]),
        embedding_provider=provider,
    )

    results = retriever.search("refund policy", top_k=1)

    assert len(results) == 1
    assert results[0].chunk.document.status == DocumentStatus.ACTIVE
    assert results[0].semantic_score > 0
    assert results[0].keyword_score > 0
    assert results[0].final_score > 0
    assert provider.calls == 1


def test_postgres_retriever_uses_exact_query_embedding_cache():
    provider = FakeProvider()

    class Cache:
        def __init__(self):
            self.values = {}

        @staticmethod
        def key(*parts):
            return "|".join(parts)

        def get(self, key):
            return self.values.get(key)

        def set(self, key, value):
            self.values[key] = value

    cache = Cache()
    retriever = PostgresHybridRetriever(
        FakeStore([row("The centre opens at 9am.")]),
        embedding_provider=provider,
        query_cache=cache,
    )

    retriever.search("centre opening", top_k=1)
    retriever.search("centre opening", top_k=1)

    assert provider.calls == 1
