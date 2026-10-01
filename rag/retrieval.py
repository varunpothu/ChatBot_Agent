from dataclasses import dataclass
import re
from math import sqrt

from rag.models import DocumentChunk
from rag.guardrails import only_active_student_evidence
from rag.embeddings import HashEmbeddingProvider

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "when", "where",
    "how", "can", "do", "does", "to", "of", "for", "and", "or", "in", "on",
    "my", "me", "please", "tell", "about", "with"
}

@dataclass(frozen=True)
class ScoredChunk:
    chunk: DocumentChunk
    semantic_score: float
    keyword_score: float
    final_score: float

def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-zA-Z0-9£$€_.-]+", text.lower()))
    return {t for t in tokens if t not in STOPWORDS}

def keyword_score(query: str, text: str) -> float:
    q = tokenize(query)
    t = tokenize(text)
    if not q:
        return 0.0
    overlap = len(q & t) / len(q)
    phrase_bonus = 0.15 if query.lower().strip() in text.lower() else 0.0
    return min(1.0, overlap + phrase_bonus)

def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    ln = sqrt(sum(a * a for a in left)) or 1.0
    rn = sqrt(sum(b * b for b in right)) or 1.0
    return max(0.0, dot / (ln * rn))

class HybridRetriever:
    """Fast local hybrid retrieval with precomputed deterministic vectors.

    Production can replace the provider with Bedrock embeddings + pgvector
    without changing the orchestrator contract.
    """
    def __init__(self, chunks: list[DocumentChunk], dimensions: int = 96):
        self.chunks = only_active_student_evidence(chunks)
        self.embedding_provider = HashEmbeddingProvider(dimensions=dimensions)
        self.embeddings = self.embedding_provider.embed([c.text for c in self.chunks])

    def search(self, query: str, top_k: int = 3) -> list[ScoredChunk]:
        if not query.strip() or not self.chunks:
            return []
        query_vector = self.embedding_provider.embed([query])[0]
        results: list[ScoredChunk] = []
        for chunk, vector in zip(self.chunks, self.embeddings):
            ks = keyword_score(query, chunk.text)
            ss = _cosine(query_vector, vector)
            final = 0.55 * ss + 0.45 * ks
            results.append(ScoredChunk(chunk, ss, ks, final))
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_k]
