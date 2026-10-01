# AI Evaluation Matrix

| Area | Metric | Gate |
|---|---|---:|
| Retrieval | Recall@K | >= 0.80 |
| Retrieval | Term/context coverage | >= 0.85 |
| Grounding | Verification failures | 0 |
| Citations | Citation accuracy | >= 0.90 |
| Safety | Critical injection tests | 100% blocked |
| Abstention | Unsupported-question handling | Evaluated against golden set |
| Performance | Average latency | <= 3000ms |
| Operations | Error rate | Monitored |
| Governance | Model/prompt version present | 100% |
| Traceability | Answer has source metadata | 100% grounded answers |

Thresholds are engineering defaults for this portfolio project and should be calibrated with real coaching-centre data before production.
