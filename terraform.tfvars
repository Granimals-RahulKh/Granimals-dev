# terraform/terraform.tfvars

lambda_s3_bucket               = "granimals-auth-lambdas"
register_user_lambda_s3_key    = "register_user.zip"
change_password_lambda_s3_key  = "change_password.zip"
delete_user_lambda_s3_key      = "delete_user.zip"
login_lambda_s3_key            = "login.zip"
insert_diet_plan_lambda_s3_key = "insert_diet_plan.zip"

region         = "ap-south-1"
api_stage_name = "dev"
api_name       = "granimals-auth-api"

tags = {
  Environment = "dev"
  Project     = "CognitoAuth"
}

user_pool_id            = "ap-south-1_1MWt66w1H"
user_pool_arn           = "arn:aws:cognito-idp:ap-south-1:211125304405:userpool/ap-south-1_1MWt66w1H"
user_pool_client_id     = "6ge8o11et15ho25l3q5kpepkjn"
user_pool_client_secret = "5ite76cdc7vrpqe3mioe4ut44idrekj4ppaeamf1ep313m7ggeo"


rds_secret_arn   = "arn:aws:secretsmanager:ap-south-1:211125304405:secret:db-creds-tQqMII"
lambda_layer_arn = "arn:aws:lambda:ap-south-1:211125304405:layer:psycopg2:7"


db_host = "rds-proxy-postgresqlv2.proxy-cr82g6co4rta.ap-south-1.rds.amazonaws.com"
db_port = "5432"
db_name = "granimalsdev"