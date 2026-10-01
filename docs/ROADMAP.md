# CoachAI Platform Roadmap

## Completed foundations
- Multi-format document parsing
- Hybrid retrieval
- Evidence-first answering
- Citation model
- Prompt-injection guard
- Runtime KPI monitoring
- Failure alerts
- Retrieval evaluation
- AI governance controls
- AI assurance checks
- AWS Polly voice adapter
- Operations dashboard
- CI quality workflow

## Production milestones

### M1 — Knowledge platform
- S3 document storage
- Textract OCR
- PostgreSQL + pgvector persistence
- asynchronous ingestion with SQS
- document approval workflow

### M2 — AI evaluation
- golden question dataset
- retrieval Recall@K / MRR / NDCG
- faithfulness and citation evaluation
- adversarial prompt-injection suite
- regression reports attached to pull requests

### M3 — AI assurance
- model registry
- prompt registry
- release gates
- risk register
- control evidence
- human review queue
- audit trail

### M4 — Voice
- speech-to-text adapter
- Amazon Polly neural TTS
- selectable voices and languages
- latency and transcription-quality metrics

### M5 — Production operations
- CloudWatch dashboards
- alarms
- cost monitoring
- SLOs
- incident runbooks
- rollback/version pinning

### M6 — FDE demonstration
The final demo should show:
1. Admin uploads a PDF/DOCX/spreadsheet.
2. System processes and indexes it.
3. Admin approves the version.
4. Student asks by typing or voice.
5. RAG retrieves evidence.
6. Answer displays citations.
7. Voice reads the answer using selected voice.
8. Unsupported question triggers abstention.
9. Security attack is blocked.
10. KPI dashboard changes in real time.
11. Assurance dashboard shows release/control status.
