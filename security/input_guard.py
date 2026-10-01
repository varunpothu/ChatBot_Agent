import re

INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) instructions",
    r"system prompt",
    r"developer message",
    r"reveal (your|the) instructions",
    r"disregard (the|all) rules",
]

def looks_like_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)
