resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}/api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.project_name}/worker"
  retention_in_days = 14
}

resource "aws_ecs_cluster" "main" {
  name = var.project_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.app_task.arn

  lifecycle {
    precondition {
      condition     = var.auth_mode != "oidc" || (trimspace(var.oidc_issuer_url) != "" && length(var.oidc_audience) > 0)
      error_message = "AUTH_MODE=oidc requires oidc_issuer_url and at least one oidc_audience value."
    }
  }

  container_definitions = jsonencode([{
    name      = "api"
    image     = var.app_image
    essential = true
    command   = ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    environment = [
      { name = "APP_ENV", value = "production" },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "INGESTION_MODE", value = "aws_async" },
      { name = "DOCUMENT_S3_BUCKET", value = aws_s3_bucket.documents.bucket },
      { name = "DOCUMENT_INGESTION_QUEUE_URL", value = aws_sqs_queue.ingestion.id },
      { name = "BEDROCK_MODEL_ID", value = var.bedrock_model_id },
      { name = "BEDROCK_EMBEDDING_MODEL_ID", value = var.bedrock_embedding_model_id },
      { name = "BEDROCK_EMBEDDING_DIMENSIONS", value = "512" },
      { name = "OCR_PROVIDER", value = "textract" },
      { name = "TTS_MODE", value = "browser" },
      { name = "AUTH_MODE", value = var.auth_mode },
      { name = "OIDC_ISSUER_URL", value = var.oidc_issuer_url },
      { name = "OIDC_AUDIENCE", value = join(",", var.oidc_audience) },
      { name = "OIDC_JWKS_URL", value = var.oidc_jwks_url },
      { name = "POSTGRES_AUTO_INIT_SCHEMA", value = "false" }
    ]
    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "REDIS_URL", valueFrom = aws_secretsmanager_secret.redis_url.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.api.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project_name}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.worker_task.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = var.app_image
    essential = true
    command   = ["coachai-ingestion-worker"]
    environment = [
      { name = "APP_ENV", value = "production" },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "DOCUMENT_INGESTION_QUEUE_URL", value = aws_sqs_queue.ingestion.id },
      { name = "BEDROCK_EMBEDDING_MODEL_ID", value = var.bedrock_embedding_model_id },
      { name = "BEDROCK_EMBEDDING_DIMENSIONS", value = "512" },
      { name = "OCR_PROVIDER", value = "textract" }
    ]
    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "REDIS_URL", valueFrom = aws_secretsmanager_secret.redis_url.arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.worker.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "worker"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    assign_public_ip = true
    security_groups  = [aws_security_group.app.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.http_forward,
    aws_lb_listener.http_redirect,
    aws_lb_listener.https
  ]
}

resource "aws_ecs_service" "worker" {
  name            = "${var.project_name}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    assign_public_ip = true
    security_groups  = [aws_security_group.app.id]
  }
}
