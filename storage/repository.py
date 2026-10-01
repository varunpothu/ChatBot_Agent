from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    name: str
    version: str
    content_hash: str
    status: str
    category: str
    owner: str | None = None
    source_uri: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None

class DocumentRepository:
    def save(self, document: DocumentRecord) -> None:
        raise NotImplementedError

    def activate(self, document_id: str, version: str) -> None:
        raise NotImplementedError

    def archive(self, document_id: str, version: str) -> None:
        raise NotImplementedError
