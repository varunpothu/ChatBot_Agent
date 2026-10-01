import re
from typing import Literal

ConversationStyle = Literal["friendly", "professional", "concise"]

def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    return re.split(r"(?<=[.!?])\s+", clean)

def humanize_factual_answer(answer: str, style: ConversationStyle = "friendly", question: str = "") -> str:
    clean = re.sub(r"\s+", " ", answer).strip()
    if not clean:
        return clean

    sentences = _sentences(clean)
    if question and len(sentences) > 1:
        q_terms = set(re.findall(r"[a-zA-Z0-9£$€]+", question.lower()))
        ranked = sorted(
            sentences,
            key=lambda s: len(q_terms & set(re.findall(r"[a-zA-Z0-9£$€]+", s.lower()))),
            reverse=True,
        )
        clean = ranked[0]
    elif len(sentences) > 3:
        clean = " ".join(sentences[:3])

    if style == "concise":
        return clean
    if style == "professional":
        prefix = "According to the approved centre information, "
    else:
        prefix = "Sure. Based on the approved centre information, "

    if clean.lower().startswith(("according to ", "based on ", "sure.", "the ")):
        return clean
    return prefix + clean[0].lower() + clean[1:] if clean else clean

def humanize_deep_answer(answer: str, style: ConversationStyle = "friendly") -> str:
    clean = re.sub(r"\s+", " ", answer).strip()
    if style == "concise":
        parts = _sentences(clean)
        return " ".join(parts[:3]) if parts else clean
    if style == "professional":
        return clean
    if clean and not clean[0].isupper():
        clean = clean[0].upper() + clean[1:]
    return clean
