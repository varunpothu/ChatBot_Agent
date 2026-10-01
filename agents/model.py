from typing import Protocol

class AnswerModel(Protocol):
    async def generate(self, question: str, evidence: list[str], style: str = "friendly") -> str:
        ...

class ExtractiveAnswerModel:
    """Zero-LLM local answer path.

    It can never invent a fact because it returns only retrieved evidence.
    Natural-language wrapping happens outside the model boundary.
    """
    async def generate(self, question: str, evidence: list[str], style: str = "friendly") -> str:
        return evidence[0] if evidence else ""
