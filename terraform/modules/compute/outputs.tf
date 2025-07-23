# Outputs for compute module

# Lambda Function outputs
output "lambda_main_function_name" {
  description = "Name of the main Lambda function"
  value       = aws_lambda_function.main.function_name
}

output "lambda_main_function_arn" {
  description = "ARN of the main Lambda function"
  value       = aws_lambda_function.main.arn
}

output "lambda_websocket_function_name" {
  description = "Name of the WebSocket Lambda function"
  value       = aws_lambda_function.websocket.function_name
}

output "lambda_websocket_function_arn" {
  description = "ARN of the WebSocket Lambda function"
  value       = aws_lambda_function.websocket.arn
}

output "lambda_jwt_authorizer_function_name" {
  description = "Name of the JWT authorizer Lambda function"
  value       = aws_lambda_function.jwt_authorizer.function_name
}

output "lambda_jwt_authorizer_function_arn" {
  description = "ARN of the JWT authorizer Lambda function"
  value       = aws_lambda_function.jwt_authorizer.arn
}

# API Gateway outputs
output "api_gateway_rest_api_id" {
  description = "ID of the REST API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_gateway_rest_api_arn" {
  description = "ARN of the REST API Gateway"
  value       = aws_api_gateway_rest_api.main.arn
}

output "api_gateway_rest_api_execution_arn" {
  description = "Execution ARN of the REST API Gateway"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "api_gateway_rest_api_url" {
  description = "URL of the REST API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${var.api_gateway_stage_name}"
}

output "api_gateway_websocket_api_id" {
  description = "ID of the WebSocket API Gateway"
  value       = aws_apigatewayv2_api.websocket.id
}

output "api_gateway_websocket_api_arn" {
  description = "ARN of the WebSocket API Gateway"
  value       = aws_apigatewayv2_api.websocket.arn
}

output "api_gateway_websocket_api_execution_arn" {
  description = "Execution ARN of the WebSocket API Gateway"
  value       = aws_apigatewayv2_api.websocket.execution_arn
}

output "api_gateway_websocket_url" {
  description = "URL of the WebSocket API Gateway"
  value       = "wss://${aws_apigatewayv2_api.websocket.id}.execute-api.${var.aws_region}.amazonaws.com/${var.api_gateway_stage_name}"
}

output "api_gateway_authorizer_id" {
  description = "ID of the JWT authorizer"
  value       = aws_api_gateway_authorizer.jwt.id
}

# DynamoDB outputs
output "dynamodb_sessions_table_name" {
  description = "Name of the DynamoDB sessions table"
  value       = aws_dynamodb_table.sessions.name
}

output "dynamodb_sessions_table_arn" {
  description = "ARN of the DynamoDB sessions table"
  value       = aws_dynamodb_table.sessions.arn
}

output "dynamodb_sessions_table_stream_arn" {
  description = "Stream ARN of the DynamoDB sessions table"
  value       = aws_dynamodb_table.sessions.stream_arn
}

# CloudWatch outputs
output "cloudwatch_log_group_api_gateway" {
  description = "Name of the API Gateway CloudWatch log group"
  value       = aws_cloudwatch_log_group.api_gateway.name
}

output "cloudwatch_log_group_lambda_main" {
  description = "Name of the main Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_main.name
}

output "cloudwatch_log_group_lambda_websocket" {
  description = "Name of the WebSocket Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_websocket.name
}

# Monitoring outputs
output "cloudwatch_alarms" {
  description = "CloudWatch alarms created for monitoring"
  value = {
    lambda_errors      = aws_cloudwatch_metric_alarm.lambda_errors.arn
    lambda_duration    = aws_cloudwatch_metric_alarm.lambda_duration.arn
    api_gateway_errors = aws_cloudwatch_metric_alarm.api_gateway_errors.arn
    dynamodb_throttles = aws_cloudwatch_metric_alarm.dynamodb_throttles.arn
  }
}

# Configuration outputs for other modules
output "compute_config" {
  description = "Configuration object for compute resources"
  value = {
    lambda_functions = {
      main = {
        name = aws_lambda_function.main.function_name
        arn  = aws_lambda_function.main.arn
      }
      websocket = {
        name = aws_lambda_function.websocket.function_name
        arn  = aws_lambda_function.websocket.arn
      }
      jwt_authorizer = {
        name = aws_lambda_function.jwt_authorizer.function_name
        arn  = aws_lambda_function.jwt_authorizer.arn
      }
    }
    api_gateway = {
      rest_api = {
        id           = aws_api_gateway_rest_api.main.id
        url          = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${var.api_gateway_stage_name}"
        execution_arn = aws_api_gateway_rest_api.main.execution_arn
      }
      websocket_api = {
        id           = aws_apigatewayv2_api.websocket.id
        url          = "wss://${aws_apigatewayv2_api.websocket.id}.execute-api.${var.aws_region}.amazonaws.com/${var.api_gateway_stage_name}"
        execution_arn = aws_apigatewayv2_api.websocket.execution_arn
      }
      authorizer_id = aws_api_gateway_authorizer.jwt.id
    }
    dynamodb = {
      sessions_table = {
        name = aws_dynamodb_table.sessions.name
        arn  = aws_dynamodb_table.sessions.arn
      }
    }
    log_groups = {
      api_gateway     = aws_cloudwatch_log_group.api_gateway.name
      lambda_main     = aws_cloudwatch_log_group.lambda_main.name
      lambda_websocket = aws_cloudwatch_log_group.lambda_websocket.name
    }
  }
}