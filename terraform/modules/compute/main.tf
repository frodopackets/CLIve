# Compute module for AI Assistant CLI
# This module creates Lambda functions, API Gateway, DynamoDB, and CloudWatch resources

terraform {
  required_providers {
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 0.70"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

# Local values for common configurations
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(var.tags, {
    Module = "compute"
  })
  
  lambda_environment_variables = {
    ENVIRONMENT           = var.environment
    AWS_REGION           = var.aws_region
    KNOWLEDGE_BASE_ID    = var.knowledge_base_id
    BEDROCK_MODELS       = jsonencode(var.bedrock_models)
    SESSIONS_TABLE_NAME  = aws_dynamodb_table.sessions.name
    LOG_LEVEL           = var.environment == "prod" ? "INFO" : "DEBUG"
    IDENTITY_CENTER_ISSUER_URL = var.identity_center_issuer_url
    JWT_AUDIENCE        = var.jwt_audience
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

#
# DynamoDB Table for Session Storage
#
resource "aws_dynamodb_table" "sessions" {
  name           = "${local.name_prefix}-sessions"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "session_id"
  
  attribute {
    name = "session_id"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "last_activity"
    type = "S"
  }
  
  # Global Secondary Index for user queries
  global_secondary_index {
    name            = "UserIndex"
    hash_key        = "user_id"
    range_key       = "last_activity"
    projection_type = "ALL"
  }
  
  # TTL for automatic session cleanup
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  
  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-sessions"
  })
}

#
# CloudWatch Log Groups
#
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-api-gateway-logs"
  })
}

resource "aws_cloudwatch_log_group" "lambda_main" {
  name              = "/aws/lambda/${local.name_prefix}-main"
  retention_in_days = var.log_retention_days
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-lambda-main-logs"
  })
}

resource "aws_cloudwatch_log_group" "lambda_websocket" {
  name              = "/aws/lambda/${local.name_prefix}-websocket"
  retention_in_days = var.log_retention_days
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-lambda-websocket-logs"
  })
}

#
# Lambda Function Package
#
data "archive_file" "lambda_package" {
  type        = "zip"
  output_path = "${path.module}/lambda_package.zip"
  
  source {
    content = templatefile("${path.module}/lambda_placeholder.py", {
      environment = var.environment
    })
    filename = "main.py"
  }
}

#
# Main Lambda Function (FastAPI Backend)
#
resource "aws_lambda_function" "main" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${local.name_prefix}-main"
  role            = var.lambda_bedrock_role_arn
  handler         = "main.handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  reserved_concurrent_executions = var.lambda_reserved_concurrency
  
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
  
  environment {
    variables = local.lambda_environment_variables
  }
  
  depends_on = [aws_cloudwatch_log_group.lambda_main]
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-main-lambda"
  })
}

#
# WebSocket Lambda Function
#
resource "aws_lambda_function" "websocket" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${local.name_prefix}-websocket"
  role            = var.lambda_bedrock_role_arn
  handler         = "websocket.handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  reserved_concurrent_executions = var.lambda_reserved_concurrency
  
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
  
  environment {
    variables = local.lambda_environment_variables
  }
  
  depends_on = [aws_cloudwatch_log_group.lambda_websocket]
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-websocket-lambda"
  })
}

#
# Lambda Permissions for API Gateway
#
resource "aws_lambda_permission" "api_gateway_main" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_websocket" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

#
# JWT Authorizer Lambda Function
#
resource "aws_lambda_function" "jwt_authorizer" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${local.name_prefix}-jwt-authorizer"
  role            = var.lambda_bedrock_role_arn
  handler         = "jwt_authorizer.handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256
  
  environment {
    variables = {
      IDENTITY_CENTER_ISSUER_URL = var.identity_center_issuer_url
      JWT_AUDIENCE              = var.jwt_audience
      LOG_LEVEL                = var.environment == "prod" ? "INFO" : "DEBUG"
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-jwt-authorizer-lambda"
  })
}

