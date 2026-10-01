from dataclasses import dataclass, field
from datetime import date
from enum import Enum

class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"

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
