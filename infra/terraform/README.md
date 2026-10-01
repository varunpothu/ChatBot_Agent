# CoachAI Terraform

This is the infrastructure-as-code reference stack for the production CoachAI architecture.

## Provisions

- VPC with public application subnets and private data subnets
- Application Load Balancer
- ECS/Fargate API service
- ECS/Fargate SQS ingestion worker
- RDS PostgreSQL for durable state
- ElastiCache Redis with TLS and authentication
- S3 document bucket with public-access blocking and versioning
- SQS ingestion queue and dead-letter queue
- ECR image repository with immutable tags and scan-on-push
- CloudWatch log groups
- Secrets Manager database, Redis and admin secrets
- IAM task and execution roles

Fargate task definitions support explicit CPU, memory, networking, logging and IAM settings; this stack uses the AWS Logs driver for CloudWatch. citeturn579688search0turn579688search4

RDS/Aurora PostgreSQL supports pgvector and HNSW indexing. The application SQL bootstrap enables the `vector` extension after the database is created. citeturn982582search1turn982582search4

Redis in-transit encryption is enabled. citeturn579688search1turn579688search6

## Security requirements before public exposure

The generated ALB supports HTTP and optional HTTPS. Supply `certificate_arn` before internet production use. The application task defaults to `AUTH_MODE=api_gateway`; deploy it behind a trusted identity-aware ingress that injects the headers documented in `docs/security/AUTH.md`.

Do not open PostgreSQL or Redis to the internet. Their security groups only allow the application security group.

## Cost posture

Defaults are deliberately small: one API task, one ingestion worker, one DB instance and one Redis node. These are starting points for load testing, not universal production sizing.

## Usage

    cd infra/terraform
    terraform init
    terraform plan -var='app_image=<ECR_IMAGE_URI>'
    terraform apply -var='app_image=<ECR_IMAGE_URI>'

Review the variables and identity architecture before applying. Enable deletion protection and backup/restore procedures appropriate to the real environment.