from dataclasses import dataclass

@dataclass(frozen=True)
class ReleaseGate:
    passed: bool
    reasons: list[str]

def evaluate_release(kpis: dict, retrieval_recall: float, citation_accuracy: float) -> ReleaseGate:
    reasons = []
    if kpis.get("verification_failures", 0) > 0:
        reasons.append("grounding verification failures detected")
    if retrieval_recall < 0.80:
        reasons.append("retrieval recall below 0.80")
    if citation_accuracy < 0.90:
        reasons.append("citation accuracy below 0.90")
    if kpis.get("average_latency_ms", 0) > 3000:
        reasons.append("latency above 3000ms")
    if kpis.get("abstention_check") is False:
        reasons.append("unsupported-question abstention check failed")
    return ReleaseGate(not reasons, reasons)
