from dataclasses import dataclass
import re

from rag.models import DocumentChunk
from rag.guardrails import only_active_student_evidence


@dataclass(frozen=True)
class ScoredChunk:
    chunk: DocumentChunk
    semantic_score: float
    keyword_score: float
    final_score: float


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def keyword_score(query: str, text: str) -> float:
    q = tokenize(query)
    t = tokenize(text)
    if not q:
        return 0.0
    return len(q & t) / len(q)


class HybridRetriever:
    """Deterministic baseline retriever.

    Phase 2 uses this as a local/test implementation. A pgvector semantic
    retriever can implement the same interface without changing the API layer.
    """

    def __init__(self, chunks: list[DocumentChunk]):
        self.chunks = only_active_student_evidence(chunks)

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        results = []
        for chunk in self.chunks:
            ks = keyword_score(query, chunk.text)
            # Semantic score is intentionally explicit until embeddings are wired.
            ss = 0.0
            final = 0.35 * ks + 0.65 * ss
            results.append(ScoredChunk(chunk, ss, ks, final))

        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_k]
