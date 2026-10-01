from typing import Protocol

class AnswerModel(Protocol):
    async def generate(self, question: str, evidence: list[str]) -> str:
        ...

class ExtractiveAnswerModel:
    """Safe local adapter: returns retrieved evidence without inventing facts."""
    async def generate(self, question: str, evidence: list[str]) -> str:
        return evidence[0] if evidence else ""
