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

user_pool_id        = "ap-south-1_YjeFkbY7H"
user_pool_arn       = "arn:aws:cognito-idp:ap-south-1:211125304405:userpool/ap-south-1_YjeFkbY7H"
user_pool_client_id = "74oivi4jf3c7batf64b5g3spen"