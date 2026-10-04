# CoachAI Platform Roadmap

## Implemented now

### Conversation, multilingual UX and cost
- Human-style response modes: friendly, professional and concise
- Language selector with Auto-detect
- Localized greeting, abstention, human-review and security messages
- English, Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Punjabi, Urdu, Kannada, Malayalam, Spanish, French, German, Arabic, Italian, Portuguese, Japanese and Simplified Chinese text support
- Deterministic script detection for major Indic, Arabic-derived, Japanese and Chinese scripts
- Native cross-language retrieval option using a local multilingual embedding model
- Translation bridge for English-source knowledge bases as a fallback
- Verified-answer translation, not direct unverified translation
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
- Runtime LLM, translation, voice, token and latency telemetry
- Multilingual retrieval benchmark command for real-corpus evaluation

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
- Broader golden evaluation and reproducible quality benchmark
- Terraform infrastructure-as-code reference stack
- Manual OIDC-based deployment workflow
- CloudWatch operations alarms/dashboard and optional AWS budget guardrail
- Persistent model/prompt registry with evaluation-required activation

### AI and AWS provider boundaries
- Bedrock Nova Micro adapter for low-cost synthesis
- Bedrock Titan Text Embeddings V2 adapter with configurable dimensions
- AWS Translate adapter for multilingual retrieval/answer translation
- Optional local multilingual E5 embeddings
- Groq adapter remains optional
- AWS Polly adapter with optional cached dynamic capability discovery
- Amazon Transcribe streaming adapter with optional server-side /stt endpoint
- PostgreSQL/pgvector durable runtime and database-native hybrid retrieval
- S3/SQS/Textract/Transcribe/ECS/CloudWatch/Secrets Manager/IAM production service boundaries

## Integrated production foundations

- PostgreSQL/pgvector runtime backend is selected with DATABASE_URL.
- Durable governed document registry, knowledge generation, audit events and human-review queue are available.
- S3 immutable document source plus an SQS background ingestion path is available through INGESTION_MODE=aws_async.
- Redis shared response/translation caching and an atomic distributed sliding-window request limiter are available through REDIS_URL.
- The ingestion worker verifies the S3 SHA-256 manifest and uses SQS long polling with safe retry semantics.
- Inline ingestion remains the default for local development.

## Still to integrate for a full production deployment

1. Replace the development admin-key operations control with the final production identity/role mapping.
2. Expand the golden corpus with real centre documents, multilingual translated queries and adversarial evaluation sets.
3. Add formal retention/deletion controls for persisted conversation records.
4. Add full deployment SLO dashboards, incident runbooks and restore drills in the target AWS account.

## Scale target

The architecture is intentionally designed so higher traffic does not automatically mean higher model usage. The preferred scaling path is:

more users -> more cache/local retrieval -> more shared infrastructure -> only proportionally more deep model calls.

Do not optimize for the smallest model at any cost. Optimize for the cheapest architecture that passes the required quality, multilingual, safety and latency gates.
