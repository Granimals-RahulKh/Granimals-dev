#modules/lambda/main.tf
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.lambda_name}_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "cognito_access_policy" {
  name = "${var.lambda_name}_cognito_access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminDeleteUser",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:AdminAddUserToGroup",
          "cognito-idp:AdminRemoveUserFromGroup"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_cognito_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.cognito_access_policy.arn
}

resource "aws_lambda_function" "lambda_function" {
  function_name = var.lambda_name
  handler       = var.handler
  runtime       = var.runtime
  role          = aws_iam_role.lambda_exec_role.arn
  s3_bucket     = var.lambda_s3_bucket
  s3_key        = var.lambda_function_key

  environment {
    variables = {
      USER_POOL_ID           = var.user_pool_id
      USER_POOL_CLIENT_ID    = var.user_pool_client_id
      USER_GROUPS            = join(",", var.user_groups)
      REGISTER_FUNCTION_NAME = var.register_function_name
      FROM_EMAIL             = var.from_email
      #      SNS_TOPIC_ARN       = var.sns_topic_arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_cognito_access,
    aws_iam_role_policy_attachment.lambda_logs
  ]
}

output "lambda_arn" {
  value = aws_lambda_function.lambda_function.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.lambda_function.function_name
}

resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = var.api_gateway_arn
}

resource "aws_lambda_permission" "api_gateway" {
  count         = length(var.api_gateway_paths)
  statement_id  = "AllowExecutionFromAPIGateway-${count.index}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_arn}/*/*/${element(var.api_gateway_paths, count.index)}"
}
resource "aws_iam_policy" "allow_invoke_register_user" {
  name        = "AllowInvokeRegisterUser_${var.lambda_name}"
  description = "Allow ${var.lambda_name} Lambda to invoke register_user"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = "arn:aws:lambda:ap-south-1:211125304405:function:register_user"
      }
    ]
  })
}

#resource "aws_iam_role_policy_attachment" "attach_invoke_permission" {
#  role       = aws_iam_role.lambda_exec_role.name
#  policy_arn = aws_iam_policy.allow_invoke_register_user.arn
#}
#resource "aws_iam_policy" "lambda_sns_publish_policy" {
#  name        = "${var.lambda_name}-sns-publish-policy"
#  description = "Allow Lambda to publish to SNS"
#  policy = jsonencode({
#    Version = "2012-10-17"
#    Statement = [
#      {
#        Action = "sns:Publish"
#        Effect = "Allow"
#        Resource = var.sns_topic_arn
#      }
#    ]
#  })
#}

#resource "aws_iam_role_policy_attachment" "lambda_sns_attach" {
#  role       = aws_iam_role.lambda_exec_role.name
#  policy_arn = aws_iam_policy.lambda_sns_publish_policy.arn
#}
resource "aws_iam_policy" "lambda_ses_send_email" {
  name = "${var.lambda_name}-ses-send-email-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ses:SendEmail"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ses_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_ses_send_email.arn
}
