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
