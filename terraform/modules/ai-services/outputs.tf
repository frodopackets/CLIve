# Outputs for AI Services module

output "knowledge_base_s3_bucket_name" {
  description = "Name of the S3 bucket for knowledge base data sources"
  value       = aws_s3_bucket.knowledge_base_data.bucket
}

output "knowledge_base_s3_bucket_arn" {
  description = "ARN of the S3 bucket for knowledge base data sources"
  value       = aws_s3_bucket.knowledge_base_data.arn
}

output "opensearch_collection_endpoint" {
  description = "Endpoint of the OpenSearch Serverless collection"
  value       = awscc_opensearchserverless_collection.knowledge_base_vector_store.collection_endpoint
}

output "opensearch_collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  value       = awscc_opensearchserverless_collection.knowledge_base_vector_store.arn
}

output "opensearch_collection_id" {
  description = "ID of the OpenSearch Serverless collection"
  value       = awscc_opensearchserverless_collection.knowledge_base_vector_store.id
}

output "bedrock_knowledge_base_role_arn" {
  description = "ARN of the IAM role for Bedrock Knowledge Base"
  value       = aws_iam_role.bedrock_knowledge_base_role.arn
}

output "bedrock_knowledge_base_role_name" {
  description = "Name of the IAM role for Bedrock Knowledge Base"
  value       = aws_iam_role.bedrock_knowledge_base_role.name
}

output "lambda_bedrock_role_arn" {
  description = "ARN of the IAM role for Lambda functions to access Bedrock"
  value       = aws_iam_role.lambda_bedrock_role.arn
}

output "lambda_bedrock_role_name" {
  description = "Name of the IAM role for Lambda functions to access Bedrock"
  value       = aws_iam_role.lambda_bedrock_role.name
}

output "bedrock_api_log_group_name" {
  description = "Name of the CloudWatch log group for Bedrock API logs"
  value       = aws_cloudwatch_log_group.bedrock_api_logs.name
}

output "knowledge_base_log_group_name" {
  description = "Name of the CloudWatch log group for Knowledge Base logs"
  value       = aws_cloudwatch_log_group.knowledge_base_logs.name
}

output "bedrock_models" {
  description = "List of Bedrock models configured for access"
  value       = var.bedrock_models
}

output "embedding_model" {
  description = "Bedrock embedding model configured for knowledge base"
  value       = var.knowledge_base_embedding_model
}

# Security and monitoring outputs
output "bedrock_error_alarm_arn" {
  description = "ARN of the CloudWatch alarm for Bedrock errors"
  value       = aws_cloudwatch_metric_alarm.bedrock_error_rate.arn
}

output "bedrock_throttling_alarm_arn" {
  description = "ARN of the CloudWatch alarm for Bedrock throttling"
  value       = aws_cloudwatch_metric_alarm.bedrock_throttling.arn
}

# Configuration outputs for other modules
output "ai_services_config" {
  description = "Configuration object for AI services"
  value = {
    knowledge_base_bucket = aws_s3_bucket.knowledge_base_data.bucket
    opensearch_endpoint   = awscc_opensearchserverless_collection.knowledge_base_vector_store.collection_endpoint
    bedrock_role_arn     = aws_iam_role.bedrock_knowledge_base_role.arn
    lambda_role_arn      = aws_iam_role.lambda_bedrock_role.arn
    embedding_model      = var.knowledge_base_embedding_model
    supported_models     = var.bedrock_models
    log_groups = {
      bedrock_api      = aws_cloudwatch_log_group.bedrock_api_logs.name
      knowledge_base   = aws_cloudwatch_log_group.knowledge_base_logs.name
    }
  }
}# K
nowledge Base outputs
output "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  value       = awscc_bedrock_knowledge_base.main.knowledge_base_id
}

output "knowledge_base_arn" {
  description = "ARN of the Bedrock Knowledge Base"
  value       = awscc_bedrock_knowledge_base.main.knowledge_base_arn
}

output "knowledge_base_name" {
  description = "Name of the Bedrock Knowledge Base"
  value       = awscc_bedrock_knowledge_base.main.name
}

output "data_source_id" {
  description = "ID of the Bedrock Data Source"
  value       = awscc_bedrock_data_source.main.data_source_id
}

output "data_source_name" {
  description = "Name of the Bedrock Data Source"
  value       = awscc_bedrock_data_source.main.name
}