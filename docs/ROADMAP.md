# CoachAI Platform Roadmap

## Implemented now

### Conversation and cost
- Human-style response modes: friendly, professional and concise
- Fast deterministic path for simple factual lookups
- One-call deep path only for synthesis/explanation questions
- Adaptive evidence selection
- Strict input, context and output limits
- Response cache with knowledge-generation invalidation
- Minimal structured conversation memory
- Cloud-call daily budget
- Local request rate limiting
- Browser speech input/output as the default low-cost voice path
- Optional cached Amazon Polly TTS
- Runtime cost, token and latency telemetry

### Knowledge and safety
- PDF, DOCX, PPTX, XLS/XLSX, CSV, TXT, Markdown, HTML and JSON ingestion
- Content hashing and duplicate detection
- Version numbering
- PENDING_REVIEW -> APPROVED -> ACTIVE -> ARCHIVED lifecycle
- Active-source filtering before retrieval
- Prompt-injection guard
- Citations
- Human review queue
- Audit events
- Admin API-key protection
- Deterministic retrieval and grounding quality gates in CI configuration

### AI and AWS provider boundaries
- Bedrock Nova Micro adapter for low-cost synthesis
- Bedrock Titan Text Embeddings V2 adapter with configurable dimensions
- Groq adapter remains optional
- AWS Polly adapter
- AWS Transcribe boundary
- PostgreSQL/pgvector production schema
- S3/SQS/Textract/ECS/CloudWatch/Secrets Manager/IAM target architecture

## Still to integrate for a multi-instance production deployment

1. PostgreSQL/pgvector as the runtime source of truth, replacing the in-memory store.
2. S3 as immutable document storage.
3. SQS workers for parsing, OCR, chunking and embeddings.
4. AWS Textract for scanned/image documents.
5. Distributed cache/rate limiting with Redis/ElastiCache or gateway controls.
6. Amazon Transcribe streaming adapter for server-side voice.
7. OIDC/IAM/API Gateway authentication instead of the development admin-key mechanism.
8. Full model/prompt registry persistence and approval workflow.
9. Larger golden evaluation suite covering retrieval, citations, faithfulness, adversarial inputs, latency and cost.
10. Terraform/IaC, deployment pipelines, CloudWatch SLOs and operational runbooks.

## Scale target

The architecture is intentionally designed so higher traffic does not automatically mean higher model usage. The preferred scaling path is:

more users -> more cached/local retrieval -> more shared infrastructure -> only proportionally more deep model calls.

Do not optimize for “smallest model at any cost.” Optimize for the cheapest architecture that passes the required quality and safety gates.
