# terraform/terraform.tfvars

lambda_s3_bucket                       = "granimals-auth-lambdas"
register_user_lambda_s3_key            = "register_user.zip"
change_password_lambda_s3_key          = "change_password.zip"
delete_user_lambda_s3_key              = "delete_user.zip"
login_lambda_s3_key                    = "login.zip"
insert_diet_plan_lambda_s3_key         = "insert_diet_plan.zip"
push_data_lambda_s3_key                = "push_data_to_rds.zip"
pull_data_lambda_s3_key                = "pull_data_from_rds.zip"
push_onboarding_lambda_s3_key          = "push_onboarding_question.zip"
pull_onboarding_lambda_s3_key          = "pull_onboarding_question.zip"
ai_food_stats_calculator_lambda_s3_key = "ai_food_stats_calculator.zip"


region         = "ap-south-1"
api_stage_name = "dev"
api_name       = "granimals-auth-api"

tags = {
  Environment = "dev"
  Project     = "CognitoAuth"
}

user_pool_id            = "ap-south-1_BHF74oRmO"
user_pool_arn           = "arn:aws:cognito-idp:ap-south-1:211125304405:userpool/ap-south-1_BHF74oRmO"
user_pool_client_id     = "1rvo2h51o7khfqfr4762otjdjc"
user_pool_client_secret = "j14qf9ncvk1acffhrfh6e391hmeuuif9tofcdgs9h9o0s32br0b"


rds_secret_arn   = "arn:aws:secretsmanager:ap-south-1:211125304405:secret:db-creds-tQqMII"
lambda_layer_arn = "arn:aws:lambda:ap-south-1:211125304405:layer:psycopg2:7"


db_host           = "rds-proxy-postgresqlv2.proxy-cr82g6co4rta.ap-south-1.rds.amazonaws.com"
db_port           = "5432"
db_name           = "granimalsdev"
openai_secret_arn = "arn:aws:secretsmanager:ap-south-1:211125304405:secret:openai_key-EmQA1Z"

user_pool_client_id_app        = "602ohhitoi3apraimn59a8psuv"
user_pool_client_secret_mobile = null # no secret for mobile
