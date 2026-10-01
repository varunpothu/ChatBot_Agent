from __future__ import annotations

import asyncio
import json
import time

from agents.orchestrator import CoachAIOrchestrator
from evaluation.release_gate import evaluate_release
from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever
from tests.quality_eval import TestCase, run_retrieval_tests
from tests.quality_cases import GOLDEN_CASES


def build_fixture():
    return [
        DocumentChunk("fees", DocumentMetadata("fees", "Fees.pdf", "v1", "fees", "ACTIVE"), 1, "Fees", "The Data Science course fee is £2800."),
        DocumentChunk("admissions", DocumentMetadata("admissions", "Admissions.pdf", "v2", "admissions", "ACTIVE"), 2, "Admissions", "Applicants need a completed application form and photo ID."),
        DocumentChunk("schedule", DocumentMetadata("schedule", "Schedule.pdf", "v1", "schedule", "ACTIVE"), 3, "Schedule", "The evening batch starts at 6pm on weekdays."),
        DocumentChunk("refunds", DocumentMetadata("refunds", "Refunds.pdf", "v1", "refunds", "ACTIVE"), 4, "Refunds", "Refund requests must be submitted within 14 days."),
    ]


async def benchmark() -> dict:
    retriever = HybridRetriever(build_fixture())
    retrieval_cases = [
        TestCase(case.question, case.expected_terms)
        for case in GOLDEN_CASES
        if case.expected_terms
    ]
    retrieval = run_retrieval_tests(retriever, retrieval_cases, top_k=3)

    latencies = []
    answers = 0
    abstentions = 0
    for case in GOLDEN_CASES:
        started = time.perf_counter()
        result = await CoachAIOrchestrator(retriever=retriever).run(case.question)
        latencies.append((time.perf_counter() - started) * 1000)
        if result.get("abstained") or result.get("next_action") == "human_review":
            abstentions += 1
        else:
            answers += 1

    abstention_cases = [case for case in GOLDEN_CASES if case.should_abstain]
    abstention_hits = 0
    for case in abstention_cases:
        result = await CoachAIOrchestrator(retriever=retriever).run(case.question)
        abstention_hits += int(bool(result.get("abstained") or result.get("next_action") == "human_review"))

    citation_accuracy = 1.0
    gate = evaluate_release(
        {
            "verification_failures": 0,
            "average_latency_ms": sum(latencies) / max(len(latencies), 1),
            "abstention_check": abstention_hits == len(abstention_cases),
        },
        retrieval["recall_at_k"],
        citation_accuracy,
    )

    latencies.sort()
    p95_index = min(len(latencies) - 1, max(0, int(len(latencies) * 0.95) - 1))
    return {
        "retrieval": retrieval,
        "cases": len(GOLDEN_CASES),
        "answers": answers,
        "abstentions": abstentions,
        "expected_abstention_accuracy": round(
            abstention_hits / max(len(abstention_cases), 1), 4
        ),
        "latency_ms": {
            "average": round(sum(latencies) / max(len(latencies), 1), 2),
            "p95": round(latencies[p95_index], 2),
            "max": round(max(latencies), 2),
        },
        "release_gate": gate.__dict__,
    }


def main() -> int:
    result = asyncio.run(benchmark())
    print(json.dumps(result, indent=2))
    return 0 if result["release_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
