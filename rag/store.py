from dataclasses import dataclass, field
from rag.models import DocumentChunk

@dataclass
class InMemoryKnowledgeStore:
    """Fast local store for development and demos."""
    chunks: list[DocumentChunk] = field(default_factory=list)
    generation: int = 0

    def add(self, new_chunks: list[DocumentChunk]) -> None:
        self.chunks.extend(new_chunks)
        self.generation += 1

    def all(self) -> list[DocumentChunk]:
        return list(self.chunks)
