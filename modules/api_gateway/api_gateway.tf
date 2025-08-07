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
  authorization = "NONE"
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
  authorization = "NONE"
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
# Unknown User
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
# Updated Deployment to include all integrations
# -------------------------------------------------------------------
resource "aws_api_gateway_deployment" "auth_deployment" {
  depends_on = [
    aws_api_gateway_integration.register_user_integration,
    aws_api_gateway_integration.change_password_integration,
    aws_api_gateway_integration.delete_user_integration,
    aws_api_gateway_integration.login_integration,
    aws_api_gateway_integration.insert_diet_plan_integration,
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