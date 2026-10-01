import os
import re
from dataclasses import dataclass
from typing import Literal

AnswerMode = Literal["fast", "deep"]


@dataclass(frozen=True)
class CostPolicy:
    max_input_chars: int = 1400
    retrieval_top_k: int = 3
    max_evidence_chars: int = 3600
    max_output_tokens: int = 180
    cache_ttl_seconds: int = 300
    llm_enabled: bool = True
    deep_word_limit: int = 20
    low_score_threshold: float = 0.18

    @classmethod
    def from_env(cls) -> "CostPolicy":
        return cls(
            max_input_chars=int(os.getenv("MAX_INPUT_CHARS", "1400")),
            retrieval_top_k=int(os.getenv("TOP_K_FINAL", "3")),
            max_evidence_chars=int(os.getenv("MAX_EVIDENCE_CHARS", "3600")),
            max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "180")),
            cache_ttl_seconds=int(os.getenv("RESPONSE_CACHE_TTL_SECONDS", "300")),
            llm_enabled=os.getenv("LLM_ENABLED", "true").lower() == "true",
            deep_word_limit=int(os.getenv("DEEP_WORD_LIMIT", "20")),
            low_score_threshold=float(os.getenv("LOW_RETRIEVAL_SCORE", "0.18")),
        )


def classify_answer_mode(message: str, policy: CostPolicy) -> AnswerMode:
    text = re.sub(r"\s+", " ", message.strip().lower())
    words = text.split()
    deep_signals = (
        "compare", "difference", "why", "explain", "summarise", "summarize",
        "step by step", "recommend", "which one", "how does", "pros and cons",
        "multiple", "options", "scenario", "example",
    )
    if len(words) > policy.deep_word_limit:
        return "deep"
    if any(signal in text for signal in deep_signals):
        return "deep"
    if text.count("?") > 1:
        return "deep"
    return "fast"


def trim_evidence(evidence: list[str], max_chars: int) -> list[str]:
    budget = max(0, int(max_chars))
    selected: list[str] = []
    total = 0

    for item in evidence:
        clean = re.sub(r"\s+", " ", item).strip()
        if not clean or total >= budget:
            continue

        remaining = budget - total
        if len(clean) <= remaining:
            selected.append(clean)
            total += len(clean)
            continue

        if remaining <= 1:
            selected.append(clean[:remaining])
            break

        trimmed = clean[:remaining - 1].rstrip()
        if not trimmed:
            selected.append(clean[:remaining])
            break

        selected.append(trimmed + "…")
        break

    return selected
