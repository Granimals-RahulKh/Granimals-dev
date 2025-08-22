# terraform/variables.tf

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "push_onboarding_lambda_s3_key" {
  description = "S3 key for insert onboarding question lambda package"
  type        = string
}

variable "pull_onboarding_lambda_s3_key" {
  description = "S3 key for get onboarding questions lambda package"
  type        = string
}


variable "insert_diet_plan_lambda_s3_key" {
  description = "S3 key of the insert_diet_plan Lambda ZIP"
  type        = string
}

variable "register_user_lambda_s3_key" {
  description = "S3 key (file path) for the register_user lambda zip"
  type        = string
}

variable "login_lambda_s3_key" {
  description = "S3 key (file path) for the login lambda zip"
  type        = string
}

variable "change_password_lambda_s3_key" {
  description = "S3 key (file path) for the change_password lambda zip"
  type        = string
}

variable "delete_user_lambda_s3_key" {
  description = "S3 key (file path) for the delete_user lambda zip"
  type        = string
}

variable "lambda_s3_bucket" {
  description = "S3 bucket where all lambda zip files are uploaded"
  type        = string
}

variable "cognito_user_groups" {
  description = "User roles/groups for the app"
  type        = list(string)
  default = [
    "client",
    "admin",
    "physiotherapist",
    "nutritionist",
    "guest_admin",
    "guest_physio",
    "guest_nutrition"
  ]
}

variable "api_name" {
  type        = string
  description = "API Gateway name"
}

variable "api_description" {
  type    = string
  default = "API Gateway for Cognito Lambda functions"
}

variable "api_stage_name" {
  type    = string
  default = "dev"
}

variable "tags" {
  type = map(string)
  default = {
    Environment = "dev"
    Project     = "CognitoAuth"
  }
}


variable "db_host" {}
variable "db_port" {}
variable "db_name" {}

variable "user_pool_id" {
  type    = string
  default = null
}

variable "user_pool_client_id" {
  type    = string
  default = null
}

variable "user_pool_arn" {
  type    = string
  default = null
}

variable "register_function_name" {
  type    = string
  default = null
}

variable "user_groups" {
  type    = list(string)
  default = []
}

variable "from_email" {
  type    = string
  default = "rahul.khandelwal@granimals.com"
}

variable "rds_secret_arn" {
  type    = string
  default = null
}

variable "lambda_layer_arn" {
  description = "ARN of the Lambda layer to attach"
  type        = string
}
variable "user_pool_client_secret" {
  description = "Client secret for Cognito User Pool"
  type        = string
  sensitive   = true
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

variable "chatgpt_integration_lambda_s3_key" {
  type      = string
  sensitive = true
  default   = null
}

variable "openai_secret_arn" {
  type    = string
  default = null
}

variable "environment_variables" {
  description = "Environment variables for Lambda"
  type        = map(string)
  default     = {}
}