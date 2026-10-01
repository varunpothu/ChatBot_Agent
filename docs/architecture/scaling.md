# Scaling strategy

CoachAI scales by keeping the student request path mostly deterministic.

## Stage 1: low traffic

- FastAPI + in-memory retrieval cache
- Browser speech recognition and browser TTS
- Local deterministic retrieval
- Optional one-call Bedrock/Groq synthesis for deep questions
- Process-local response cache and cloud-call circuit breaker

## Stage 2: growing traffic

Move only state that must be shared:

- Redis/ElastiCache for response and retrieval caches
- PostgreSQL/pgvector for active knowledge
- S3 for immutable source documents
- SQS for ingestion/evaluation jobs
- CloudWatch for SLOs and cost alarms

The API contract stays unchanged.

## Stage 3: high-volume knowledge

Do not embed or OCR synchronously in the student request.

Upload -> S3 -> SQS -> parser/OCR worker -> content hash -> chunk -> embedding cache -> vector index -> approval -> active.

Unchanged content should be skipped using its SHA-256 hash. Titan Text Embeddings V2 is designed for retrieval and supports configurable vector dimensions; use the smallest dimension that passes the project's retrieval evaluation rather than assuming the largest vector is necessary.

## Stage 4: high conversational volume

Keep conversation state structured. Store intent, entities, source IDs and a small set of resolved facts. Avoid sending entire transcripts back to the model.

Use exact response caching for repeated questions and only invalidate it when active knowledge changes.

## Stage 5: cost protection

Keep these controls independent:

- per-client rate limit
- daily cloud-call budget
- deep-question classifier
- adaptive evidence count
- input/evidence/output caps
- TTS opt-in
- TTS audio cache
- cloud fallback timeout
- release gate

The system should degrade toward a grounded extractive answer or human review, not toward an unbounded expensive model loop.
