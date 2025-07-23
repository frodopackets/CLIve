# Terraform Variables for AI Assistant CLI

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-assistant-cli"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "ai-assistant-cli"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# Networking variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}# AI
 Services variables
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch log retention value."
  }
}

variable "knowledge_base_embedding_model" {
  description = "Bedrock embedding model for knowledge base"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
  
  validation {
    condition = contains([
      "amazon.titan-embed-text-v1",
      "amazon.titan-embed-text-v2:0"
    ], var.knowledge_base_embedding_model)
    error_message = "Embedding model must be a supported Titan embedding model."
  }
}

variable "knowledge_base_chunking_strategy" {
  description = "Chunking strategy for knowledge base documents"
  type        = string
  default     = "FIXED_SIZE"
  
  validation {
    condition     = contains(["FIXED_SIZE", "NONE"], var.knowledge_base_chunking_strategy)
    error_message = "Chunking strategy must be either FIXED_SIZE or NONE."
  }
}

variable "knowledge_base_chunk_size" {
  description = "Size of chunks for knowledge base documents (when using FIXED_SIZE strategy)"
  type        = number
  default     = 300
  
  validation {
    condition     = var.knowledge_base_chunk_size >= 20 && var.knowledge_base_chunk_size <= 8192
    error_message = "Chunk size must be between 20 and 8192 tokens."
  }
}

variable "knowledge_base_chunk_overlap" {
  description = "Overlap between chunks for knowledge base documents"
  type        = number
  default     = 20
  
  validation {
    condition     = var.knowledge_base_chunk_overlap >= 1 && var.knowledge_base_chunk_overlap <= 99
    error_message = "Chunk overlap must be between 1 and 99 percent."
  }
}

variable "bedrock_models" {
  description = "List of Bedrock models to grant access to"
  type        = list(string)
  default = [
    "amazon.nova-pro-v1:0",
    "amazon.nova-lite-v1:0"
  ]
}

variable "enable_bedrock_logging" {
  description = "Enable CloudWatch logging for Bedrock API calls"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}
# Lambda 
configuration variables
variable "lambda_runtime" {
  description = "Runtime for Lambda functions"
  type        = string
  default     = "python3.11"
  
  validation {
    condition = contains([
      "python3.8", "python3.9", "python3.10", "python3.11", "python3.12"
    ], var.lambda_runtime)
    error_message = "Lambda runtime must be a supported Python version."
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 30
  
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
  
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 and 10240 MB."
  }
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda functions"
  type        = number
  default     = 10
  
  validation {
    condition     = var.lambda_reserved_concurrency >= 0 && var.lambda_reserved_concurrency <= 1000
    error_message = "Lambda reserved concurrency must be between 0 and 1000."
  }
}

# API Gateway configuration variables
variable "api_gateway_stage_name" {
  description = "Stage name for API Gateway"
  type        = string
  default     = "v1"
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.api_gateway_stage_name))
    error_message = "API Gateway stage name must contain only alphanumeric characters, underscores, and hyphens."
  }
}

variable "api_gateway_throttle_rate_limit" {
  description = "Rate limit for API Gateway throttling (requests per second)"
  type        = number
  default     = 1000
  
  validation {
    condition     = var.api_gateway_throttle_rate_limit >= 1
    error_message = "API Gateway throttle rate limit must be at least 1."
  }
}

variable "api_gateway_throttle_burst_limit" {
  description = "Burst limit for API Gateway throttling"
  type        = number
  default     = 2000
  
  validation {
    condition     = var.api_gateway_throttle_burst_limit >= 1
    error_message = "API Gateway throttle burst limit must be at least 1."
  }
}

# DynamoDB configuration variables
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

# Authentication configuration variables
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

# Frontend hosting configuration variables
variable "frontend_s3_bucket_name" {
  description = "Name of the S3 bucket for frontend hosting (optional, will be generated if not provided)"
  type        = string
  default     = ""
}

