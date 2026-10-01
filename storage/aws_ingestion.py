from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IngestionTarget:
    bucket: str
    queue_url: str
    prefix: str = "documents"


class AWSIngestionPublisher:
    """Immutable S3 source + SQS event publisher.

    The API uploads bytes once, then the worker owns parsing/OCR/chunking.
    """

    def __init__(self, target: IngestionTarget | None = None, region: str | None = None):
        import boto3

        self.target = target or IngestionTarget(
            bucket=os.getenv("DOCUMENT_S3_BUCKET", ""),
            queue_url=os.getenv("DOCUMENT_INGESTION_QUEUE_URL", ""),
            prefix=os.getenv("DOCUMENT_S3_PREFIX", "documents"),
        )
        if not self.target.bucket or not self.target.queue_url:
            raise ValueError("DOCUMENT_S3_BUCKET and DOCUMENT_INGESTION_QUEUE_URL are required")
        session_region = region or os.getenv("AWS_REGION", "eu-west-2")
        self.s3 = boto3.client("s3", region_name=session_region)
        self.sqs = boto3.client("sqs", region_name=session_region)

    def upload_file(
        self,
        path: str | Path,
        *,
        document_id: str,
        filename: str,
        version: str,
        content_hash: str,
    ) -> str:
        path = Path(path)
        key = f"{self.target.prefix}/{document_id}/{filename}"
        self.s3.upload_file(
            str(path),
            self.target.bucket,
            key,
            ExtraArgs={"Metadata": {"sha256": content_hash, "document-version": version}},
        )
        return f"s3://{self.target.bucket}/{key}"

    def enqueue(
        self,
        *,
        document_id: str,
        filename: str,
        version: str,
        content_hash: str,
        source_uri: str,
    ) -> None:
        message = {
            "event": "coachai.document.ingest",
            "document_id": document_id,
            "filename": filename,
            "version": version,
            "content_hash": content_hash,
            "source_uri": source_uri,
        }
        self.sqs.send_message(
            QueueUrl=self.target.queue_url,
            MessageBody=json.dumps(message, separators=(",", ":")),
        )

    def publish_file(
        self,
        path: str | Path,
        *,
        document_id: str,
        filename: str,
        version: str,
        content_hash: str,
    ) -> str:
        source_uri=self.upload_file(path,document_id=document_id,filename=filename,version=version,content_hash=content_hash)
        self.enqueue(document_id=document_id,filename=filename,version=version,content_hash=content_hash,source_uri=source_uri)
        return source_uri
