from dataclasses import dataclass
import re

from rag.retrieval import STOPWORDS

@dataclass(frozen=True)
class VerificationResult:
    grounded: bool
    score: float
    unsupported_claims: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()

def _facts_only(answer: str) -> str:
    filler = (
        r"\bsure\b[,.]?\s*",
        r"\bbased on the approved (centre|center) information[,:]?\s*",
        r"\baccording to the approved (centre|center) information[,:]?\s*",
    )
    text = answer
    for pattern in filler:
        text = re.sub(pattern, "", text, flags=re.I)
    return text.strip()

def _terms(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-zA-Z0-9£$€_.-]+", text.lower()))
    return {t for t in tokens if t not in STOPWORDS}

def verify_claims(answer: str, evidence_text: list[str]) -> VerificationResult:
    if not answer.strip() or not evidence_text:
        return VerificationResult(False, 0.0, ("No verifiable evidence.",))

    facts = _facts_only(answer)
    answer_terms = _terms(facts)
    evidence_terms = _terms(" ".join(evidence_text))
    if not answer_terms:
        return VerificationResult(False, 0.0, ("No factual content detected.",))

    overlap = len(answer_terms & evidence_terms) / max(len(answer_terms), 1)
    grounded = overlap >= 0.35
    return VerificationResult(grounded, round(overlap, 4))
