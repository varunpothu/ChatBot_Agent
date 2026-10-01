variable "project_name" { type = string default = "coachai" }
variable "aws_region" { type = string default = "eu-west-2" }
variable "vpc_cidr" { type = string default = "10.40.0.0/16" }
variable "public_subnet_cidrs" { type = list(string) default = ["10.40.1.0/24", "10.40.2.0/24"] }
variable "private_subnet_cidrs" { type = list(string) default = ["10.40.11.0/24", "10.40.12.0/24"] }
variable "app_image" { type = string description = "Full ECR image URI for the CoachAI application image." }
variable "api_desired_count" { type = number default = 1 }
variable "worker_desired_count" { type = number default = 1 }
variable "db_instance_class" { type = string default = "db.t4g.micro" }
variable "redis_node_type" { type = string default = "cache.t4g.micro" }
variable "db_name" { type = string default = "coachai" }
variable "bedrock_model_id" { type = string default = "amazon.nova-micro-v1:0" }
variable "bedrock_embedding_model_id" { type = string default = "amazon.titan-embed-text-v2:0" }
variable "auth_mode" { type = string default = "api_gateway" }
variable "certificate_arn" { type = string default = "" description = "ACM certificate ARN for production HTTPS." }

variable "monthly_budget_usd" {
  type        = number
  default     = 50
  description = "Optional monthly AWS spend alert threshold."
}

variable "budget_alert_email" {
  type        = string
  default     = ""
  description = "Optional email for AWS Budget notifications. Leave empty to disable."
}
