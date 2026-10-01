from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import tempfile
import time

from knowledge.chunker import semantic_chunks
from knowledge.parsers import parse_document
from knowledge.document_types import detect_type, DocumentType
from knowledge.textract import AmazonTextractProvider
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from rag.managed_embeddings import CachedEmbeddingProvider, build_bedrock_embedding_provider
from storage.postgres import PostgresRuntime


class IngestionWorker:
    """SQS worker for expensive document processing.

    Processing is deliberately outside the student request path.
    """

    def __init__(self, runtime: PostgresRuntime):
        self.runtime = runtime
        self.store = runtime.knowledge_store()
        self.documents = runtime.document_registry()
        self.ops = runtime.ops()

    def process_message(self, payload: dict) -> int:
        document_id = payload["document_id"]
        source_uri = payload["source_uri"]
        bucket, key = source_uri[5:].split("/", 1)

        import boto3

        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "eu-west-2"))
        suffix = Path(payload["filename"]).suffix.lower()

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / f"{document_id}{suffix}"
            s3.download_file(bucket, key, str(destination))
            digest=hashlib.sha256(destination.read_bytes()).hexdigest()
            if digest != payload["content_hash"]:
                raise ValueError("S3 object hash does not match the upload manifest")
            normalized = parse_document(destination) if detect_type(payload["filename"]) != DocumentType.IMAGE else None
            if os.getenv("OCR_PROVIDER", "none").lower() == "textract" and (
                normalized is None or not normalized.text.strip()
            ):
                textract = AmazonTextractProvider(region=os.getenv("AWS_REGION", "eu-west-2"))
                if suffix == ".pdf":
                    normalized = textract.detect_s3_async(
                        bucket,
                        key,
                        filename=payload["filename"],
                        timeout_seconds=int(os.getenv("TEXTRACT_TIMEOUT_SECONDS", "180")),
                        poll_seconds=float(os.getenv("TEXTRACT_POLL_SECONDS", "2")),
                    )
                else:
                    normalized = textract.detect_s3(
                        bucket,
                        key,
                        filename=payload["filename"],
                    )
            if normalized is None:
                raise ValueError("Image document requires OCR_PROVIDER=textract in async ingestion mode")
            if not normalized.text.strip():
                raise ValueError("No extractable text was found in the document")
            chunks = semantic_chunks(normalized)
            metadata = self.documents.get(document_id)
            document_metadata = DocumentMetadata(
                document_id=document_id,
                name=metadata.name,
                version=metadata.version,
                category=metadata.category,
                status=DocumentStatus.PENDING_REVIEW,
            )
            cache=None
            if os.getenv("REDIS_URL","").strip():
                from infra.redis_runtime import RedisTTLCache
                cache=RedisTTLCache(
                    os.getenv("REDIS_URL",""),
                    ttl_seconds=int(os.getenv("EMBEDDING_CACHE_TTL_SECONDS","900")),
                    namespace="coachai:document-embeddings",
                )
            embedding_provider = CachedEmbeddingProvider(build_bedrock_embedding_provider(), cache=cache)
            vectors = embedding_provider.embed([item.text for item in chunks])
            converted = [
                DocumentChunk(
                    chunk_id=f"{document_id}-{i}",
                    document=document_metadata,
                    page=item.location.page,
                    section=item.location.section,
                    text=item.text,
                    embedding=vectors[i],
                )
                for i, item in enumerate(chunks)
            ]
            self.store.add(converted)
            self.documents.set_status(document_id, "PENDING_REVIEW")
            event = self.ops.audit(
                "DOCUMENT_INGESTION_COMPLETED",
                "ingestion-worker",
                document_id,
                {"source_uri": source_uri, "chunks": len(converted)},
            )
            return len(converted)


def run_once(body: str) -> int:
    runtime = PostgresRuntime(
        os.getenv("DATABASE_URL", ""),
        auto_init_schema=False,
    )
    payload = json.loads(body)
    return IngestionWorker(runtime).process_message(payload)


def main() -> None:
    import boto3

    queue_url=os.getenv("DOCUMENT_INGESTION_QUEUE_URL","")
    if not queue_url:
        raise RuntimeError("DOCUMENT_INGESTION_QUEUE_URL is required")
    runtime=PostgresRuntime(os.getenv("DATABASE_URL",""),auto_init_schema=False)
    worker=IngestionWorker(runtime)
    sqs=boto3.client("sqs",region_name=os.getenv("AWS_REGION","eu-west-2"))
    while True:
        response=sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=20,
            VisibilityTimeout=int(os.getenv("INGESTION_VISIBILITY_TIMEOUT_SECONDS","300")),
        )
        for message in response.get("Messages",[]):
            try:
                worker.process_message(json.loads(message["Body"]))
            except Exception as exc:
                worker.ops.audit("DOCUMENT_INGESTION_FAILED","ingestion-worker",None,{"error":str(exc),"message_id":message.get("MessageId")})
            else:
                sqs.delete_message(QueueUrl=queue_url,ReceiptHandle=message["ReceiptHandle"])
        if not response.get("Messages"):
            time.sleep(0.2)