resource "aws_lambda_permission" "jwt_authorizer" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.jwt_authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/authorizers/*"
}

#
# REST API Gateway
#
resource "aws_api_gateway_rest_api" "main" {
  name        = "${local.name_prefix}-api"
  description = "AI Assistant CLI REST API"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rest-api"
  })
}

# JWT Authorizer
resource "aws_api_gateway_authorizer" "jwt" {
  name                   = "${local.name_prefix}-jwt-authorizer"
  rest_api_id           = aws_api_gateway_rest_api.main.id
  authorizer_uri        = aws_lambda_function.jwt_authorizer.invoke_arn
  authorizer_credentials = var.lambda_bedrock_role_arn
  type                  = "TOKEN"
  identity_source       = "method.request.header.Authorization"
  authorizer_result_ttl_in_seconds = 300
}

# API Gateway Resources and Methods
resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "v1"
}

# Health check endpoint (no auth required)
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "health"
}

resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "health_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# Sessions endpoint (auth required)
resource "aws_api_gateway_resource" "sessions" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "sessions"
}

resource "aws_api_gateway_method" "sessions_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "sessions_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.sessions_get.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

resource "aws_api_gateway_method" "sessions_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "sessions_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.sessions_post.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# Session by ID endpoint
resource "aws_api_gateway_resource" "session_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.sessions.id
  path_part   = "{session_id}"
}

resource "aws_api_gateway_method" "session_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.session_id.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "session_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.session_id.id
  http_method = aws_api_gateway_method.session_get.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

resource "aws_api_gateway_method" "session_delete" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.session_id.id
  http_method   = "DELETE"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "session_delete" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.session_id.id
  http_method = aws_api_gateway_method.session_delete.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# Knowledge bases endpoint
resource "aws_api_gateway_resource" "knowledge_bases" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "knowledge-bases"
}

resource "aws_api_gateway_method" "knowledge_bases_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.knowledge_bases.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "knowledge_bases_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.knowledge_bases.id
  http_method = aws_api_gateway_method.knowledge_bases_get.http_method
  
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# CORS configuration for all resources
resource "aws_api_gateway_method" "cors_options" {
  for_each = toset([
    aws_api_gateway_resource.health.id,
    aws_api_gateway_resource.sessions.id,
    aws_api_gateway_resource.session_id.id,
    aws_api_gateway_resource.knowledge_bases.id
  ])
  
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = each.value
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors_options" {
  for_each = aws_api_gateway_method.cors_options
  
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_options" {
  for_each = aws_api_gateway_method.cors_options
  
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "cors_options" {
  for_each = aws_api_gateway_integration.cors_options
  
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.health_get,
    aws_api_gateway_integration.sessions_get,
    aws_api_gateway_integration.sessions_post,
    aws_api_gateway_integration.session_get,
    aws_api_gateway_integration.session_delete,
    aws_api_gateway_integration.knowledge_bases_get,
    aws_api_gateway_integration.cors_options
  ]
  
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.api_gateway_stage_name
  
  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.api_gateway_stage_name
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip            = "$context.identity.sourceIp"
      caller        = "$context.identity.caller"
      user          = "$context.identity.user"
      requestTime   = "$context.requestTime"
      httpMethod    = "$context.httpMethod"
      resourcePath  = "$context.resourcePath"
      status        = "$context.status"
      protocol      = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-api-stage"
  })
}

# API Gateway Method Settings
resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"
  
  settings {
    metrics_enabled    = true
    logging_level     = "INFO"
    data_trace_enabled = var.environment != "prod"
    
    throttling_rate_limit  = var.api_gateway_throttle_rate_limit
    throttling_burst_limit = var.api_gateway_throttle_burst_limit
  }
}

#
# WebSocket API Gateway
#
resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${local.name_prefix}-websocket"
  protocol_type             = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-websocket-api"
  })
}

# WebSocket Routes
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_connect.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_disconnect.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_default.id}"
}

# WebSocket Integrations
resource "aws_apigatewayv2_integration" "websocket_connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket.invoke_arn
}

resource "aws_apigatewayv2_integration" "websocket_disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket.invoke_arn
}

resource "aws_apigatewayv2_integration" "websocket_default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket.invoke_arn
}

# WebSocket Stage
resource "aws_apigatewayv2_stage" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = var.api_gateway_stage_name
  auto_deploy = true
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip            = "$context.identity.sourceIp"
      requestTime   = "$context.requestTime"
      routeKey      = "$context.routeKey"
      status        = "$context.status"
      protocol      = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-websocket-stage"
  })
}

#
# CloudWatch Alarms and Monitoring
#
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors"
  
  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.name_prefix}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "25000"  # 25 seconds
  alarm_description   = "This metric monitors lambda duration"
  
  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_gateway_errors" {
  alarm_name          = "${local.name_prefix}-api-gateway-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors API Gateway 4XX errors"
  
  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
  }
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  alarm_name          = "${local.name_prefix}-dynamodb-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors DynamoDB throttles"
  
  dimensions = {
    TableName = aws_dynamodb_table.sessions.name
  }
  
  tags = local.common_tags
}