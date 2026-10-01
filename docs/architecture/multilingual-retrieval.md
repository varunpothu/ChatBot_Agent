# Native multilingual retrieval

CoachAI now supports native cross-language retrieval as an optional local layer.

The model used by the adapter is intfloat/multilingual-e5-small. Its current model card lists 94 languages and a 384-dimensional hidden size. The repository includes a main safetensors weight file of about 471 MB. citeturn272176search0turn272176search2turn272176search7

## Modes

Set MULTILINGUAL_EMBEDDING_PROVIDER=auto:

- If sentence-transformers is installed, CoachAI uses the local multilingual embedding provider.
- Otherwise it falls back safely to the deterministic test embedding provider.

Set MULTILINGUAL_EMBEDDING_PROVIDER=hash to force the lightweight offline test path.

Set MULTILINGUAL_EMBEDDING_PROVIDER=local_e5 to require native multilingual retrieval and fail fast if the optional dependency is missing.

Install the optional dependency with:

    pip install -e ".[multilingual]"

## Runtime path

Hindi/Telugu/Tamil/etc. question
-> direct multilingual query embedding
-> English source chunks
-> hybrid ranking
-> adaptive evidence
-> verification
-> answer in requested language

This removes the translation round-trip from retrieval when native multilingual embeddings are enabled.

## Cost trade-off

The model creates a fixed local CPU/RAM cost and a one-time model download, but it avoids per-question translation calls for retrieval.

Before production, benchmark the real corpus using Recall@K, NDCG/MRR, p50/p95 latency, CPU/RAM, translation calls avoided and total cost per 1,000 questions.

The repository includes a small benchmark command:

    coachai-multilingual-benchmark --provider local_e5

The benchmark is intentionally not treated as a production quality proof. Replace its sample cases with real coaching-centre multilingual golden questions.
