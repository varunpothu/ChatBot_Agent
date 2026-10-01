from __future__ import annotations

import os
from pathlib import Path

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
