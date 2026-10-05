# AWS deployment smoke test

Run this after the production ECS service is healthy.

## Basic public checks

PowerShell:
```powershell
$env:COACHAI_BASE_URL="https://your-coachai-domain.example"
python scripts/aws_smoke_test.py
```

This checks `/health`, `/config` and `/languages` without creating application data.

## Authenticated end-to-end check

For the OIDC deployment, provide a short-lived access token:

```powershell
$env:COACHAI_BEARER_TOKEN="<short-lived-token>"
python scripts/aws_smoke_test.py
```

The script performs one `/chat` request, records elapsed time, then deletes the generated conversation.

Never commit the token or place it in Terraform, GitHub files, shell history or screenshots.

## Evidence to capture

- ALB URL and HTTPS status
- `/health` response
- ECS desired/running task counts
- CloudWatch API and worker logs
- `/chat` latency
- response cache hit on a repeated question
- Bedrock invocation count, tokens and cost
- SQS queue depth and DLQ depth
- RDS and Redis health
- document lifecycle: upload -> PROCESSING -> PENDING_REVIEW -> ACTIVE

This smoke test is not a load test. Run a separate controlled load test before making capacity or p95 production claims.