output "api_gateway_id" {
  description = "The ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.auth_api.id
}

output "api_gateway_arn" {
  description = "The ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.auth_api.execution_arn
}

output "api_endpoint" {
  description = "Base URL of the deployed stage"
  value       = "${aws_api_gateway_rest_api.auth_api.execution_arn}/${aws_api_gateway_stage.auth_stage.stage_name}"
}

output "api_invoke_url" {
  description = "Invoke URL for the stage"
  value       = aws_api_gateway_stage.auth_stage.invoke_url
}