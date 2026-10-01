# Production-grade CoachAI architecture

CoachAI is designed as a real AI application rather than a chatbot demo.

## Core principle

**No evidence = no answer.**

The language model is not treated as the source of truth. Approved coaching-centre documents are the source of truth.

## Runtime

1. Student starts a text or voice conversation.
2. API authenticates the request and applies rate limits.
3. Conversation state is loaded.
4. Router identifies the request type.
5. Retrieval agent performs metadata-filtered hybrid search.
6. Reranker orders candidate evidence.
7. Evidence selector removes weak or conflicting material.
8. Answer model drafts only from selected evidence.
9. Claim verifier checks the draft against evidence.
10. Citation builder attaches source/version/page metadata.
11. Failed verification causes abstention or human escalation.
12. Approved answer is returned.
13. TTS speaks the answer using the student's selected voice.
14. Metrics and audit events are recorded.

## Voice

Voice is a delivery preference, not a trust boundary.

Users can select:
- male or female voice
- language/accent
- conversational style
- automatic speech.

Production voice architecture:

Microphone -> STT -> Conversation Orchestrator -> RAG -> Verification -> TTS -> Audio

The STT and TTS providers are adapters. Local development can use browser speech recognition, while production can use managed AWS services.

## Knowledge lifecycle

UPLOAD -> VALIDATE -> EXTRACT/OCR -> CHUNK -> EMBED -> PENDING_REVIEW -> APPROVED -> ACTIVE -> ARCHIVED

Only ACTIVE documents can be used for student answers.

Every document version should retain:
- content hash
- source
- owner
- effective dates
- approval state
- version
- processing status.

## AI assurance

A release must not proceed when configured quality gates fail.

Examples:
- retrieval recall below target
- citation accuracy below target
- grounding verification failures
- critical prompt-injection tests failing
- latency above SLO
- missing model or prompt version
- missing source metadata.

## Human oversight

The system escalates when:
- evidence is absent
- evidence conflicts
- verification fails
- a request requires staff intervention
- security controls detect suspicious input.

Human review events are auditable and visible on the operations dashboard.

## Production deployment

Target AWS architecture:

CloudFront/API Gateway -> ECS/Fargate -> PostgreSQL/pgvector

Supporting services:
- S3 for source documents
- SQS for asynchronous ingestion
- Textract for scanned documents
- Bedrock for model/embedding providers
- Transcribe for speech recognition
- Polly for speech synthesis
- CloudWatch for logs, metrics and alarms
- Secrets Manager for credentials
- IAM for least-privilege access.

Local development remains possible without AWS by using the local adapters.

## Engineering standard

The project should prefer explicit interfaces, deterministic tests, observable failures, versioned artifacts and reversible deployments over hidden magic.

A provider integration is considered production-ready only when it has:
- configuration
- authentication
- timeout handling
- retries where safe
- structured errors
- metrics
- tests
- documented failure behaviour
- version pinning.