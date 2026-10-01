from __future__ import annotations

import json
import os
from functools import lru_cache


class BedrockTitanEmbeddingProvider:
    """Managed 512-dimension embeddings for the durable pgvector path."""

    def __init__(
        self,
        model_id: str | None = None,
        region: str | None = None,
        dimensions: int | None = None,
        normalize: bool = True,
    ):
        import boto3

        self.model_id = model_id or os.getenv(
            "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
        )
        self.region = region or os.getenv("AWS_REGION", "eu-west-2")
        self.dimensions = int(
            dimensions or os.getenv("BEDROCK_EMBEDDING_DIMENSIONS", "512")
        )
        self.normalize = normalize
        if self.dimensions not in {256, 512, 1024}:
            raise ValueError("Titan Text Embeddings V2 dimensions must be 256, 512 or 1024")
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    def embed_one(self, text: str) -> list[float]:
        value = text.strip()
        if not value:
            return []
        response = self.client.invoke_model(
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json",
            body=json.dumps(
                {
                    "inputText": value,
                    "dimensions": self.dimensions,
                    "normalize": self.normalize,
                },
                ensure_ascii=False,
            ),
        )
        payload = json.loads(response["body"].read())
        vector = payload.get("embedding") or payload.get("embeddingsByType", {}).get("float")
        if not vector:
            raise ValueError("Bedrock returned no float embedding")
        if len(vector) != self.dimensions:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimensions}, got {len(vector)}"
            )
        return [float(item) for item in vector]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_one(text)


@lru_cache(maxsize=4)
def build_bedrock_embedding_provider() -> BedrockTitanEmbeddingProvider:
    return BedrockTitanEmbeddingProvider()
