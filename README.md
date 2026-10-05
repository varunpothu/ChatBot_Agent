# CoachAI

Production-oriented RAG coaching-centre assistant designed around four goals:

**human conversation, very fast answers, very low inference cost, and evidence-first safety.**

## Core design

- Fast path first: simple factual questions are answered deterministically from approved evidence with no cloud LLM call.
- Deep path only when needed: comparison, explanation and multi-part questions may use one small cloud-model call.
- Adaptive evidence: strong matches may use one chunk, weaker matches use two or three.
- Tiny structured memory: follow-up questions retain only the previous query and intent, not the full transcript.
- Conversation privacy: authenticated users own their durable conversations, can delete them, and expired conversations can be purged by retention policy.
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
- `CONVERSATION_RETENTION_DAYS` controls durable conversation retention. Run `python scripts/purge_conversations.py` on the configured schedule.

The API does not require PostgreSQL or Redis for a local demo. Production service selection is explicit rather than silently falling back.

## Cost/latency principles

The system intentionally avoids multi-agent LLM loops for ordinary questions. Agents are used as explicit deterministic stages: routing, retrieval, evidence selection, answer generation only when needed, verification, translation and escalation.

For AWS, Bedrock prompt caching and intelligent prompt routing can provide additional optimization for supported models, but CoachAI's own deterministic fast/deep gate runs first so simple questions do not need model inference.

For embeddings, the production schema keeps a 512-dimensional pgvector column so managed embedding workers can write durable vectors without recomputing the full corpus on each API restart. The current multilingual E5 path remains an explicit optional retrieval profile for cross-language evaluation. Run `python -m evaluation.multilingual_benchmark --provider local_e5` to measure Recall@1, Recall@K, MRR, NDCG@K and p50/p95 retrieval latency.

## Cost and latency evaluation

CoachAI includes a deterministic benchmark that exercises routing, response-cache behaviour, multilingual requests, human escalation, token estimates and configurable cost assumptions without making paid model calls.

```bash
python -m evaluation.cost_latency --iterations 20
```

Use `BENCHMARK_INPUT_COST_PER_1K`, `BENCHMARK_OUTPUT_COST_PER_1K`, and `BENCHMARK_TRANSLATION_COST_PER_1K_CHARS` when producing planning estimates for a chosen provider. The benchmark explicitly labels its token counts as estimates and its latency as local routing/cache overhead, not production AWS latency.

## Testing

Run the deterministic unit and quality suite:

    pytest -q -m "not integration"
    python -m evaluation.ci_gate
    python -m compileall agents rag knowledge monitoring governance evaluation ai_controls voice storage infra workers apps

Run the real service integration suite when PostgreSQL/pgvector and Redis are available:

    pytest -m integration -q

Build the distribution smoke test with:

    python -m build

For retention cleanup, configure `DATABASE_URL` and optionally `CONVERSATION_RETENTION_DAYS`, then run:

    python scripts/purge_conversations.py

The complete test matrix and release evidence requirements are documented in `docs/testing/TESTING.md` and `docs/release/RELEASE-CHECKLIST.md`.

## Production deployment

The repository includes a Terraform reference stack under `infra/terraform` and a manual OIDC-based GitHub Actions deployment workflow in `.github/workflows/deploy.yml`.

Typical flow:

    pytest -q -m "not integration"
    python -m evaluation.ci_gate
    python -m evaluation.benchmark
    cd infra/terraform
    terraform init
    terraform plan -var='app_image=<ECR_IMAGE_URI>'

The production workflow builds an immutable commit-SHA image, pushes it to ECR and applies the reviewed Terraform plan. GitHub recommends constraining the AWS OIDC trust policy with the repository/workflow subject and using a protected environment for deployments. citeturn832579search0turn832579search2

## AI governance

Model and prompt versions can be persisted in PostgreSQL. New records start in `PENDING_REVIEW`; activation requires an evaluation reference and archives the previous active version.

Seed the initial records with:

    coachai-db-init
    python -m scripts.seed_governance

Then review and activate the records through the admin governance API before enabling:

    PROMPT_GOVERNANCE_REQUIRED=true
    MODEL_GOVERNANCE_REQUIRED=true

See `docs/governance/AI-CHANGE-CONTROL.md`.

## Operations

Terraform provisions CloudWatch alarms for ALB errors/latency, unhealthy targets, ingestion backlog/DLQ, RDS CPU and Redis CPU, plus an operations dashboard. ECR retains a bounded number of deployment images and an optional AWS monthly budget can be enabled.

## Run locally

Create a virtual environment, install the package and start FastAPI:

    pip install -e .
    uvicorn apps.api.main:app --reload

Set ADMIN_API_KEY before using the operations dashboard. Keep TTS_MODE=browser for the lowest-cost local demo. Start with inline ingestion, then add DATABASE_URL and REDIS_URL for shared runtime state. AWS async ingestion additionally requires DOCUMENT_S3_BUCKET and DOCUMENT_INGESTION_QUEUE_URL. Non-English retrieval can use the native multilingual embedding profile or the AWS Translate bridge.

## End-to-end flow

Student text/voice -> guardrails -> language selection/detection -> routing -> optional translation for retrieval -> hybrid retrieval -> adaptive evidence -> fast extraction OR one cloud generation -> claim verification -> optional translation -> citations -> optional voice -> monitoring.

The goal is not zero hallucinations. The goal is a system that refuses to invent when evidence is missing and makes every answer traceable to approved knowledge.
