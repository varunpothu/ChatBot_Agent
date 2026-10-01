# Multi-format knowledge ingestion

CoachAI uses one normalized evidence contract regardless of source format.

Supported now:
- PDF
- DOCX
- PPTX
- XLSX / XLS
- CSV
- TXT
- Markdown
- HTML
- JSON

Images and scanned documents are classified and reserved for OCR/vision ingestion. They must not be treated as ordinary text files.

Accuracy flow:
1. Detect format.
2. Extract text and structure.
3. Preserve source location where possible.
4. Normalize.
5. Chunk.
6. Apply version/status/access metadata.
7. Embed and index.
8. Hybrid retrieve and rerank.
9. Generate only from evidence.
10. Verify claims and citations.
11. Abstain if evidence is insufficient.
