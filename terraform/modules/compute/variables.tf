# Variables for compute module

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
}

# Networking variables
variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of the private subnets for Lambda functions"
  type        = list(string)
}

variable "lambda_security_group_id" {
  description = "ID of the security group for Lambda functions"
  type        = string
}

# AI Services variables
variable "lambda_bedrock_role_arn" {
  description = "ARN of the IAM role for Lambda functions to access Bedrock"
  type        = string
}

variable "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  type        = string
}

variable "bedrock_models" {
  description = "List of Bedrock models to grant access to"
  type        = list(string)
}

# Lambda configuration
variable "lambda_runtime" {
  description = "Runtime for Lambda functions"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda functions"
  type        = number
  default     = 10
}

# API Gateway configuration
variable "api_gateway_stage_name" {
  description = "Stage name for API Gateway"
  type        = string
  default     = "v1"
}

variable "api_gateway_throttle_rate_limit" {
  description = "Rate limit for API Gateway throttling"
  type        = number
  default     = 1000
}

variable "api_gateway_throttle_burst_limit" {
  description = "Burst limit for API Gateway throttling"
  type        = number
  default     = 2000
}

# DynamoDB configuration
variable "dynamodb_billing_mode" {
  description = "Billing mode for DynamoDB table"
  type        = string
  default     = "PAY_PER_REQUEST"
  
  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.dynamodb_billing_mode)
    error_message = "DynamoDB billing mode must be either PAY_PER_REQUEST or PROVISIONED."
  }
}

variable "dynamodb_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB table"
  type        = bool
  default     = true
}

# CloudWatch configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Authentication configuration
variable "identity_center_issuer_url" {
  description = "Identity Center issuer URL for JWT validation"
  type        = string
  default     = ""
}

variable "jwt_audience" {
  description = "Expected audience for JWT tokens"
  type        = string
  default     = ""
}