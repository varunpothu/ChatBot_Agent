from datetime import date

from agents.verification import verify_claims
from rag.guardrails import only_active_student_evidence
from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever


def make_chunk(status="ACTIVE"):
    doc = DocumentMetadata(
        document_id="doc-1",
        name="Fees.pdf",
        version="v1",
        category="fees",
        status=status,
        effective_from=date(2026, 1, 1),
    )
    return DocumentChunk("chunk-1", doc, 2, "Fees", "The course fee is £2800.")


def test_inactive_documents_are_filtered():
    assert only_active_student_evidence([make_chunk("ARCHIVED")]) == []


def test_keyword_retrieval_returns_matching_evidence():
    result = HybridRetriever([make_chunk()]).search("course fee", top_k=1)
    assert len(result) == 1
    assert result[0].keyword_score > 0


def test_verifier_fails_without_evidence():
    result = verify_claims("The fee is £2800", [])
    assert result.grounded is False
