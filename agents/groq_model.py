import os
import httpx

from agents.answer_prompt import build_system_prompt

class GroqAnswerModel:
    """Optional cloud adapter used only for deep/synthesis questions."""
    def __init__(self, model: str | None = None, prompt_provider=None):
        self.api_key=os.getenv("GROQ_API_KEY")
        self.model=model or os.getenv("GROQ_MODEL")
        if not self.api_key: raise RuntimeError("GROQ_API_KEY is not configured")
        if not self.model: raise RuntimeError("GROQ_MODEL is not configured")
        self.max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS","180"))
        self.prompt_provider=prompt_provider
        self.timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS","8"))
        self.client=httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds,connect=2.0),
            limits=httpx.Limits(max_connections=20,max_keepalive_connections=10),
        )

    async def generate(self, question: str, evidence: list[str], style: str = "friendly", target_language: str = "English") -> str:
        evidence_text="\n".join(f"[S{i}] {item}" for i,item in enumerate(evidence,1))
        payload={
            "model":self.model,
            "temperature":0,
            "max_tokens":self.max_output_tokens,
            "messages":[
                {"role":"system","content":(self.prompt_provider.system_prompt(style,target_language) if self.prompt_provider else None) or build_system_prompt(style,target_language)},
                {"role":"user","content":f"EVIDENCE:\n{evidence_text}\n\nQUESTION: {question}"},
            ],
        }
        response=await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization":f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
