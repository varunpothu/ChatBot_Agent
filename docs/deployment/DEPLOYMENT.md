# CoachAI Deployment

## Deployment sequence

1. Run the AI quality/unit gate.
2. Build the immutable Docker image tagged with the Git commit SHA.
3. Push the image to the ECR repository created by Terraform.
4. Authenticate to AWS using GitHub Actions OIDC and an assumable AWS role.
5. Run Terraform plan.
6. Apply the exact planned infrastructure/image version.
7. Read Terraform outputs and perform the production smoke tests.

GitHub Actions OIDC avoids storing long-lived AWS access keys in repository secrets. The workflow only needs `AWS_ROLE_ARN` as an environment-protected secret and an AWS trust policy that permits the repository/workflow to assume the role.

## Environment protection

Use a GitHub `production` environment with required reviewers before the deployment workflow can apply Terraform.

## Image strategy

ECR is configured for immutable image tags. Each deployment uses the Git commit SHA as the image tag, so a release can always be traced back to a source commit.

## Database bootstrap

The API task has `POSTGRES_AUTO_INIT_SCHEMA=true` in the reference stack so the schema exists before ALB health checks. For a mature production environment, move schema changes to a controlled migration task and set this flag to false after the migration workflow is established.

## HTTPS and identity

Before public exposure, provide an ACM certificate and place the service behind the trusted identity layer described in `docs/security/AUTH.md`. The ALB reference supports HTTP-to-HTTPS redirection when `certificate_arn` is supplied.

API Gateway HTTP APIs can validate JWTs using a JWT authorizer. The deployment must also ensure validated identity claims reach the application identity boundary; JWT validation alone does not magically create trusted application headers.

## Rollback

Rollback by redeploying the previous immutable ECR image tag and the corresponding Terraform plan. Do not rebuild the image with a moving `latest` tag.