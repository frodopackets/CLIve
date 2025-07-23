# Output values for the main Terraform configuration

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "security_group_lambda_id" {
  description = "ID of the Lambda security group"
  value       = module.security.lambda_security_group_id
}

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}#
 AI Services outputs
output "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  value       = module.ai_services.knowledge_base_id
}

output "knowledge_base_arn" {
  description = "ARN of the Bedrock Knowledge Base"
  value       = module.ai_services.knowledge_base_arn
}

output "knowledge_base_s3_bucket_name" {
  description = "Name of the S3 bucket for knowledge base data sources"
  value       = module.ai_services.knowledge_base_s3_bucket_name
}

output "opensearch_collection_endpoint" {
  description = "Endpoint of the OpenSearch Serverless collection"
  value       = module.ai_services.opensearch_collection_endpoint
}

output "bedrock_knowledge_base_role_arn" {
  description = "ARN of the IAM role for Bedrock Knowledge Base"
  value       = module.ai_services.bedrock_knowledge_base_role_arn
}

output "lambda_bedrock_role_arn" {
  description = "ARN of the IAM role for Lambda functions to access Bedrock"
  value       = module.ai_services.lambda_bedrock_role_arn
}

output "ai_services_config" {
  description = "Configuration object for AI services"
  value       = module.ai_services.ai_services_config
  sensitive   = false
}#
 Compute module outputs
output "api_gateway_rest_api_url" {
  description = "URL of the REST API Gateway"
  value       = module.compute.api_gateway_rest_api_url
}

output "api_gateway_websocket_url" {
  description = "URL of the WebSocket API Gateway"
  value       = module.compute.api_gateway_websocket_url
}

output "lambda_main_function_name" {
  description = "Name of the main Lambda function"
  value       = module.compute.lambda_main_function_name
}

output "lambda_websocket_function_name" {
  description = "Name of the WebSocket Lambda function"
  value       = module.compute.lambda_websocket_function_name
}

output "dynamodb_sessions_table_name" {
  description = "Name of the DynamoDB sessions table"
  value       = module.compute.dynamodb_sessions_table_name
}

output "compute_config" {
  description = "Configuration object for compute resources"
  value       = module.compute.compute_config
  sensitive   = false
}

# Frontend hosting outputs
output "frontend_s3_bucket_name" {
  description = "Name of the S3 bucket for frontend hosting"
  value       = module.frontend_hosting.s3_bucket_name
}

output "frontend_cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = module.frontend_hosting.cloudfront_distribution_id
}

output "frontend_cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = module.frontend_hosting.cloudfront_domain_name
}

output "frontend_cloudfront_distribution_url" {
  description = "URL of the CloudFront distribution"
  value       = module.frontend_hosting.cloudfront_distribution_url
}

output "frontend_custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = module.frontend_hosting.custom_domain_url
}

output "frontend_codebuild_project_name" {
  description = "Name of the CodeBuild project for frontend deployment"
  value       = module.frontend_hosting.codebuild_project_name
}

output "frontend_codepipeline_name" {
  description = "Name of the CodePipeline for frontend deployment"
  value       = module.frontend_hosting.codepipeline_name
}

output "frontend_hosting_config" {
  description = "Complete frontend hosting configuration"
  value       = module.frontend_hosting.frontend_hosting_config
  sensitive   = false
}

# Combined configuration for easy reference
output "application_config" {
  description = "Complete application configuration"
  value = {
    environment = var.environment
    region      = var.aws_region
    
    api_endpoints = {
      rest_api   = module.compute.api_gateway_rest_api_url
      websocket  = module.compute.api_gateway_websocket_url
    }
    
    lambda_functions = {
      main       = module.compute.lambda_main_function_name
      websocket  = module.compute.lambda_websocket_function_name
    }
    
    storage = {
      sessions_table = module.compute.dynamodb_sessions_table_name
      knowledge_base_bucket = module.ai_services.knowledge_base_s3_bucket_name
      frontend_bucket = module.frontend_hosting.s3_bucket_name
    }
    
    ai_services = {
      knowledge_base_id = module.ai_services.knowledge_base_id
      bedrock_models    = var.bedrock_models
    }
    
    frontend = {
      cloudfront_url = module.frontend_hosting.cloudfront_distribution_url
      custom_domain_url = module.frontend_hosting.custom_domain_url
      s3_bucket = module.frontend_hosting.s3_bucket_name
      distribution_id = module.frontend_hosting.cloudfront_distribution_id
    }
  }
  sensitive = false
}