import json
import os

class BedrockEmbeddingProvider:
    """Amazon Titan Text Embeddings V2 adapter.

    512 dimensions gives a smaller vector footprint than the default 1024
    dimensions while remaining configurable for evaluation.
    """
    def __init__(self, model_id: str | None = None, region: str | None = None, dimensions: int = 512):
        import boto3
        self.model_id = model_id or os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
        self.region = region or os.getenv("AWS_REGION", "eu-west-2")
        self.dimensions = int(os.getenv("BEDROCK_EMBEDDING_DIMENSIONS", str(dimensions)))
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inputText": text[:50000],
                    "dimensions": self.dimensions,
                    "normalize": True,
                }),
                contentType="application/json",
                accept="application/json",
            )
            body = json.loads(response["body"].read())
            vectors.append(body["embedding"])
        return vectors
