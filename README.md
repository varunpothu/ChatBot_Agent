# CoachAI RAG

Production-style RAG coaching-centre assistant with grounded text and voice conversations, source citations, multi-agent orchestration, document governance, verification, evaluation, and human escalation.

## Core principle

**No evidence = no answer.** CoachAI answers from approved, authorized documents and abstains when evidence is missing, stale, conflicting, or insufficient.

## Architecture

```text
Student (Text / Voice)
        |
        v
   FastAPI Gateway
        |
        v
   Agent Orchestrator
   |      |       |       |
 Router  Rewrite  Retrieve  Escalate
                   |
             Hybrid Search
              /          \
        Vector / pgvector  BM25
              \          /
                Reranker
                    |
               Evidence Set
                    |
               Answer Agent
                    |
             Claim Verifier
              /           \
          PASS             FAIL
           |                 |
      Citations        Regenerate / Escalate
           |
        Response
           |
      TTS for Voice
```

## Planned capabilities

- Text + voice using the same grounded pipeline
- Hybrid retrieval with semantic + keyword search and reranking
- Multi-agent orchestration with bounded responsibilities
- Claim-level verification and citation validation
- Document versions, effective dates, approval states, and access controls
- Human-in-the-loop escalation
- Evaluation datasets and adversarial tests
- Observability and AWS-ready deployment

## Repository layout

```text
apps/            API and UI
agents/          router, rewrite, retrieval, answer, verification, escalation
rag/             ingestion, chunking, embeddings, retrieval, citations
voice/           speech-to-text and text-to-speech adapters
knowledge/       document models and versioning
security/        auth, access control, prompt-injection controls
evaluation/      golden set and RAG quality tests
tests/           unit, integration, end-to-end tests
infrastructure/  Terraform/AWS
```

## Development status

Phase 1: foundation and controlled orchestration skeleton.

Next: document ingestion, hybrid retrieval, verification, UI, voice, evaluation, and AWS deployment.
