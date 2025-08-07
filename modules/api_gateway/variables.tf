variable "api_name" {
  description = "The name of the API Gateway REST API"
  type        = string
}

variable "api_description" {
  description = "A description of the API Gateway"
  type        = string
  default     = "API Gateway for Lambda integrations"
}

variable "api_stage_name" {
  description = "Stage name for API Gateway deployment"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region where resources are deployed"
  type        = string
  default     = "ap-south-1"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "register_user_lambda_arn" {
  description = "ARN of the register_user Lambda function"
  type        = string
}

variable "change_password_lambda_arn" {
  description = "ARN of the change_password Lambda function"
  type        = string
}

variable "delete_user_lambda_arn" {
  description = "ARN of the delete_user Lambda function"
  type        = string
}

variable "login_lambda_arn" {
  description = "ARN of the login Lambda function"
  type        = string
}

variable "insert_diet_plan_lambda_arn" {
  description = "ARN of the insert_diet_plan Lambda function"
  type        = string
}
