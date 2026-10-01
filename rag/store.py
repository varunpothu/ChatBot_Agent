from dataclasses import dataclass, field
from rag.models import DocumentChunk

@dataclass
class InMemoryKnowledgeStore:
    """Local store for development; production uses PostgreSQL + pgvector."""
    chunks: list[DocumentChunk] = field(default_factory=list)

    def add(self, new_chunks: list[DocumentChunk]) -> None:
        self.chunks.extend(new_chunks)

    def all(self) -> list[DocumentChunk]:
        return list(self.chunks)
