# terraform/main.tf

terraform {
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
provider "aws" {
  region = var.region
}

locals {
  user_groups = [
    "client", "admin", "physiotherapist", "nutritionist",
    "guest_admin", "guest_physio", "guest_nutrition"
  ]
}


module "lambda_register_user" {
  source              = "./modules/lambda"
  lambda_name         = "register_user"
  handler             = "register_user.lambda_handler"
  runtime             = "python3.12"
  user_pool_id        = var.user_pool_id
  user_pool_arn       = var.user_pool_arn
  user_pool_client_id = var.user_pool_client_id
  lambda_s3_bucket    = var.lambda_s3_bucket
  lambda_function_key = var.register_user_lambda_s3_key
  user_groups         = local.user_groups
  api_gateway_arn     = module.api_gateway.api_gateway_arn
  api_gateway_paths   = ["register_user"]
  from_email          = var.from_email
  #  sns_topic_arn       = module.sns.sns_topic_arn
}

module "lambda_delete_user" {
  source              = "./modules/lambda"
  lambda_name         = "delete_user"
  handler             = "delete_user.lambda_handler"
  runtime             = "python3.12"
  user_pool_id        = var.user_pool_id
  user_pool_arn       = var.user_pool_arn
  user_pool_client_id = var.user_pool_client_id
  lambda_s3_bucket    = var.lambda_s3_bucket
  lambda_function_key = var.delete_user_lambda_s3_key
  user_groups         = local.user_groups
  api_gateway_arn     = module.api_gateway.api_gateway_arn
  api_gateway_paths   = ["delete_user"]
  from_email          = var.from_email
  #  sns_topic_arn       = module.sns.sns_topic_arn
}

module "lambda_change_password" {
  source              = "./modules/lambda"
  lambda_name         = "change_password"
  handler             = "change_password.lambda_handler"
  runtime             = "python3.12"
  user_pool_id        = var.user_pool_id
  user_pool_arn       = var.user_pool_arn
  user_pool_client_id = var.user_pool_client_id
  lambda_s3_bucket    = var.lambda_s3_bucket
  lambda_function_key = var.change_password_lambda_s3_key
  user_groups         = local.user_groups
  api_gateway_arn     = module.api_gateway.api_gateway_arn
  api_gateway_paths   = ["change_password"]
  from_email          = var.from_email
  #  sns_topic_arn       = module.sns.sns_topic_arn
}

module "lambda_unknown_user" {
  source                 = "./modules/lambda"
  lambda_name            = "unknown_user"
  handler                = "unknown_user.lambda_handler"
  runtime                = "python3.12"
  user_pool_id           = var.user_pool_id
  user_pool_arn          = var.user_pool_arn
  user_pool_client_id    = var.user_pool_client_id
  register_function_name = module.lambda_register_user.lambda_function_name
  lambda_s3_bucket       = var.lambda_s3_bucket
  lambda_function_key    = var.unknown_user_lambda_s3_key
  user_groups            = local.user_groups
  api_gateway_arn        = module.api_gateway.api_gateway_arn
  api_gateway_paths      = ["unknown_user"]
  from_email             = var.from_email
  #  sns_topic_arn       = module.sns.sns_topic_arn
}

module "lambda_insert_diet_plan" {
  source              = "./modules/lambda"
  lambda_name         = "insert_diet_plan"
  handler             = "insert_diet_plan.lambda_handler"
  runtime             = "python3.12"
  lambda_s3_bucket    = var.lambda_s3_bucket
  lambda_function_key = var.insert_diet_plan_lambda_s3_key
  api_gateway_arn     = module.api_gateway.api_gateway_arn
  api_gateway_paths   = ["insert_diet_plan"]
  rds_secret_arn      = var.rds_secret_arn
  #  DB_NAME             = var.db_name
  #  DB_HOST             = var.db_host
  #  DB_PORT             = var.db_port
}

# API Gateway for exposing the Lambda functions
module "api_gateway" {
  source          = "./modules/api_gateway"
  region          = var.region
  api_name        = "granimals-auth-api"
  api_description = "API for Cognito auth Lambda functions"
  api_stage_name  = "dev"
  tags            = var.tags

  register_user_lambda_arn    = module.lambda_register_user.lambda_arn
  change_password_lambda_arn  = module.lambda_change_password.lambda_arn
  delete_user_lambda_arn      = module.lambda_delete_user.lambda_arn
  unknown_user_lambda_arn     = module.lambda_unknown_user.lambda_arn
  insert_diet_plan_lambda_arn = module.lambda_insert_diet_plan.lambda_arn
}