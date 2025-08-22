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
  type    = string
  default = "rahul.khandelwal@granimals.com"
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

variable "layers" {
  description = "List of Lambda layer ARNs to attach"
  type        = list(string)
  default     = []
}
variable "user_pool_client_secret" {
  description = "Client secret for Cognito User Pool"
  type        = string
  sensitive   = true
  default     = null
}
variable "environment_variables" {
  type        = map(string)
  description = "Extra environment variables for the Lambda function"
  default     = null
}
variable "push_data_lambda_s3_key" {
  description = "S3 key of the push_data_to_rds Lambda ZIP"
  type        = string
  default     = null
}

variable "pull_data_lambda_s3_key" {
  description = "S3 key of the pull_data_from_rds Lambda ZIP"
  type        = string
  default     = null
}

variable "user_pool_client_id_app" {
  type    = string
  default = null
}

variable "user_pool_client_secret_app" {
  type      = string
  sensitive = true
  default   = null
}

variable "push_onboarding_lambda_s3_key" {
  description = "S3 key for insert onboarding question lambda package"
  type        = string
  default     = null
}

variable "pull_onboarding_lambda_s3_key" {
  description = "S3 key for get onboarding questions lambda package"
  type        = string
  default     = null
}

variable "openai_secret_arn" {
  description = "Secrets Manager ARN containing the OpenAI API key"
  type        = string
  default     = null
}