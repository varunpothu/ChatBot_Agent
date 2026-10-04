# CoachAI Release Checklist

## Automated evidence

- [ ] Unit suite passes with `pytest -q -m "not integration"` on the current release commit.
- [ ] Deterministic quality gate passes with `python -m evaluation.ci_gate` on the current release commit.
- [ ] PostgreSQL/Redis integration suite passes with `pytest -m integration -q` on the current release commit.
- [ ] Compile/static smoke test passes on the current release commit.
- [ ] Package build passes on the current release commit.

## AWS evidence

- [ ] S3/SQS ingestion smoke test completed.
- [ ] Textract image and multi-page PDF OCR smoke test completed.
- [ ] Bedrock embedding dimension check completed.
- [ ] Grounded answer/citation smoke test completed.
- [ ] Transcribe streaming tested with the deployed audio format and sample rate.
- [ ] Polly voice path tested, including unsupported-language fallback.

## Security and operations

- [ ] API is behind the production identity/authentication layer.
- [ ] IAM roles are least-privilege and secrets are not stored in Git.
- [ ] Redis is treated as cache/safety infrastructure, not the source of truth.
- [ ] PostgreSQL backups and restore procedure have been verified.
- [ ] CloudWatch dashboards/alarms and incident runbooks are configured.
- [ ] Rate limits and cloud-call budget have been set for expected traffic.

## Release record

Record the commit SHA, CI workflow URL, test totals, skipped tests, quality-gate output, production smoke-test date, representative latency, estimated cost per 1,000 chats, and any known limitations.

The automated gates above are verified by GitHub Actions. Keep the AWS, identity and operational checks unchecked until they are run in the target account.
## Verified automated gates

AI Quality Gate: https://github.com/varunpothu/ChatBot_Agent/actions/runs/36913480280

Commit: d36c7c5a969bb5c84be5479ea4914c3a65447fb5

Unit/quality, PostgreSQL/Redis integration, Terraform validation and package build all completed successfully.


## Final automated evidence

AI Quality Gate: https://github.com/varunpothu/ChatBot_Agent/actions/runs/36913480280

Commit: d36c7c5a969bb5c84be5479ea4914c3a65447fb5

56 unit tests passed, 4 integration tests passed, Terraform validation passed, package build passed, and the deterministic quality benchmark passed. AWS account-specific smoke tests remain deployment-specific.


## Baseline evidence

The earlier commit d36c7c5a969bb5c84be5479ea4914c3a65447fb5 has documented successful CI evidence. Because the repository has changed since then, the automated gates above should be re-checked against the final release SHA.
