#resource "aws_api_gateway_deployment" "auth_deployment" {
#  depends_on = [
#    aws_api_gateway_integration.auth_integrations
#  ]

#  rest_api_id = aws_api_gateway_rest_api.auth_api.id
#  stage_name  = "prod"
#}