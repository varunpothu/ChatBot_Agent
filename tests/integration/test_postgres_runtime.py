import os
from datetime import datetime, timezone

import pytest

from knowledge.document_registry import ManagedDocument
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from rag.retrieval import PostgresHybridRetriever
from storage.postgres import PostgresRuntime
from governance.registry import GovernanceRegistry

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


class FakeQueryEmbeddingProvider:
    model_id = "integration-fake"
    dimensions = 512

    def embed_query(self, _text):
        return [1.0] + [0.0] * 511


def test_postgres_vector_retrieval_hits_persisted_embedding():
    runtime = get_runtime()
    registry = runtime.document_registry()
    name = "Integration-Retrieval.pdf"
    doc_id = "integration-retrieval-doc-001"
    doc = ManagedDocument(
        doc_id,
        name,
        registry.next_version(name),
        "integration-hash-002",
        "general",
        "PENDING_REVIEW",
        datetime.now(timezone.utc),
    )
    registry.add(doc)

    store = runtime.knowledge_store()
    chunk = DocumentChunk(
        f"{doc_id}-chunk-1",
        DocumentMetadata(doc_id, name, doc.version, "general", DocumentStatus.PENDING_REVIEW),
        1,
        "Refunds",
        "Refund requests must be submitted within 14 days.",
        [1.0] + [0.0] * 511,
    )
    store.add([chunk])
    registry.activate(doc_id, "integration-test")

    retriever = PostgresHybridRetriever(
        store,
        embedding_provider=FakeQueryEmbeddingProvider(),
    )
    results = retriever.search("refund requests", top_k=1)

    assert len(results) == 1
    assert results[0].chunk.text.startswith("Refund requests")
    assert results[0].semantic_score > 0.99
    runtime.engine.dispose()


def test_postgres_governance_requires_evaluation_reference_for_activation():
    runtime = get_runtime()
    registry = GovernanceRegistry(runtime)

    prompt = registry.register_prompt(
        "answer.integration",
        "v1",
        "Answer only from evidence in {TARGET_LANGUAGE}.",
        owner="integration-test",
    )
    assert prompt.status == "PENDING_REVIEW"

    registry.approve_prompt("answer.integration", "v1", "reviewer", "ci://golden/answer-integration-v1")
    active = registry.activate_prompt(
        "answer.integration",
        "v1",
        "reviewer",
        "ci://golden/answer-integration-v1",
    )
    assert active.status == "ACTIVE"
    assert active.evaluation_reference == "ci://golden/answer-integration-v1"
    runtime.engine.dispose()
