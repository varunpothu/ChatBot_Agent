from dataclasses import dataclass
from datetime import datetime, timezone

from knowledge.governance import validate_transition
from rag.models import DocumentStatus

@dataclass
class ManagedDocument:
    document_id: str
    name: str
    version: str
    content_hash: str
    category: str
    status: str
    uploaded_at: datetime
    approved_by: str | None = None

class InMemoryDocumentRegistry:
    """Development registry mirroring the production document lifecycle."""
    def __init__(self):
        self.documents: dict[str, ManagedDocument] = {}

    def next_version(self, name: str) -> str:
        versions = []
        for doc in self.documents.values():
            if doc.name == name:
                try:
                    versions.append(int(doc.version.lstrip("v")))
                except ValueError:
                    pass
        return f"v{max(versions, default=0) + 1}"

    def add(self, document: ManagedDocument) -> None:
        self.documents[document.document_id] = document

    def list(self) -> list[ManagedDocument]:
        return sorted(self.documents.values(), key=lambda d: d.uploaded_at, reverse=True)

    def get(self, document_id: str) -> ManagedDocument:
        try:
            return self.documents[document_id]
        except KeyError:
            raise KeyError("Document not found") from None

    def activate(self, document_id: str, approved_by: str) -> list[str]:
        target = self.get(document_id)
        if target.status != DocumentStatus.PENDING_REVIEW and target.status != DocumentStatus.APPROVED:
            raise ValueError(f"Document must be APPROVED or PENDING_REVIEW before activation")

        archived: list[str] = []
        for doc_id, doc in self.documents.items():
            if doc_id != document_id and doc.name == target.name and doc.status == DocumentStatus.ACTIVE:
                validate_transition(DocumentStatus.ACTIVE, DocumentStatus.ARCHIVED)
                doc.status = DocumentStatus.ARCHIVED
                archived.append(doc_id)

        if target.status == DocumentStatus.PENDING_REVIEW:
            validate_transition(DocumentStatus.PENDING_REVIEW, DocumentStatus.APPROVED)
            target.status = DocumentStatus.APPROVED
        validate_transition(DocumentStatus.APPROVED, DocumentStatus.ACTIVE)
        target.status = DocumentStatus.ACTIVE
        target.approved_by = approved_by
        return archived

    def reject(self, document_id: str, reviewer: str) -> None:
        target = self.get(document_id)
        if target.status != DocumentStatus.PENDING_REVIEW:
            raise ValueError("Only pending-review documents can be rejected")
        validate_transition(DocumentStatus.PENDING_REVIEW, DocumentStatus.REJECTED)
        target.status = DocumentStatus.REJECTED
        target.approved_by = reviewer

documents = InMemoryDocumentRegistry()
