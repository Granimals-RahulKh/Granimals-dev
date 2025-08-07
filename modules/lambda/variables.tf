# terraform/lambdas/variables.tf

variable "lambda_s3_bucket" {
  type        = string
  description = "S3 bucket holding Lambda code"
}

variable "user_pool_id" {
  type        = string
  description = "Cognito User Pool ID"
  default     = null
}
variable "lambda_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "user_pool_arn" {
  type    = string
  default = null
}

variable "user_pool_client_id" {
  type    = string
  default = null
}
variable "lambda_function_key" {
  type = string
}
variable "handler" {}
variable "runtime" {}
variable "user_groups" {
  type    = list(string)
  default = []
}
variable "api_gateway_arn" {
  description = "The ARN of the API Gateway to integrate with the Lambda function."
  type        = string
}
variable "api_gateway_paths" {
  type    = list(string)
  default = []
}
variable "register_function_name" {
  type        = string
  description = "Lambda function name for register_user (optional)"
  default     = null
}

variable "from_email" {
  type        = string
  default     = "rahul.khandelwal@granimals.com"
}

#variable "sns_topic_arn" {
#  description = "ARN of the SNS topic for sending user notifications"
#  type        = string
#}


variable "rds_secret_arn" {
  description = "Secret ARN for RDS credentials"
  type        = string
  default     = null
}

variable "db_name" {
  default = null
}

variable "db_host" {
  default = null
}

variable "db_port" {
  default = null
}