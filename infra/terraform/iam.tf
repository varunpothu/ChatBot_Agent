resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "app_task" {
  name = "${var.project_name}-app-task"

  assume_role_policy = aws_iam_role.ecs_execution.assume_role_policy
}

resource "aws_iam_policy" "app_task" {
  name = "${var.project_name}-app-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.documents.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.ingestion.arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [
          aws_secretsmanager_secret.database_url.arn,
          aws_secretsmanager_secret.redis_url.arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "textract:DetectDocumentText",
          "textract:StartDocumentTextDetection",
          "textract:GetDocumentTextDetection"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "polly:DescribeVoices",
          "polly:SynthesizeSpeech",
          "transcribe:StartStreamTranscription"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "app_task" {
  role   = aws_iam_role.app_task.id
  policy = aws_iam_policy.app_task.policy
}
