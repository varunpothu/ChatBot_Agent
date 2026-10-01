from datetime import datetime, timezone
from knowledge.document_registry import InMemoryDocumentRegistry, ManagedDocument

def doc(registry, doc_id, name, version, status):
    item = ManagedDocument(
        document_id=doc_id,
        name=name,
        version=version,
        content_hash=doc_id,
        category="general",
        status=status,
        uploaded_at=datetime.now(timezone.utc),
    )
    registry.add(item)
    return item

def test_new_document_is_pending_review():
    registry = InMemoryDocumentRegistry()
    item = doc(registry, "1", "Fees.pdf", "v1", "PENDING_REVIEW")
    assert item.status == "PENDING_REVIEW"

def test_activation_archives_previous_active_version():
    registry = InMemoryDocumentRegistry()
    old = doc(registry, "1", "Fees.pdf", "v1", "ACTIVE")
    new = doc(registry, "2", "Fees.pdf", "v2", "PENDING_REVIEW")
    archived = registry.activate("2", "admin")
    assert old.status == "ARCHIVED"
    assert new.status == "ACTIVE"
    assert archived == ["1"]
