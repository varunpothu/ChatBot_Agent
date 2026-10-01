def assurance_summary(kpis: dict, retrieval_recall: float) -> dict:
    checks = {
        "evidence_grounding": kpis.get("verification_failures", 0) == 0,
        "retrieval_quality": retrieval_recall >= 0.80,
        "latency": kpis.get("average_latency_ms", 0) <= 3000,
    }
    return {"checks": checks, "ready": all(checks.values())}
