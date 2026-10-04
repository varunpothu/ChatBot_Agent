# AI Governance and Change Control

CoachAI treats prompts and models as production artifacts, not untracked configuration.

## Registry lifecycle

New prompt/model versions are registered as `PENDING_REVIEW`.

An evaluator must attach an `evaluation_reference` before activation.

Activation archives the previously active version for the same logical key.

Runtime can enforce the registry with:

`PROMPT_GOVERNANCE_REQUIRED=true`
`MODEL_GOVERNANCE_REQUIRED=true`

When enforcement is enabled, an unapproved or inactive runtime model is not allowed into the deep path. An unapproved prompt cannot be used by the governed prompt provider.

## Prompt integrity

Prompt templates receive a SHA-256 hash. Activation records the reviewer, timestamp and evaluation reference. This makes a deployed prompt traceable to a specific text artifact.

## Model change control

A model record stores provider, model name, version, configuration, owner and evaluation reference. Model activation archives the previous active version.

## Safe rollout

Recommended change sequence:

1. Register new prompt/model version.
2. Run deterministic and representative evaluation.
3. Store the evaluation reference.
4. Approve.
5. Activate.
6. Monitor latency, grounding, abstention and cost.
7. Roll back by reactivating the previous approved version if quality or cost regresses.

## What is intentionally not automated

CoachAI does not automatically promote a model because a benchmark score increased. Human approval remains part of the control plane.