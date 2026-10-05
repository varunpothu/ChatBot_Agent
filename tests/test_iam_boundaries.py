from pathlib import Path


def test_ecs_api_and_worker_have_separate_task_roles():
    terraform = Path("infra/terraform")

    ecs = (terraform / "ecs.tf").read_text(encoding="utf-8")
    iam = (terraform / "iam.tf").read_text(encoding="utf-8")

    assert 'task_role_arn            = aws_iam_role.app_task.arn' in ecs
    assert 'task_role_arn            = aws_iam_role.worker_task.arn' in ecs
    assert 'resource "aws_iam_role" "worker_task"' in iam

    api_policy = iam.split('resource "aws_iam_policy" "app_task"', 1)[1].split(
        'resource "aws_iam_role_policy" "app_task"', 1
    )[0]
    worker_policy = iam.split('resource "aws_iam_policy" "worker_task"', 1)[1]

    assert "textract:" not in api_policy
    assert "sqs:ReceiveMessage" not in api_policy
    assert "textract:StartDocumentTextDetection" in worker_policy
    assert "sqs:ReceiveMessage" in worker_policy
