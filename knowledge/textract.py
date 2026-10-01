from __future__ import annotations

import os
from pathlib import Path
import time

from knowledge.document_types import DocumentType
from knowledge.schema import NormalizedDocument, SourceLocation


class AmazonTextractProvider:
    """AWS Textract text extraction for image documents."""

    def __init__(self, region: str | None = None):
        import boto3
        self.client = boto3.client("textract", region_name=region or os.getenv("AWS_REGION", "eu-west-2"))

    def detect_s3(self, bucket: str, key: str, *, filename: str) -> NormalizedDocument:
        response = self.client.detect_document_text(
            Document={"S3Object": {"Bucket": bucket, "Name": key}}
        )
        parts: list[str] = []
        locations: list[SourceLocation] = []
        current_page = 1
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "PAGE":
                current_page = int(block.get("Page", current_page))
            elif block.get("BlockType") == "LINE":
                value = (block.get("Text") or "").strip()
                if value:
                    parts.append(value)
                    locations.append(SourceLocation(page=current_page))
        return NormalizedDocument(
            Path(filename).stem,
            filename,
            DocumentType.IMAGE,
            Path(filename).stem,
            "\n".join(parts),
            tuple(locations),
        )


    def detect_s3_async(
        self,
        bucket: str,
        key: str,
        *,
        filename: str,
        timeout_seconds: int = 180,
        poll_seconds: float = 2.0,
    ) -> NormalizedDocument:
        """Poll asynchronous Textract text detection for multi-page S3 documents."""
        token = __import__("hashlib").sha256(
            f"{bucket}/{key}".encode("utf-8")
        ).hexdigest()[:48]
        started = self.client.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
            ClientRequestToken=token,
        )
        job_id = started["JobId"]
        deadline = time.monotonic() + timeout_seconds
        next_token = None
        parts: list[str] = []
        locations: list[SourceLocation] = []

        while time.monotonic() < deadline:
            kwargs = {"JobId": job_id, "MaxResults": 1000}
            if next_token:
                kwargs["NextToken"] = next_token
            response = self.client.get_document_text_detection(**kwargs)
            status = response.get("JobStatus")
            if status == "FAILED":
                raise RuntimeError(response.get("StatusMessage", "Textract job failed"))
            if status != "SUCCEEDED":
                time.sleep(poll_seconds)
                continue

            for block in response.get("Blocks", []):
                if block.get("BlockType") == "LINE":
                    value = (block.get("Text") or "").strip()
                    if value:
                        parts.append(value)
                        locations.append(
                            SourceLocation(page=int(block.get("Page", 1)))
                        )
            next_token = response.get("NextToken")
            if not next_token:
                return NormalizedDocument(
                    Path(filename).stem,
                    filename,
                    DocumentType.PDF,
                    Path(filename).stem,
                    "\n".join(parts),
                    tuple(locations),
                )

        raise TimeoutError("Textract text detection timed out")
