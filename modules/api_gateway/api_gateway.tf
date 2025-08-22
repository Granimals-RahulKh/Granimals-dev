#modules/api_gateway/api_gateway.tf
resource "aws_api_gateway_rest_api" "auth_api" {
  name        = "granimals-auth-api"
  description = "API for Cognito auth Lambda functions"
}

# -------------------------------------------------------------------
# Register User
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "register_user" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "register_user"
}

resource "aws_api_gateway_method" "register_user_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.register_user.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "register_user_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.register_user.id
  http_method             = aws_api_gateway_method.register_user_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.register_user_lambda_arn}/invocations"
}

# -------------------------------------------------------------------
# Change Password
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "change_password" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "change_password"
}

resource "aws_api_gateway_method" "change_password_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.change_password.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_auth.id
}

resource "aws_api_gateway_integration" "change_password_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.change_password.id
  http_method             = aws_api_gateway_method.change_password_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.change_password_lambda_arn}/invocations"
}

# -------------------------------------------------------------------
# Delete User
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "delete_user" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "delete_user"
}

resource "aws_api_gateway_method" "delete_user_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.delete_user.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_auth.id
}

resource "aws_api_gateway_integration" "delete_user_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.delete_user.id
  http_method             = aws_api_gateway_method.delete_user_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.delete_user_lambda_arn}/invocations"
}

# -------------------------------------------------------------------
# Login
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "login" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "login"
}

resource "aws_api_gateway_method" "login_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.login.id
  http_method             = aws_api_gateway_method.login_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.login_lambda_arn}/invocations"
}

# -------------------------------------------------------------------
# Insert Diet Plan
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "insert_diet_plan" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "insert_diet_plan"
}

resource "aws_api_gateway_method" "insert_diet_plan_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.insert_diet_plan.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "insert_diet_plan_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.insert_diet_plan.id
  http_method             = aws_api_gateway_method.insert_diet_plan_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.insert_diet_plan_lambda_arn}/invocations"
}

# -------------------------------------------------------------------
# Push Data to RDS
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "push_data_to_rds" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "push_data_to_rds"
}

resource "aws_api_gateway_method" "push_data_to_rds_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.push_data_to_rds.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_auth.id
}

resource "aws_api_gateway_integration" "push_data_to_rds_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.push_data_to_rds.id
  http_method             = aws_api_gateway_method.push_data_to_rds_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.push_data_to_rds_lambda_arn}/invocations"
}

# -------------------------------------------------------------------
# Pull Data from RDS
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "pull_data_from_rds" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "pull_data_from_rds"
}

resource "aws_api_gateway_method" "pull_data_from_rds_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.pull_data_from_rds.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_auth.id
}

resource "aws_api_gateway_integration" "pull_data_from_rds_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.pull_data_from_rds.id
  http_method             = aws_api_gateway_method.pull_data_from_rds_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.pull_data_from_rds_lambda_arn}/invocations"
}


# ---------------------------
# Reusable CORS Module (locals + reusable resource)
# ---------------------------
locals {
  cors_headers = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  cors_methods = "'OPTIONS,GET,POST,PUT,DELETE'"
  cors_origin  = "'*'"
}

# Helper function: add CORS to any resource
resource "aws_api_gateway_method" "cors_options" {
  for_each = {
    register_user             = aws_api_gateway_resource.register_user.id
    change_password           = aws_api_gateway_resource.change_password.id
    delete_user               = aws_api_gateway_resource.delete_user.id
    login                     = aws_api_gateway_resource.login.id
    insert_diet_plan          = aws_api_gateway_resource.insert_diet_plan.id
    push_data_to_rds          = aws_api_gateway_resource.push_data_to_rds.id
    pull_data_from_rds        = aws_api_gateway_resource.pull_data_from_rds.id
    push_onboarding_question  = aws_api_gateway_resource.push_onboarding_question.id
    pull_onboarding_questions = aws_api_gateway_resource.pull_onboarding_questions.id
  }
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = each.value
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors_options_integration" {
  for_each    = aws_api_gateway_method.cors_options
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "cors_options_response" {
  for_each    = aws_api_gateway_method.cors_options
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "cors_options_integration_response" {
  for_each    = aws_api_gateway_method.cors_options
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  status_code = aws_api_gateway_method_response.cors_options_response[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = local.cors_headers
    "method.response.header.Access-Control-Allow-Methods" = local.cors_methods
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}


# -------------------------------------------------------------------
# Push Onboarding Question
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "push_onboarding_question" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "push_onboarding_question"
}

resource "aws_api_gateway_method" "push_onboarding_question_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.push_onboarding_question.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_auth.id
}

resource "aws_api_gateway_integration" "push_onboarding_question_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.push_onboarding_question.id
  http_method             = aws_api_gateway_method.push_onboarding_question_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.push_onboarding_question_lambda_arn}/invocations"
}


# -------------------------------------------------------------------
# Pull Onboarding Questions
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "pull_onboarding_questions" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "pull_onboarding_questions"
}

resource "aws_api_gateway_method" "pull_onboarding_questions_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.pull_onboarding_questions.id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_auth.id
}

resource "aws_api_gateway_integration" "pull_onboarding_question_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.pull_onboarding_questions.id
  http_method             = aws_api_gateway_method.pull_onboarding_questions_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.pull_onboarding_questions_lambda_arn}/invocations"
}


# -------------------------------------------------------------------
# ChatGPT Integration (REST API)
# -------------------------------------------------------------------
resource "aws_api_gateway_resource" "chatgpt" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "chatgpt_integration"
}

resource "aws_api_gateway_method" "chatgpt_any" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.chatgpt.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "chatgpt_integration" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.chatgpt.id
  http_method             = aws_api_gateway_method.chatgpt_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.chatgpt_integration_lambda_arn}/invocations"
}


# -------------------------------------------------------------------
# Updated Deployment to include all integrations
# -------------------------------------------------------------------
resource "aws_api_gateway_deployment" "auth_deployment" {
  depends_on = [
    aws_api_gateway_integration.register_user_integration,
    aws_api_gateway_integration.change_password_integration,
    aws_api_gateway_integration.delete_user_integration,
    aws_api_gateway_integration.login_integration,
    aws_api_gateway_integration.insert_diet_plan_integration,
    aws_api_gateway_integration.push_data_to_rds_integration,
    aws_api_gateway_integration.pull_data_from_rds_integration,
    aws_api_gateway_integration.pull_onboarding_question_integration,
    aws_api_gateway_integration.chatgpt_integration,
  ]
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  description = "Deployment for API Gateway"

  lifecycle {
    create_before_destroy = true
  }

  triggers = {
    redeployment = timestamp() # forces new deployment on every plan/apply
  }
}

resource "aws_api_gateway_stage" "auth_stage" {
  stage_name    = var.api_stage_name
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  deployment_id = aws_api_gateway_deployment.auth_deployment.id
}

resource "aws_api_gateway_authorizer" "cognito_auth" {
  name            = "granimals-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.auth_api.id
  identity_source = "method.request.header.Authorization"
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [var.user_pool_arn]
}