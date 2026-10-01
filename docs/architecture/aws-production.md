# AWS Production Architecture

## Target services

- S3: immutable source documents and processed artifacts
- Textract: OCR and layout extraction for scanned PDFs/images
- RDS PostgreSQL + pgvector: metadata, chunks and vectors
- Bedrock: model abstraction for production generation
- Polly: neural text-to-speech
- ECS/Fargate: API and worker workloads
- SQS: asynchronous ingestion and evaluation jobs
- CloudWatch: logs, metrics and alarms
- Secrets Manager: credentials and API secrets
- IAM: least-privilege service identities

## Production flow

Upload -> S3 -> SQS -> parser/OCR worker -> chunking -> embeddings -> pgvector -> approval -> ACTIVE.

Chat -> API -> authorization -> hybrid retrieval -> reranking -> model -> claim verification -> citations -> response -> monitoring.

A release is blocked when mandatory assurance gates fail.
