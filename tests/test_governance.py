from datetime import date
from rag.models import DocumentMetadata, DocumentStatus
from knowledge.governance import is_answerable, validate_transition

def doc(status=DocumentStatus.ACTIVE):
    return DocumentMetadata(
        document_id="d1", name="Fees.docx", version="2",
        category="fees", status=status,
        effective_from=date(2026, 1, 1),
        access_level="student",
    )

def test_active_current_document_is_answerable():
    assert is_answerable(doc(), date(2026, 10, 1))

def test_draft_is_not_answerable():
    assert not is_answerable(doc(DocumentStatus.DRAFT), date(2026, 10, 1))

def test_expired_document_is_not_answerable():
    d=doc(); d=DocumentMetadata(**{**d.__dict__, "effective_until": date(2026, 9, 30)})
    assert not is_answerable(d, date(2026, 10, 1))

def test_transition_requires_review():
    validate_transition(DocumentStatus.PROCESSING, DocumentStatus.PENDING_REVIEW)
