import asyncio
import os

from agents.answer_prompt import build_system_prompt

class BedrockAnswerModel:
    """AWS-native low-cost adapter for synthesis questions only."""
    def __init__(self, model_id: str | None = None, region: str | None = None):
        import boto3
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region or os.getenv("AWS_REGION", "eu-west-2"),
        )
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "180"))

    def _invoke(self, question: str, evidence: list[str], style: str) -> str:
        system = build_system_prompt(style)
        evidence_text = "\n".join(f"[S{i}] {item}" for i, item in enumerate(evidence, 1))
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{
                "role": "user",
                "content": [{"text": f"EVIDENCE:\n{evidence_text}\n\nQUESTION: {question}"}],
            }],
            inferenceConfig={"temperature": 0, "maxTokens": self.max_output_tokens},
        )
        return response["output"]["message"]["content"][0]["text"].strip()

    async def generate(self, question: str, evidence: list[str], style: str = "friendly") -> str:
        return await asyncio.to_thread(self._invoke, question, evidence, style)
