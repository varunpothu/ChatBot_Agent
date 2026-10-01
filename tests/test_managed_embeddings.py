from rag.managed_embeddings import CachedEmbeddingProvider


class FakeProvider:
    model_id = "fake"
    dimensions = 512

    def __init__(self):
        self.calls = 0

    def embed_one(self, text):
        self.calls += 1
        return [1.0] + [0.0] * 511


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


def test_cached_embedding_reuses_exact_content():
    provider = FakeProvider()
    wrapped = CachedEmbeddingProvider(provider, Cache())
    assert wrapped.embed_one("same chunk") == wrapped.embed_one("same chunk")
    assert provider.calls == 1
