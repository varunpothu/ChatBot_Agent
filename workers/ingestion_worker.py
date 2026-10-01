from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile

from knowledge.chunker import semantic_chunks
from knowledge.document_registry import ManagedDocument
from knowledge.parsers import parse_document
from ops.runtime import RuntimeOps
from rag.models import DocumentChunk, DocumentStatus
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
            normalized = parse_document(destination)
            chunks = semantic_chunks(normalized)
            metadata = self.documents.get(document_id)
            document_metadata = __import__("rag.models", fromlist=["DocumentMetadata"]).DocumentMetadata(
                document_id=document_id,
                name=metadata.name,
                version=metadata.version,
                category=metadata.category,
                status=DocumentStatus.PENDING_REVIEW,
            )
            converted = [
                DocumentChunk(
                    chunk_id=f"{document_id}-{i}",
                    document=document_metadata,
                    page=item.location.page,
                    section=item.location.section,
                    text=item.text,
                )
                for i, item in enumerate(chunks)
            ]
            self.store.add(converted)
            self.documents.set_status(document_id, "PENDING_REVIEW")
            self.store.set_document_status(document_id, DocumentStatus.PENDING_REVIEW)
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
