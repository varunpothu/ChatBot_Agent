# Native multilingual retrieval

CoachAI supports two retrieval strategies.

## Default development mode

The deterministic hash embedding remains the default so the project can run without downloading model weights.

## Optional local multilingual mode

Set:

    MULTILINGUAL_EMBEDDING_PROVIDER=local_e5

This enables intfloat/multilingual-e5-small, a 384-dimensional multilingual embedding model. The current model card lists 94 languages. It uses query and passage prefixes so a question and an evidence passage can be represented in the same vector space even when the languages differ.

The retrieval path becomes:

student asks in Hindi/Telugu/Tamil
-> multilingual embedding
-> English source chunks
-> hybrid ranking
-> verification
-> answer in requested language

No translation API call is needed for retrieval.

## Cost trade-off

There is a one-time model download and local CPU/RAM cost, but no per-query translation API charge. The production choice should be based on the real corpus' retrieval and latency benchmark.

Translation support remains available as a fallback because the correct production decision should be measured rather than assumed.
