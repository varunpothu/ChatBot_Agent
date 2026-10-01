from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from rag.models import DocumentChunk, DocumentMetadata


@dataclass(frozen=True)
class IngestionResult:
    document: DocumentMetadata
    chunks: list[DocumentChunk]


def extract_pdf_chunks(path: str | Path, document: DocumentMetadata, chunk_size: int = 900, overlap: int = 120) -> IngestionResult:
    """Extract page-aware chunks while retaining source metadata.

    This deliberately keeps page boundaries so citations can point users
    back to the exact source page.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    reader = PdfReader(str(path))
    chunks: list[DocumentChunk] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue

        start = 0
        local_index = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}-p{page_number}-{local_index}",
                        document=document,
                        page=page_number,
                        section=None,
                        text=chunk_text,
                    )
                )
                local_index += 1
            if end == len(text):
                break
            start = end - overlap

    return IngestionResult(document=document, chunks=chunks)
