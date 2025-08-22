# terraform/terraform.tfvars

lambda_s3_bucket                  = "granimals-auth-lambdas"
register_user_lambda_s3_key       = "register_user.zip"
change_password_lambda_s3_key     = "change_password.zip"
delete_user_lambda_s3_key         = "delete_user.zip"
login_lambda_s3_key               = "login.zip"
insert_diet_plan_lambda_s3_key    = "insert_diet_plan.zip"
push_data_lambda_s3_key           = "push_data_to_rds.zip"
pull_data_lambda_s3_key           = "pull_data_from_rds.zip"
push_onboarding_lambda_s3_key     = "push_onboarding_question.zip"
pull_onboarding_lambda_s3_key     = "pull_onboarding_question.zip"
chatgpt_integration_lambda_s3_key = "chatgpt_integration.zip"


region         = "ap-south-1"
api_stage_name = "dev"
api_name       = "granimals-auth-api"

tags = {
  Environment = "dev"
  Project     = "CognitoAuth"
}

user_pool_id            = "ap-south-1_oZQtOxNAm"
user_pool_arn           = "arn:aws:cognito-idp:ap-south-1:211125304405:userpool/ap-south-1_oZQtOxNAm"
user_pool_client_id     = "4t645skkm7u0juuhhpu3knmtd0"
user_pool_client_secret = "s6hul8r0cv7pj8j26kf5ea11hktjl7l13rqs29bgst3jnhk7r17"


rds_secret_arn   = "arn:aws:secretsmanager:ap-south-1:211125304405:secret:db-creds-tQqMII"
lambda_layer_arn = "arn:aws:lambda:ap-south-1:211125304405:layer:psycopg2:7"


db_host = "rds-proxy-postgresqlv2.proxy-cr82g6co4rta.ap-south-1.rds.amazonaws.com"
db_port = "5432"
db_name = "granimalsdev"
openai_secret_arn = "arn:aws:secretsmanager:ap-south-1:211125304405:secret:openai_key-EmQA1Z"

user_pool_client_id_app        = "2cqadt28vkic72uplieudsh6sv"
user_pool_client_secret_mobile = null # no secret for mobile
