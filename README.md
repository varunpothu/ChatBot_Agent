# CoachAI

Production-oriented RAG coaching-centre assistant designed around four goals:

**human conversation, very fast answers, very low inference cost, and evidence-first safety.**

## Core design

- **Fast path first:** simple factual questions are answered deterministically from approved evidence with no cloud LLM call.
- **Deep path only when needed:** comparison, explanation and multi-part questions may use one small cloud-model call.
- **Adaptive evidence:** strong matches may use one chunk, weaker matches use two or three.
- **Tiny structured memory:** follow-up questions retain only the previous query and intent, not the full transcript.
- **Response cache:** repeated questions reuse verified answers until the knowledge generation changes.
- **Low token budgets:** input, evidence and output are all capped.
- **Cost firewall:** per-client rate limiting and a daily cloud-call budget prevent accidental spend spikes.
- **Voice is a delivery layer:** browser speech input/output is the default free path; Polly is optional and cached.
- **Governed knowledge:** uploads enter PENDING_REVIEW and become ACTIVE only after approval. Versions, hashes and audits are tracked.
- **Human escalation:** unsupported, security-sensitive or policy-sensitive cases can enter a human review queue.

## Supported knowledge formats

PDF, DOCX, PPTX, XLS/XLSX, CSV, TXT, Markdown, HTML and JSON are supported by the local ingestion pipeline. Image/OCR processing is isolated behind a provider boundary for production AWS integration.

## Production target

S3 + SQS + Textract + PostgreSQL/pgvector + Bedrock + Transcribe + Polly + ECS/Fargate + CloudWatch + Secrets Manager + IAM.

## Cost/latency principles

The system intentionally avoids multi-agent LLM loops for ordinary questions. Agents are used as explicit deterministic stages: routing, retrieval, evidence selection, answer generation only when needed, verification and escalation.

For AWS, Bedrock supports intelligent prompt routing for quality/cost optimization and prompt caching for supported models. The project keeps static prompt content stable and separates dynamic user input so those provider features can be adopted in production.

## Run locally

Create a virtual environment, install the package and start FastAPI:

    pip install -e .
    uvicorn apps.api.main:app --reload

Set ADMIN_API_KEY before using the operations dashboard. Keep TTS_MODE=browser and LLM_PROVIDER=local for the lowest-cost local demo.

## End-to-end flow

Student text/voice -> guardrails -> routing -> hybrid retrieval -> adaptive evidence -> fast extraction OR one cloud generation -> claim verification -> citations -> optional voice -> monitoring.

The goal is not zero hallucinations. The goal is a system that refuses to invent when evidence is missing and makes every answer traceable to approved knowledge.
