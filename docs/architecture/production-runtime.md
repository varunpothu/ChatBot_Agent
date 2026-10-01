# Production Runtime Architecture

## Request path

Student -> API -> language detection -> security guard -> deterministic routing -> approved-evidence retrieval -> fast extractive answer or one small model call -> grounding verification -> optional translation -> response cache -> optional voice output.

The request path is deliberately kept small. Document parsing and OCR are not allowed to run inside /chat.

## Shared runtime state

When DATABASE_URL is set:

- PostgreSQL becomes the source of truth for documents and chunks.
- Document lifecycle changes are durable.
- A monotonic knowledge generation invalidates stale response caches after knowledge changes.
- Audit events and human-review items survive API restarts and are visible to all instances.

When REDIS_URL is set:

- response and translation caches are shared by API instances;
- the request limiter uses an atomic Redis Lua script with a sliding window;
- cache TTLs remain bounded so stale answers cannot persist indefinitely.

The application keeps its in-memory adapters for development.

## Async document ingestion

With INGESTION_MODE=aws_async:

1. API validates file type, size and SHA-256.
2. API stores the immutable source object in S3.
3. API creates the document record as PROCESSING.
4. API publishes a compact SQS manifest.
5. coachai-ingestion-worker long-polls SQS.
6. Worker downloads the object, verifies its SHA-256, parses and chunks it.
7. Chunks are persisted and the document moves to PENDING_REVIEW.
8. A human must approve the document before it becomes ACTIVE.

This keeps expensive parsing away from student latency and gives the pipeline retry semantics.

## Idempotency

SQS is at-least-once, so ingestion must tolerate duplicates. Chunk inserts use ON CONFLICT DO NOTHING, and S3 integrity is verified against the upload manifest before parsing.

## Vector strategy

The PostgreSQL schema reserves a 512-dimensional pgvector column. The current managed embedding setting is aligned to Amazon Titan Text Embeddings V2 with a configurable 512-dimensional output. The local multilingual E5 profile remains available for cross-language evaluation and can be selected independently.

The next production step is a dedicated embedding worker that writes the selected embedding into the persisted vector column. Until that is enabled, the API can still use the existing local retrieval profiles.

## Failure handling

Redis is used as a shared optimization and safety layer, not as the system of record. PostgreSQL remains authoritative for knowledge state.

The API still has deterministic local fallbacks for answer generation when the cloud model fails. Unsupported, insecure or ambiguous requests remain eligible for human review.

## Required production services

PostgreSQL/pgvector, Redis/ElastiCache, S3, SQS and the API worker runtime are the current shared-service layer. Textract, Transcribe streaming, identity federation, Terraform and full SLO/runbook automation remain separate deployment milestones.