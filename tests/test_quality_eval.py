from datetime import date

from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever
from tests.quality_eval import TestCase, run_retrieval_tests


def make_chunks():
    return [
        DocumentChunk(
            "fees",
            DocumentMetadata("fees", "Fees.pdf", "v1", "fees", "ACTIVE", date(2026, 1, 1)),
            1,
            "Fees",
            "The Data Science course fee is £2800.",
        ),
        DocumentChunk(
            "refunds",
            DocumentMetadata("refunds", "Refunds.pdf", "v1", "refunds", "ACTIVE", date(2026, 1, 1)),
            2,
            "Refunds",
            "Refund requests must be submitted within 14 days.",
        ),
        DocumentChunk(
            "schedule",
            DocumentMetadata("schedule", "Schedule.pdf", "v1", "schedule", "ACTIVE", date(2026, 1, 1)),
            3,
            "Schedule",
            "The evening batch starts at 6pm on weekdays.",
        ),
    ]


def test_golden_retrieval_covers_distinct_policy_facts():
    retriever = HybridRetriever(make_chunks())
    cases = [
        TestCase("How much is the Data Science course?", ("£2800",)),
        EvalCase("How long do I have to request a refund?", ("14 days",)),
        EvalCase("What time does the evening batch start?", ("6pm",)),
    ]
    result = run_retrieval_tests(retriever, cases, top_k=3)
    assert result["recall_at_k"] == 1.0
    assert result["term_coverage"] == 1.0
