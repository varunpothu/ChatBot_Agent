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

### Verified in this environment

- GitHub repository files were inspected after each major implementation change.
- A real GitHub Actions run was observed for the repository; the initial production-quality run failed on setuptools package discovery and Terraform formatting.
- Those CI failures were used to drive the package-discovery and Terraform-formatting fixes now committed.
- The latest GitHub Actions runs after those fixes are being used as the next verification signal; a passing result is not claimed until the latest run concludes successfully.

### Not executed here

- Local pytest execution could not be performed because the environment could not resolve github.com and the repository could not be cloned into the local runtime.
- A real PostgreSQL/pgvector and Redis integration environment was not available in this runtime.
- No AWS account or AWS credentials are available here, so S3, SQS, Textract, Bedrock, Transcribe and Polly smoke tests were not executed.
- The latest CI run status is tracked from GitHub Actions. A passing result is not claimed unless the complete workflow concludes successfully.

## Required next verification

Run the CI workflow on the repository and record its run URL. Then perform the AWS smoke-test checklist in `docs/testing/TESTING.md` and attach the results to the release record in `docs/release/RELEASE-CHECKLIST.md`.

## Important interpretation

Passing unit tests demonstrates that the deterministic software contracts behave as expected under those tests. It does not prove production retrieval quality, AWS service availability, identity configuration, or absence of hallucinations across arbitrary student questions.