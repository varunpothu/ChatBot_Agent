# AWS Production Architecture

## Target runtime

Student request -> API Gateway/CloudFront -> ECS/Fargate API -> authorization -> deterministic routing -> hybrid retrieval -> adaptive evidence -> fast extraction OR one Bedrock synthesis call -> verification -> citations -> optional voice -> CloudWatch.

## Knowledge lifecycle

Upload -> S3 -> SQS -> parser/OCR worker -> logical chunking -> embedding cache -> pgvector -> PENDING_REVIEW -> APPROVED -> ACTIVE.

Only ACTIVE documents are eligible for student retrieval. Replacing a version archives the old active version after approval.

## AWS services

- S3: immutable source and processed artifacts
- SQS: asynchronous document/evaluation work
- Textract: OCR/layout for scans and image-heavy documents
- RDS PostgreSQL + pgvector: source metadata, chunks and vectors
- Bedrock: low-cost text generation and future model routing
- Polly: optional paid neural TTS
- Transcribe: optional streaming server-side STT
- ECS/Fargate: API and background workers
- CloudWatch: logs, metrics, alarms and cost/SLO telemetry
- Secrets Manager: provider credentials and application secrets
- IAM: least-privilege service identities
- API Gateway/WAF: authentication, throttling and edge protection

## Cost strategy

The application-level cost firewall runs before expensive inference:

1. input normalization/caps
2. injection detection
3. rate limiting
4. cache lookup
5. deterministic routing
6. approved-evidence retrieval
7. adaptive evidence sizing
8. cloud-call budget
9. strict output cap
10. verification

Bedrock prompt caching can reduce latency and input-token cost for supported models and repeated prompt prefixes. Keep stable instructions/reference material before dynamic user content and verify cache-read/write usage on the target model.

Bedrock intelligent prompt routing can route a request among configured models in a model family, with performance and cost metrics available for monitoring. This is an optional second layer; CoachAI's own fast/deep gate should run first so simple questions never incur model inference.

Nova Micro is currently documented by AWS as a fast, low-cost text-only model, making it an appropriate candidate for the deep path rather than using a large general model for every question.

Titan Text Embeddings V2 is intended for retrieval and supports 256, 512 or 1024 dimensions. CoachAI defaults its production adapter to 512 and should choose the smallest dimension that passes retrieval evaluation.

For voice, browser speech remains the cheapest default. Production server-side STT can use streaming Transcribe and partial-result stabilization for lower perceived latency.

## Reliability and escalation

If a cloud model is slow or unavailable, the application falls back to deterministic evidence or human review. It never retries indefinitely and never invents a response to hide a provider failure.

The development admin key is a bounded demo control. Production should replace it with OIDC/IAM/API Gateway authorization.
