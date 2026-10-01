from typing import Protocol

class AnswerModel(Protocol):
    async def generate(self, question: str, evidence: list[str], style: str = "friendly", target_language: str = "English") -> str:
        ...

class ExtractiveAnswerModel:
    """Zero-LLM local path."""
    async def generate(self, question: str, evidence: list[str], style: str = "friendly", target_language: str = "English") -> str:
        return evidence[0] if evidence else ""
