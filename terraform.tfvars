# terraform/terraform.tfvars

lambda_s3_bucket              = "granimals-auth-lambdas"
register_user_lambda_s3_key   = "register_user.zip"
change_password_lambda_s3_key = "change_password.zip"
delete_user_lambda_s3_key     = "delete_user.zip"
unknown_user_lambda_s3_key    = "unknown_user.zip"

region         = "ap-south-1"
api_stage_name = "dev"
api_name       = "granimals-auth-api"

tags = {
  Environment = "dev"
  Project     = "CognitoAuth"
}