# terraform/terraform.tfvars

lambda_s3_bucket               = "granimals-auth-lambdas"
register_user_lambda_s3_key    = "register_user.zip"
change_password_lambda_s3_key  = "change_password.zip"
delete_user_lambda_s3_key      = "delete_user.zip"
login_lambda_s3_key            = "login.zip"
insert_diet_plan_lambda_s3_key = "insert_diet_plan.zip"
push_data_lambda_s3_key        = "push_data_to_rds.zip"
pull_data_lambda_s3_key        = "pull_data_from_rds.zip"


region         = "ap-south-1"
api_stage_name = "dev"
api_name       = "granimals-auth-api"

tags = {
  Environment = "dev"
  Project     = "CognitoAuth"
}

user_pool_id            = "ap-south-1_gaMIQZSBN"
user_pool_arn           = "arn:aws:cognito-idp:ap-south-1:211125304405:userpool/ap-south-1_gaMIQZSBN"
user_pool_client_id     = "77s0pgis059vt24bd0mdju7d9k"
user_pool_client_secret = "i9ikgr4eqrinm16vloro6afglstcvafg2dap8dlveqvdngea09u"


rds_secret_arn   = "arn:aws:secretsmanager:ap-south-1:211125304405:secret:db-creds-tQqMII"
lambda_layer_arn = "arn:aws:lambda:ap-south-1:211125304405:layer:psycopg2:7"


db_host = "rds-proxy-postgresqlv2.proxy-cr82g6co4rta.ap-south-1.rds.amazonaws.com"
db_port = "5432"
db_name = "granimalsdev"