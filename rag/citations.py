from dataclasses import dataclass

from rag.retrieval import ScoredChunk


@dataclass(frozen=True)
class Citation:
    document_id: str
    document_name: str
    version: str
    page: int | None
    chunk_id: str
    score: float

    @classmethod
    def from_result(cls, result: ScoredChunk) -> "Citation":
        d = result.chunk.document
        return cls(
            document_id=d.document_id,
            document_name=d.name,
            version=d.version,
            page=result.chunk.page,
            chunk_id=result.chunk.chunk_id,
            score=result.final_score,
        )
