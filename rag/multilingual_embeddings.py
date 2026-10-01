import os
from functools import lru_cache
from typing import Protocol

class MultilingualEmbeddingProvider(Protocol):
    dimensions: int
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...

class E5MultilingualProvider:
    """Local cross-lingual embeddings with no per-request API bill."""
    dimensions=384
    def __init__(self,model_name: str|None=None):
        from sentence_transformers import SentenceTransformer
        self.model_name=model_name or os.getenv("MULTILINGUAL_EMBEDDING_MODEL","intfloat/multilingual-e5-small")
        self.model=self._load(self.model_name)
    @staticmethod
    @lru_cache(maxsize=2)
    def _load(model_name:str):
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    def embed_documents(self,texts:list[str])->list[list[float]]:
        vectors=self.model.encode([f"passage: {x}" for x in texts],normalize_embeddings=True,convert_to_numpy=True)
        return vectors.tolist()
    def embed_query(self,text:str)->list[float]:
        return self.model.encode([f"query: {text}"],normalize_embeddings=True,convert_to_numpy=True)[0].tolist()

def build_multilingual_provider():
    provider=os.getenv("MULTILINGUAL_EMBEDDING_PROVIDER","hash").lower()
    if provider in {"local_e5","e5","multilingual_e5"}:
        return E5MultilingualProvider()
    return None
