# CoachAI Deployment

## Deployment sequence

1. Run the AI quality/unit gate and Terraform validation.
2. Build the immutable Docker image tagged with the Git commit SHA.
3. Push the image to the ECR repository created by Terraform.
4. Authenticate to AWS using GitHub Actions OIDC and an assumable AWS role.
5. Run Terraform plan and review the plan.
6. Apply the exact planned infrastructure/image version.
7. Run the explicit database initialization/migration step.
8. Seed, approve and activate model/prompt governance records.
9. Read Terraform outputs and perform the production smoke tests.

GitHub Actions OIDC avoids storing long-lived AWS access keys in repository secrets. The workflow only needs `AWS_ROLE_ARN` as an environment-protected secret and an AWS trust policy that permits the repository/workflow to assume the role.

## Environment protection

Use a GitHub `production` environment with required reviewers before the deployment workflow can apply Terraform.

## Image strategy

ECR is configured for immutable image tags. Each deployment uses the Git commit SHA as the image tag, so a release can always be traced back to a source commit.

## Database bootstrap

The API task uses `POSTGRES_AUTO_INIT_SCHEMA=false`. Initialize the schema explicitly with the packaged `coachai-db-init` command as a deployment step. This keeps schema changes out of application startup and request traffic.

## HTTPS and identity

Before public exposure, provide an ACM certificate. The deployed API uses `AUTH_MODE=oidc` and validates bearer JWTs directly against the configured OIDC issuer and audience. The ALB is the transport/load-balancing layer; it is not the trust boundary for user identity.

Set `OIDC_ISSUER_URL` and `OIDC_AUDIENCE` in the protected GitHub production environment. Never expose the service publicly with `AUTH_MODE=development`.

## Conversation retention

Set `CONVERSATION_RETENTION_DAYS` to the approved retention period. Run `coachai-purge-conversations` as a scheduled operational job against the production database. User deletion removes conversation state, stored turns and linked human-review records; audit events are retained as operational records.

## Rollback

Rollback by redeploying the previous immutable ECR image tag and the corresponding Terraform plan. Do not rebuild the image with a moving `latest` tag.