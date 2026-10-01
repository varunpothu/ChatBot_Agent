# CoachAI AI Change Control

## Purpose

Model and prompt changes are treated as governed production changes. A new version is registered first, evaluated second, approved third, and activated last.

## Prompt workflow

1. Register the new `answer.<style>` prompt version with `coachai-seed-governance` or the governance API.
2. Run `coachai-quality-benchmark` and the broader test suite.
3. Attach the benchmark/run reference to the governance record.
4. An authorized reviewer approves the record.
5. The reviewer activates it. Activation archives the previous active version.
6. Monitor grounding, latency, abstention, cost and human-review signals.
7. Roll back by activating the previously approved version when required.

## Model workflow

Register the exact provider/model ID and configuration. Do not use a floating model name without a registry record when `MODEL_GOVERNANCE_REQUIRED=true`.

Model activation requires an evaluation reference. The same reviewer/approval process applies as for prompts.

## Safety properties

- New records start as `PENDING_REVIEW`.
- Only `ACTIVE` prompt/model versions are eligible for governed runtime selection.
- Prompt content is hashed with SHA-256.
- Model/prompt activation records who approved the change and which evaluation evidence supports it.
- Previous active versions are retained as `ARCHIVED` records for rollback and audit.

## Runtime enforcement

Set:

    PROMPT_GOVERNANCE_REQUIRED=true
    MODEL_GOVERNANCE_REQUIRED=true

when the production database contains the approved active records.

Until those flags are enabled, the built-in prompt/model configuration remains the fallback path. This makes local development simple without weakening the production change-control design.

## Evidence

Store the CI workflow URL, commit SHA, benchmark output, release checklist and production smoke-test results with every promoted model/prompt version.