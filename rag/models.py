from dataclasses import dataclass, field
from datetime import date
from typing import Literal

DocumentStatus = Literal["DRAFT", "PROCESSING", "PENDING_REVIEW", "APPROVED", "ACTIVE", "ARCHIVED", "REJECTED"]

@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    name: str
    version: str
    category: str
    status: DocumentStatus
    effective_from: date | None = None
    effective_until: date | None = None
    access_level: str = "student"

@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document: DocumentMetadata
    page: int | None
    section: str | None
    text: str
    embedding: list[float] = field(default_factory=list)
