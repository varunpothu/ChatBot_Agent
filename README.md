# CoachAI

Production-oriented RAG coaching-centre assistant designed around four goals:

**human conversation, very fast answers, very low inference cost, and evidence-first safety.**

## Core design

- Fast path first: simple factual questions are answered deterministically from approved evidence with no cloud LLM call.
- Deep path only when needed: comparison, explanation and multi-part questions may use one small cloud-model call.
- Adaptive evidence: strong matches may use one chunk, weaker matches use two or three.
- Tiny structured memory: follow-up questions retain only the previous query and intent, not the full transcript.
- Response cache: repeated questions reuse verified answers until knowledge generation changes.
- Low token budgets: input, evidence and output are all capped.
- Cost firewall: per-client rate limiting and a daily cloud-call budget prevent accidental spend spikes.
- Multilingual conversation: selected or script-detected language is carried through text, retrieval, verification, translation, STT and TTS.
- Translation after verification: non-English responses are translated only after the source-language answer has passed grounding checks.
- Voice is a delivery layer: browser speech input/output is the default low-cost voice path; Polly is optional and cached.
- Governed knowledge: uploads enter PENDING_REVIEW and become ACTIVE only after approval. Versions, hashes and audits are tracked.
- Human escalation: unsupported, security-sensitive or policy-sensitive cases can enter a human review queue.

## Supported knowledge formats

PDF, DOCX, PPTX, XLS/XLSX, CSV, TXT, Markdown, HTML, JSON and image uploads are supported. Image/scanned-document OCR uses the AWS Textract boundary when enabled in async ingestion.

## Multilingual support

The UI supports English, Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Punjabi, Urdu, Kannada, Malayalam, Spanish, French, German, Arabic, Italian, Portuguese, Japanese and Simplified Chinese.

Set TRANSLATION_PROVIDER=aws_translate for multilingual retrieval against an English knowledge base. Browser speech uses the selected locale. Cloud voice availability remains provider-dependent.

## Production target

S3 + SQS + Textract + PostgreSQL/pgvector + Redis/ElastiCache + Bedrock + Transcribe + Polly + ECS/Fargate + CloudWatch + Secrets Manager + IAM.

### Runtime modes

The same API can run in a zero-infrastructure local mode or switch to shared production services through environment variables.

- `DATABASE_URL` enables durable PostgreSQL state for documents, knowledge generation, audits and human-review items.
- `REDIS_URL` enables a shared response/translation cache and an atomic distributed sliding-window request limiter.
- `INGESTION_MODE=aws_async` moves document processing out of the request path: upload to S3, publish to SQS, then parse/chunk in the worker.
- `INGESTION_MODE=inline` keeps the current local development path.

The API does not require PostgreSQL or Redis for a local demo. Production service selection is explicit rather than silently falling back.

## Cost/latency principles

The system intentionally avoids multi-agent LLM loops for ordinary questions. Agents are used as explicit deterministic stages: routing, retrieval, evidence selection, answer generation only when needed, verification, translation and escalation.

For AWS, Bedrock prompt caching and intelligent prompt routing can provide additional optimization for supported models, but CoachAI's own deterministic fast/deep gate runs first so simple questions do not need model inference.

For embeddings, the production schema keeps a 512-dimensional pgvector column so managed embedding workers can write durable vectors without recomputing the full corpus on each API restart. The current multilingual E5 path remains an explicit optional retrieval profile for cross-language evaluation.

## Testing

Run the deterministic unit and quality suite:

    pytest -q -m "not integration"
    python -m evaluation.ci_gate
    python -m compileall agents rag knowledge monitoring governance evaluation ai_controls voice storage infra workers apps

Run the real service integration suite when PostgreSQL/pgvector and Redis are available:

    pytest -m integration -q

Build the distribution smoke test with:

    python -m build

The complete test matrix and release evidence requirements are documented in `docs/testing/TESTING.md` and `docs/release/RELEASE-CHECKLIST.md`.

## Run locally

Create a virtual environment, install the package and start FastAPI:

    pip install -e .
    uvicorn apps.api.main:app --reload

Set ADMIN_API_KEY before using the operations dashboard. Keep TTS_MODE=browser for the lowest-cost local demo. Start with inline ingestion, then add DATABASE_URL and REDIS_URL for shared runtime state. AWS async ingestion additionally requires DOCUMENT_S3_BUCKET and DOCUMENT_INGESTION_QUEUE_URL. Non-English retrieval can use the native multilingual embedding profile or the AWS Translate bridge.

## End-to-end flow

Student text/voice -> guardrails -> language selection/detection -> routing -> optional translation for retrieval -> hybrid retrieval -> adaptive evidence -> fast extraction OR one cloud generation -> claim verification -> optional translation -> citations -> optional voice -> monitoring.

The goal is not zero hallucinations. The goal is a system that refuses to invent when evidence is missing and makes every answer traceable to approved knowledge.
