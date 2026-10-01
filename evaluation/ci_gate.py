import sys
from datetime import date
import asyncio

from agents.orchestrator import CoachAIOrchestrator
from evaluation.release_gate import evaluate_release
from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever
from tests.quality_eval import TestCase, run_retrieval_tests

def build_fixture():
    return [
        DocumentChunk("fees-1", DocumentMetadata("fees", "Fees.pdf", "v1", "fees", "ACTIVE", date(2026, 1, 1)), 1, "Fees", "The Data Science course fee is £2800."),
        DocumentChunk("admissions-1", DocumentMetadata("admissions", "Admissions.pdf", "v2", "admissions", "ACTIVE", date(2026, 1, 1)), 2, "Admissions", "Applicants need a completed application form and photo ID."),
        DocumentChunk("schedule-1", DocumentMetadata("schedule", "Schedule.pdf", "v1", "schedule", "ACTIVE", date(2026, 1, 1)), 3, "Schedule", "The evening batch starts at 6pm on weekdays."),
        DocumentChunk("refunds-1", DocumentMetadata("refunds", "Refunds.pdf", "v1", "refunds", "ACTIVE", date(2026, 1, 1)), 4, "Refunds", "Refund requests must be submitted within 14 days."),
    ]

def main() -> int:
    chunks = build_fixture()
    retriever = HybridRetriever(chunks)
    cases = [
        TestCase("What is the Data Science course fee?", ("£2800",)),
        TestCase("What do applicants need?", ("application", "photo ID")),
        TestCase("When does the evening batch start?", ("6pm", "weekdays")),
        TestCase("How long do I have to request a refund?", ("14 days",)),
    ]
    retrieval = run_retrieval_tests(retriever, cases, top_k=3)
    result = asyncio.run(CoachAIOrchestrator(retriever=retriever).run("What is the Data Science course fee?"))
    abstention_result = asyncio.run(CoachAIOrchestrator(retriever=retriever).run("What is the weather on Mars?"))
    citation_accuracy = 1.0 if result.get("citations") and result["verification"]["grounded"] else 0.0
    abstention_ok = bool(abstention_result.get("abstained"))
    gate = evaluate_release(
        {"verification_failures": 0, "average_latency_ms": 0, "abstention_check": abstention_ok},
        retrieval["recall_at_k"],
        citation_accuracy,
    )
    print({"retrieval": retrieval, "citation_accuracy": citation_accuracy, "abstention_ok": abstention_ok, "release_gate": gate.__dict__})
    if not gate.passed:
        print("AI QUALITY GATE FAILED:", "; ".join(gate.reasons), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
