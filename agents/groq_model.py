import os
import httpx

from agents.answer_prompt import SYSTEM_PROMPT

class GroqAnswerModel:
    """Optional OpenAI-compatible Groq adapter.

    The adapter is only enabled when GROQ_API_KEY is configured. Keeping the
    provider behind the AnswerModel boundary lets the project swap to AWS
    Bedrock or another provider without changing retrieval or verification.
    """

    def __init__(self, model: str | None = None):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        if not self.model:
            raise RuntimeError("GROQ_MODEL is not configured")

    async def generate(self, question: str, evidence: list[str]) -> str:
        evidence_text = "\n\n".join(
            f"[S{i}] {item}" for i, item in enumerate(evidence, start=1)
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + evidence_text},
                {"role": "user", "content": question},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
