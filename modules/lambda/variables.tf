# terraform/lambdas/variables.tf

variable "lambda_s3_bucket" {
  type        = string
  description = "S3 bucket holding Lambda code"
}

variable "user_pool_id" {
  type        = string
  description = "Cognito User Pool ID"
}
variable "lambda_name" {
  description = "Name of the Lambda function"
  type        = string
}

#variable "s3_key" {
#  description = "S3 object key of the Lambda zip file"
#  type        = string
#}
variable "user_pool_arn" {
  type = string
}

variable "user_pool_client_id" {
  type = string
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

#variable "sns_topic_arn" {
#  description = "ARN of the SNS topic for sending user notifications"
#  type        = string
#}

variable "from_email" {
  description = "Verified SES email address used as sender"
  type        = string
  default     = "rahul.khandelwal@granimals.com"
}
