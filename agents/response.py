import re
from typing import Literal

ConversationStyle = Literal["friendly", "professional", "concise"]

def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    return re.split(r"(?<=[.!?])\s+", clean)

def humanize_factual_answer(answer: str, style: ConversationStyle = "friendly") -> str:
    """Turn extracted evidence into natural language without adding facts."""
    clean = re.sub(r"\s+", " ", answer).strip()
    if not clean:
        return clean

    # Preserve short factual answers exactly enough for fees, dates, names, etc.
    sentences = _sentences(clean)
    if len(sentences) > 3:
        clean = " ".join(sentences[:3])

    if style == "concise":
        return clean

    if style == "professional":
        prefix = "According to the approved centre information, "
    else:
        prefix = "Sure. Based on the approved centre information, "

    # Avoid an awkward double prefix when the source already starts naturally.
    lowered = clean.lower()
    if lowered.startswith(("according to ", "based on ", "sure.", "the ")):
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
