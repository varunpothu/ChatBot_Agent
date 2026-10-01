# Retrieval architecture

CoachAI uses two independent signals:

1. Semantic vector similarity for meaning.
2. Keyword matching for exact terms such as course codes, prices, policy names and dates.

The signals are fused before reranking. This is important because pure vector search can miss exact identifiers, while pure keyword search can miss paraphrases.

Production target:
- PostgreSQL + pgvector
- embedding model behind an adapter
- BM25/lexical retrieval
- cross-encoder reranking
- metadata filters for document status, version, effective dates and access level
- citation-preserving evidence objects

The system must evaluate retrieval separately from answer generation.