variable "frontend_s3_force_destroy" {
  description = "Force destroy S3 bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "frontend_s3_versioning_enabled" {
  description = "Enable versioning on S3 bucket"
  type        = bool
  default     = true
}

variable "frontend_cloudfront_price_class" {
  description = "Price class for CloudFront distribution"
  type        = string
  default     = "PriceClass_100"
  
  validation {
    condition = contains([
      "PriceClass_All",
      "PriceClass_200", 
      "PriceClass_100"
    ], var.frontend_cloudfront_price_class)
    error_message = "CloudFront price class must be one of: PriceClass_All, PriceClass_200, PriceClass_100."
  }
}

variable "frontend_cloudfront_default_root_object" {
  description = "Default root object for CloudFront distribution"
  type        = string
  default     = "index.html"
}

variable "frontend_cloudfront_custom_error_responses" {
  description = "Custom error responses for CloudFront distribution"
  type = list(object({
    error_code         = number
    response_code      = number
    response_page_path = string
    error_caching_min_ttl = number
  }))
  default = [
    {
      error_code         = 404
      response_code      = 200
      response_page_path = "/index.html"
      error_caching_min_ttl = 300
    },
    {
      error_code         = 403
      response_code      = 200
      response_page_path = "/index.html"
      error_caching_min_ttl = 300
    }
  ]
}

variable "frontend_cloudfront_cache_behaviors" {
  description = "Cache behaviors for CloudFront distribution"
  type = list(object({
    path_pattern     = string
    allowed_methods  = list(string)
    cached_methods   = list(string)
    compress         = bool
    default_ttl      = number
    max_ttl          = number
    min_ttl          = number
  }))
  default = [
    {
      path_pattern     = "/static/*"
      allowed_methods  = ["GET", "HEAD"]
      cached_methods   = ["GET", "HEAD"]
      compress         = true
      default_ttl      = 86400
      max_ttl          = 31536000
      min_ttl          = 0
    }
  ]
}

variable "frontend_ssl_certificate_arn" {
  description = "ARN of SSL certificate for CloudFront (optional, will use CloudFront default if not provided)"
  type        = string
  default     = ""
}

variable "frontend_domain_name" {
  description = "Custom domain name for the frontend (optional)"
  type        = string
  default     = ""
}

variable "frontend_domain_aliases" {
  description = "Additional domain aliases for CloudFront distribution"
  type        = list(string)
  default     = []
}

variable "frontend_enable_waf" {
  description = "Enable AWS WAF for CloudFront distribution"
  type        = bool
  default     = false
}

variable "frontend_waf_web_acl_id" {
  description = "ID of WAF Web ACL to associate with CloudFront distribution"
  type        = string
  default     = ""
}

variable "frontend_enable_deployment_pipeline" {
  description = "Enable CodePipeline for frontend deployment"
  type        = bool
  default     = true
}

variable "frontend_github_repo_owner" {
  description = "GitHub repository owner for deployment pipeline"
  type        = string
  default     = ""
}

variable "frontend_github_repo_name" {
  description = "GitHub repository name for deployment pipeline"
  type        = string
  default     = ""
}

variable "frontend_github_branch" {
  description = "GitHub branch for deployment pipeline"
  type        = string
  default     = "main"
}

variable "frontend_build_spec_path" {
  description = "Path to buildspec.yml file for CodeBuild"
  type        = string
  default     = "frontend/buildspec.yml"
}

variable "frontend_source_dir" {
  description = "Source directory for frontend files"
  type        = string
  default     = "frontend/"
}

variable "frontend_build_output_dir" {
  description = "Build output directory for frontend files"
  type        = string
  default     = "frontend/dist"
}

variable "frontend_enable_cloudwatch_monitoring" {
  description = "Enable CloudWatch monitoring for CloudFront"
  type        = bool
  default     = true
}