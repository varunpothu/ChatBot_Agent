import argparse
import json
import time

from language.registry import get_language
from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever

CASES = [
    ("What is the course fee?", "£2800", "en-GB"),
    ("कोर्स की फीस कितनी है?", "£2800", "hi-IN"),
    ("కోర్సు ఫీజు ఎంత?", "£2800", "te-IN"),
    ("Quel est le prix du cours ?", "£2800", "fr-FR"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="auto", choices=["auto", "hash", "local_e5"])
    args = parser.parse_args()

    import os
    os.environ["MULTILINGUAL_EMBEDDING_PROVIDER"] = args.provider

    chunks = [
        DocumentChunk(
            "fees",
            DocumentMetadata("fees", "Fees.pdf", "v1", "fees", "ACTIVE"),
            1,
            "Fees",
            "The Data Science course fee is £2800.",
        )
    ]
    retriever = HybridRetriever(chunks)

    rows = []
    for question, expected, language in CASES:
        get_language(language)
        started = time.perf_counter()
        result = retriever.search(question, top_k=1)
        elapsed = (time.perf_counter() - started) * 1000
        text = result[0].chunk.text if result else ""
        rows.append({
            "language": language,
            "question": question,
            "hit": expected.lower() in text.lower(),
            "latency_ms": round(elapsed, 2),
            "score": round(result[0].final_score, 4) if result else 0,
        })

    print(json.dumps({
        "provider": args.provider,
        "cross_language_enabled": retriever.supports_cross_language,
        "results": rows,
        "hit_rate": round(sum(r["hit"] for r in rows) / len(rows), 4),
        "avg_latency_ms": round(sum(r["latency_ms"] for r in rows) / len(rows), 2),
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
