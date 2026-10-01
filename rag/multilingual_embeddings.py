import os
from functools import lru_cache

class E5MultilingualProvider:
    """Local cross-lingual embeddings with no per-request API bill."""
    dimensions = 384

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name or os.getenv("MULTILINGUAL_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
        self.device = os.getenv("MULTILINGUAL_EMBEDDING_DEVICE", "cpu")
        self.batch_size = int(os.getenv("MULTILINGUAL_EMBEDDING_BATCH_SIZE", "16"))
        self.model = self._load(self.model_name, self.device)

    @staticmethod
    @lru_cache(maxsize=2)
    def _load(model_name: str, device: str):
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            [f"passage: {x}" for x in texts],
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(
            [f"query: {text}"],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0].tolist()

def build_multilingual_provider():
    provider = os.getenv("MULTILINGUAL_EMBEDDING_PROVIDER", "auto").lower()
    if provider in {"none", "hash", "off"}:
        return None
    if provider in {"local_e5", "e5", "multilingual_e5", "auto"}:
        try:
            return E5MultilingualProvider()
        except ImportError:
            if provider == "auto":
                return None
            raise
        except Exception:
            if provider == "auto":
                return None
            raise
    return None
