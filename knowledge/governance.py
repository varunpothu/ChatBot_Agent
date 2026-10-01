from datetime import date

from rag.models import DocumentMetadata, DocumentStatus

def is_answerable(document: DocumentMetadata, today: date | None = None) -> bool:
    today = today or date.today()
    if document.status != DocumentStatus.ACTIVE:
        return False
    if document.access_level != "student":
        return False
    if document.effective_from and today < document.effective_from:
        return False
    if document.effective_until and today > document.effective_until:
        return False
    return True

def validate_transition(current: DocumentStatus, target: DocumentStatus) -> None:
    allowed = {
        DocumentStatus.DRAFT: {DocumentStatus.PROCESSING, DocumentStatus.REJECTED},
        DocumentStatus.PROCESSING: {DocumentStatus.PENDING_REVIEW, DocumentStatus.REJECTED},
        DocumentStatus.PENDING_REVIEW: {DocumentStatus.APPROVED, DocumentStatus.REJECTED},
        DocumentStatus.APPROVED: {DocumentStatus.ACTIVE, DocumentStatus.ARCHIVED},
        DocumentStatus.ACTIVE: {DocumentStatus.ARCHIVED},
        DocumentStatus.ARCHIVED: set(),
        DocumentStatus.REJECTED: {DocumentStatus.DRAFT},
    }
    if target not in allowed[current]:
        raise ValueError(f"Invalid document transition: {current} -> {target}")
