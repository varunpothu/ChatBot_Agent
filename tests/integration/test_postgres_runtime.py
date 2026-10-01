import os
from datetime import datetime, timezone

import pytest

from knowledge.document_registry import ManagedDocument
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from storage.postgres import PostgresRuntime

pytestmark = pytest.mark.integration


def get_runtime():
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not configured")
    return PostgresRuntime(url, auto_init_schema=True)


def test_postgres_runtime_persists_document_chunk_and_generation():
    runtime = get_runtime()
    name = "Integration-Postgres.pdf"
    registry = runtime.document_registry()
    doc_id = "integration-postgres-doc-001"
    doc = ManagedDocument(
        doc_id,
        name,
        registry.next_version(name),
        "integration-hash-001",
        "general",
        "PENDING_REVIEW",
        datetime.now(timezone.utc),
    )
    registry.add(doc)

    store = runtime.knowledge_store()
    before = store.generation
    chunk = DocumentChunk(
        f"{doc_id}-chunk-1",
        DocumentMetadata(doc_id, name, doc.version, "general", DocumentStatus.PENDING_REVIEW),
        1,
        "Integration",
        "The integration course fee is £100.",
        [1.0] + [0.0] * 511,
    )
    store.add([chunk])

    assert store.generation > before
    assert any(item.text == chunk.text for item in store.all())

    registry.activate(doc_id, "integration-test")
    assert registry.get(doc_id).status == "ACTIVE"
    runtime.engine.dispose()
