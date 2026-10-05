resource "aws_cloudwatch_metric_alarm" "api_cpu" {
  alarm_name          = "${var.project_name}-api-high-cpu"
  alarm_description   = "CoachAI API average CPU is high."
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 85
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
}
