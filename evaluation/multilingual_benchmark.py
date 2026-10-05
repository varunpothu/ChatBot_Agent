from __future__ import annotations

import argparse
import json
import statistics
import time

from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever


CASES = [
    ("What is the course fee?", "fees", "en-GB"),
    ("कोर्स की फीस कितनी है?", "fees", "hi-IN"),
    ("కోర్సు ఫీజు ఎంత?", "fees", "te-IN"),
    ("コース料金はいくらですか？", "fees", "ja-JP"),
    ("What documents do I need to apply?", "admissions", "en-GB"),
    ("आवेदन करने के लिए कौन से दस्तावेज़ चाहिए?", "admissions", "hi-IN"),
    ("దరఖాస్తు చేయడానికి ఏ పత్రాలు కావాలి?", "admissions", "te-IN"),
    ("Quels documents dois-je fournir pour postuler ?", "admissions", "fr-FR"),
    ("When does the evening batch start?", "schedule", "en-GB"),
    ("शाम की कक्षा कब शुरू होती है?", "schedule", "hi-IN"),
    ("వీక్ఎండ్ కాదు, సాయంత్రం బ్యాచ్ ఎప్పుడు మొదలవుతుంది?", "schedule", "te-IN"),
    ("Quelles sont les heures du cours du soir ?", "schedule", "fr-FR"),
    ("What is the refund window?", "refunds", "en-GB"),
    ("रिफंड कितने दिनों के भीतर माँगना होता है?", "refunds", "hi-IN"),
    ("환불은 며칠 안에 요청해야 하나요?", "refunds", "ko-KR"),
    ("Quel est le délai pour demander un remboursement ?", "refunds", "fr-FR"),
]


CHUNKS = [
    ("fees", "Fees", "The Data Science course fee is £2800."),
    ("admissions", "Admissions", "Applicants need a completed application form and photo ID."),
    ("schedule", "Schedule", "The evening batch starts at 6pm on weekdays."),
    ("refunds", "Refunds", "Refund requests must be submitted within 14 days."),
]


def build_retriever() -> HybridRetriever:
    return HybridRetriever(
        [
            DocumentChunk(
                chunk_id,
                DocumentMetadata(chunk_id, f"{title}.pdf", "v1", chunk_id, "ACTIVE"),
                1,
                title,
                text,
            )
            for chunk_id, title, text in CHUNKS
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark cross-language retrieval.")
    parser.add_argument("--provider", default="auto", choices=["auto", "hash", "local_e5"])
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--min-recall-at-1", type=float, default=None)
    args = parser.parse_args()

    import os

    os.environ["MULTILINGUAL_EMBEDDING_PROVIDER"] = args.provider
    retriever = build_retriever()
    top_k = max(1, min(args.top_k, len(CHUNKS)))

    rows = []
    reciprocal_ranks = []
    ndcgs = []
    for question, expected_id, language in CASES:
        started = time.perf_counter()
        results = retriever.search(question, top_k=top_k)
        elapsed = (time.perf_counter() - started) * 1000
        rank = next(
            (index + 1 for index, hit in enumerate(results) if hit.chunk.chunk_id == expected_id),
            None,
        )
        rr = 1.0 / rank if rank else 0.0
        ndcg = 1.0 / __import__("math").log2(rank + 1) if rank else 0.0
        reciprocal_ranks.append(rr)
        ndcgs.append(ndcg)
        rows.append(
            {
                "language": language,
                "question": question,
                "expected_chunk": expected_id,
                "rank": rank,
                "hit_at_1": rank == 1,
                "hit_at_k": rank is not None,
                "latency_ms": round(elapsed, 2),
            }
        )

    recall_at_1 = sum(row["hit_at_1"] for row in rows) / len(rows)
    recall_at_k = sum(row["hit_at_k"] for row in rows) / len(rows)
    p50 = statistics.median(row["latency_ms"] for row in rows)
    p95 = sorted(row["latency_ms"] for row in rows)[min(len(rows) - 1, int(len(rows) * 0.95))]

    summary = {
        "provider": args.provider,
        "cross_language_enabled": retriever.supports_cross_language,
        "cases": len(CASES),
        "recall_at_1": round(recall_at_1, 4),
        "recall_at_k": round(recall_at_k, 4),
        "mrr": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4),
        "ndcg_at_k": round(sum(ndcgs) / len(ndcgs), 4),
        "latency_ms": {"p50": p50, "p95": p95},
        "results": rows,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.min_recall_at_1 is not None and recall_at_1 < args.min_recall_at_1:
        raise SystemExit(
            f"Recall@1 {recall_at_1:.4f} is below required {args.min_recall_at_1:.4f}"
        )


if __name__ == "__main__":
    main()
