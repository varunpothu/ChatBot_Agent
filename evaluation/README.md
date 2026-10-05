# Evaluation

CoachAI will use a versioned golden dataset to measure retrieval and answer quality.

Planned metrics:

- Recall@K, MRR, NDCG
- Citation correctness
- Claim-level grounding rate
- Unsupported claim rate
- Abstention accuracy
- Prompt-injection resistance
- End-to-end latency

Thresholds should be tuned against the evaluation dataset rather than treated as universal guarantees.


## Cost and latency benchmark

Run the deterministic benchmark without calling Bedrock, translation APIs, STT, or TTS:

```bash
python -m evaluation.cost_latency --iterations 20
```

The benchmark reports:

- fast versus deep routing
- LLM-call rate
- response-cache hit rate
- estimated input/output tokens
- multilingual translation characters
- configurable estimated cost per request and per 1,000 requests
- local routing/cache p50 and p95 latency

Set these environment variables when you want planning estimates for a specific provider pricing model:

```text
BENCHMARK_INPUT_COST_PER_1K=...
BENCHMARK_OUTPUT_COST_PER_1K=...
BENCHMARK_TRANSLATION_COST_PER_1K_CHARS=...
```

These values are intentionally not hard-coded. Token counts are planning estimates and local latency is not production AWS latency.

For production evidence, run a separate live AWS load test and record actual provider usage and end-to-end p50/p95 latency.
