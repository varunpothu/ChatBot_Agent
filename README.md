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

PDF, DOCX, PPTX, XLS/XLSX, CSV, TXT, Markdown, HTML and JSON are supported by the local ingestion pipeline. Image/OCR processing is isolated behind a provider boundary for production AWS integration.

## Multilingual support

The UI supports English, Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Punjabi, Urdu, Kannada, Malayalam, Spanish, French, German, Arabic, Italian, Portuguese, Japanese and Simplified Chinese.

Set TRANSLATION_PROVIDER=aws_translate for multilingual retrieval against an English knowledge base. Browser speech uses the selected locale. Cloud voice availability remains provider-dependent.

## Production target

S3 + SQS + Textract + PostgreSQL/pgvector + Bedrock + Transcribe + Polly + ECS/Fargate + CloudWatch + Secrets Manager + IAM.

## Cost/latency principles

The system intentionally avoids multi-agent LLM loops for ordinary questions. Agents are used as explicit deterministic stages: routing, retrieval, evidence selection, answer generation only when needed, verification, translation and escalation.

For AWS, Bedrock prompt caching and intelligent prompt routing can provide additional optimization for supported models, but CoachAI's own deterministic fast/deep gate runs first so simple questions do not need model inference.

## Run locally

Create a virtual environment, install the package and start FastAPI:

    pip install -e .
    uvicorn apps.api.main:app --reload

Set ADMIN_API_KEY before using the operations dashboard. Keep TTS_MODE=browser and LLM_PROVIDER=local for the lowest-cost local demo. Non-English retrieval requires a configured translation provider unless the production vector layer is replaced with a multilingual embedding strategy.

## End-to-end flow

Student text/voice -> guardrails -> language selection/detection -> routing -> optional translation for retrieval -> hybrid retrieval -> adaptive evidence -> fast extraction OR one cloud generation -> claim verification -> optional translation -> citations -> optional voice -> monitoring.

The goal is not zero hallucinations. The goal is a system that refuses to invent when evidence is missing and makes every answer traceable to approved knowledge.
