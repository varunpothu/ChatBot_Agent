from dataclasses import dataclass
from rag.retrieval import HybridRetriever

@dataclass(frozen=True)
class TestCase:
    question: str
    expected_terms: tuple[str, ...]

def run_retrieval_tests(retriever: HybridRetriever, cases: list[TestCase], top_k: int = 5) -> dict:
    if not cases:
        return {"cases": 0, "recall_at_k": 0.0, "term_coverage": 0.0}
    hits = 0
    coverage = 0.0
    for case in cases:
        results = retriever.search(case.question, top_k=top_k)
        text = " ".join(r.chunk.text.lower() for r in results)
        found = sum(term.lower() in text for term in case.expected_terms)
        hits += found > 0
        coverage += found / len(case.expected_terms) if case.expected_terms else 1.0
    return {
        "cases": len(cases),
        "recall_at_k": round(hits / len(cases), 4),
        "term_coverage": round(coverage / len(cases), 4),
    }
