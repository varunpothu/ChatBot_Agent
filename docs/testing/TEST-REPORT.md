# CoachAI Test Report

## Scope

This report covers the automated tests and production-test scaffolding added to the CoachAI repository.

## Automated coverage added

- API configuration, language capability and no-knowledge abstention contracts.
- Production authentication boundary and protected document upload.
- Prompt-injection detection.
- Grounding verification including unsupported-fact rejection.
- Managed embedding cache reuse.
- Textract line-to-page mapping.
- Transcribe missing-SDK failure contract.
- Multilingual/script detection.
- Cost/routing/budget controls.
- Document lifecycle/version activation.
- PostgreSQL/pgvector persistence and retrieval integration.
- Redis shared cache and distributed rate limiting integration.
- Deterministic retrieval/grounding release gate.
- Python compile/static smoke test.
- Python package build smoke test.

## CI jobs

`unit-quality`: unit tests, deterministic AI quality gate and compile/static checks.

`integration`: PostgreSQL with pgvector plus Redis, then integration tests.

`package-smoke`: Python distribution build.

## Execution status

### Previously verified baseline

- A real GitHub Actions AI Quality Gate completed successfully for commit d36c7c5a969bb5c84be5479ea4914c3a65447fb5.
- Unit/quality job: passed, including deterministic retrieval/grounding gate, broader quality benchmark and compile/static checks.
- PostgreSQL/Redis integration job: passed against GitHub-hosted PostgreSQL with pgvector and Redis service containers.
- Terraform validation job: passed.
- Package smoke-test job: passed.
- The verified workflow run is https://github.com/varunpothu/ChatBot_Agent/actions/runs/36913480280.

### Current-head verification status

- The current head contains additional infrastructure, authentication, conversation-persistence and test changes after the verified baseline commit.
- Those newer changes require a fresh GitHub Actions run before the current head can be marked verified.

### Not executed here

- Local pytest execution could not be performed because the environment could not resolve github.com and the repository could not be cloned into the local runtime.
- A real PostgreSQL/pgvector and Redis integration environment was not available in this runtime.
- No AWS account or AWS credentials are available here, so S3, SQS, Textract, Bedrock, Transcribe and Polly smoke tests were not executed.
- AWS production smoke tests remain environment-specific and are not represented by the GitHub-hosted test run.

## Required next verification

The automated CI evidence is now recorded above. The remaining deployment-specific verification is the real AWS smoke-test checklist in `docs/testing/TESTING.md`.

## Important interpretation

Passing unit tests demonstrates that the deterministic software contracts behave as expected under those tests. It does not prove production retrieval quality, AWS service availability, identity configuration, or absence of hallucinations across arbitrary student questions.

## Verified CI result

The successful unit job reported 55 passed, 1 skipped and 4 deselected before the deterministic quality and benchmark steps completed successfully. The PostgreSQL/Redis integration job also completed successfully.

Workflow: https://github.com/varunpothu/ChatBot_Agent/actions/runs/36913480280
Commit: d36c7c5a969bb5c84be5479ea4914c3a65447fb5


## Final automated evidence

AI Quality Gate: https://github.com/varunpothu/ChatBot_Agent/actions/runs/36913480280

Commit: d36c7c5a969bb5c84be5479ea4914c3a65447fb5

Unit/quality: 56 passed, 1 skipped, 4 deselected; deterministic quality gate passed; benchmark passed; compile passed. PostgreSQL/Redis integration: 4 passed, 57 deselected. Terraform validation passed. Package build passed.
