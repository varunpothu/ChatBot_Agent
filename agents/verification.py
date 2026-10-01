from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    grounded: bool
    score: float
    unsupported_claims: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()


def verify_claims(answer: str, evidence_text: list[str]) -> VerificationResult:
    """Conservative baseline verifier.

    Full claim-level NLI/LLM verification will be added after retrieval.
    An empty evidence set always fails closed.
    """
    if not answer.strip() or not evidence_text:
        return VerificationResult(False, 0.0, ("No verifiable evidence.",))

    combined = " ".join(evidence_text).lower()
    answer_terms = set(answer.lower().split())
    evidence_terms = set(combined.split())
    overlap = len(answer_terms & evidence_terms) / max(len(answer_terms), 1)

    grounded = overlap >= 0.35
    return VerificationResult(grounded, overlap)
