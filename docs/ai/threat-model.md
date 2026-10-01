# AI Threat Model

## Threats

- Prompt injection inside uploaded documents
- Prompt injection from students
- Stale or conflicting policy documents
- Unauthorized document access
- Data exfiltration through retrieval
- Unsupported model claims
- Malicious files
- Voice transcription errors
- Excessive tool permissions

## Controls

Documents are treated as untrusted data. Retrieval is filtered by authorization and document status. Answers require evidence. File types and processing are validated. Sensitive or uncertain cases can be escalated. Model and prompt versions are logged.
