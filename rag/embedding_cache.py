import hashlib
from collections import OrderedDict
from typing import Protocol

class BatchEmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...

class CachedEmbeddingProvider:
    """Content-addressed embedding cache.

    Unchanged chunks are never embedded twice in the same process. Production
    deployments can replace this with a shared cache keyed by content hash.
    """
    def __init__(self, provider: BatchEmbeddingProvider, max_items: int = 10000):
        self.provider = provider
        self.max_items = max_items
        self._cache: OrderedDict[str, list[float]] = OrderedDict()

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def embed(self, texts: list[str]) -> list[list[float]]:
        result: list[list[float] | None] = []
        missing: list[str] = []
        missing_keys: list[str] = []
        for text in texts:
            key = self._key(text)
            value = self._cache.get(key)
            if value is None:
                result.append(None)
                missing.append(text)
                missing_keys.append(key)
            else:
                self._cache.move_to_end(key)
                result.append(value)

        if missing:
            vectors = self.provider.embed(missing)
            for key, vector in zip(missing_keys, vectors):
                self._cache[key] = vector
                self._cache.move_to_end(key)
                while len(self._cache) > self.max_items:
                    self._cache.popitem(last=False)

            index = 0
            for i, value in enumerate(result):
                if value is None:
                    result[i] = vectors[index]
                    index += 1

        return [v for v in result if v is not None]
