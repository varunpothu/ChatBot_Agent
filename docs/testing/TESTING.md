# CoachAI Testing Strategy

## Automated layers

### Unit and deterministic quality

`pytest -q -m "not integration"`

Covers language detection, routing/cost policy, evidence bounds, cache behavior, budgets, document lifecycle, prompt-injection detection, grounding verification, multilingual retrieval configuration, managed embedding caching and AWS adapter contracts.

`python -m evaluation.ci_gate`

Runs a fixed retrieval/citation/grounding corpus through the deterministic release gate. It is intentionally small and reproducible; it is not a claim of broad production model quality.

`python -m compileall agents rag knowledge monitoring governance evaluation ai_controls voice storage infra workers apps`

Checks syntax and imports that are visible to the Python compiler.

### Integration

`pytest -m integration -q`

The CI integration job starts PostgreSQL with pgvector and Redis. It verifies durable document/chunk persistence, knowledge generation changes, lifecycle activation, conversation ownership/deletion, shared cache behavior and distributed request limiting.

### Conversation retention

Durable conversations are deleted with their conversation state, stored turns and linked human-review items. The cleanup command is:

    CONVERSATION_RETENTION_DAYS=30 python scripts/purge_conversations.py

The cleanup uses the durable `updated_at` timestamp and bounds the configured retention period to a safe operational range. Verify deletion of expired conversations and preservation of active conversations in the PostgreSQL integration environment.

### Packaging

`python -m build`

Builds the Python distribution and checks that packaging succeeds before release.

## AWS smoke tests

A real AWS environment must separately validate:

- S3 upload and object ownership/encryption policy.
- SQS enqueue, retry and dead-letter behavior.
- Textract text detection for images and multi-page PDF OCR.
- Bedrock embedding generation and pgvector dimension compatibility.
- Bedrock answer generation only on the deep path.
- Transcribe streaming with a supported language, sample rate and encoding.
- Polly speech synthesis and voice fallback.
- CloudWatch metrics, logs and alarms.
- IAM least-privilege policies and secret access.

Amazon Transcribe streaming requires a supported media format and sample rate, and AWS recommends SDK-based streaming rather than implementing the HTTP/2/WebSocket protocol directly. The current adapter follows the SDK boundary. 

Textract provides synchronous `DetectDocumentText` and asynchronous `StartDocumentTextDetection`/`GetDocumentTextDetection`; the worker uses the asynchronous path for multi-page PDFs. 

## Acceptance gates

Do not call the system production-ready solely because `pytest` passes.

A release should have:

1. Unit tests passing.
2. Deterministic retrieval/grounding gate passing.
3. PostgreSQL/Redis integration tests passing.
4. Package build passing.
5. Compile/static smoke test passing.
6. A real AWS smoke test for ingestion, retrieval and voice paths.
7. Representative latency and cost measurements.
8. Conversation retention/deletion behavior verified for the configured policy.
9. Authentication, IAM, secrets, network and logging review.

## Current verification status

The repository now contains the automated unit, integration and package tests plus the CI definition. This environment does not have the user's AWS account or production PostgreSQL/Redis services, and GitHub Actions has not produced a run for the latest commits. Therefore this work documents the tests and CI gates but does not claim a passing remote test run.

Record the CI workflow URL, commit SHA, test totals, skipped tests, quality-gate result and production smoke-test evidence in the release record.