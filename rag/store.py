from dataclasses import dataclass, field, replace
from rag.models import DocumentChunk, DocumentStatus

@dataclass
class InMemoryKnowledgeStore:
    """Fast local store for development and demos."""
    chunks: list[DocumentChunk] = field(default_factory=list)
    generation: int = 0

    def add(self, new_chunks: list[DocumentChunk]) -> None:
        self.chunks.extend(new_chunks)
        self.generation += 1

    def set_document_status(self, document_id: str, status: DocumentStatus) -> int:
        changed = 0
        updated: list[DocumentChunk] = []
        for chunk in self.chunks:
            if chunk.document.document_id == document_id:
                updated.append(replace(chunk, document=replace(chunk.document, status=status)))
                changed += 1
            else:
                updated.append(chunk)
        if changed:
            self.chunks = updated
            self.generation += 1
        return changed

    def all(self) -> list[DocumentChunk]:
        return list(self.chunks)
