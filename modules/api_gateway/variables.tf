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
variable "user_pool_arn" {
  description = "ARN of the Cognito user pool"
  type        = string
}
variable "push_data_to_rds_lambda_arn" { type = string }
variable "pull_data_from_rds_lambda_arn" { type = string }
variable "push_onboarding_question_lambda_arn" {
  type        = string
  description = "ARN of the Lambda function for pushing onboarding questions"
}

variable "pull_onboarding_questions_lambda_arn" {
  type        = string
  description = "ARN of the Lambda function for pulling onboarding questions"
}
variable "chatgpt_integration_lambda_arn" { type = string }
#variable "openai_api_key" {
#  description = "OpenAI API Key for ChatGPT"
#  type        = string
#  sensitive   = true
#}

variable "openai_model" {
  description = "ChatGPT model to be used"
  type        = string
  default     = "gpt-4o-mini"
}