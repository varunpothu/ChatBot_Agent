# CoachAI Release Checklist

## Automated evidence

- [x] Unit suite passes with `pytest -q -m "not integration"`.
- [x] Deterministic quality gate passes with `python -m evaluation.ci_gate`.
- [x] PostgreSQL/Redis integration suite passes with `pytest -m integration -q`.
- [x] Compile/static smoke test passes.
- [x] Package build passes.

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

AI Quality Gate: https://github.com/varunpothu/ChatBot_Agent/actions/runs/36912758911

Commit: b9b2691df45d882e151daf584aafda3430bef72e

Unit/quality, PostgreSQL/Redis integration, Terraform validation and package build all completed successfully.
