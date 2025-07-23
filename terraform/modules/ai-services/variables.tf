# Variables for AI Services module

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
  default     = {}
}

variable "vpc_id" {
  description = "VPC ID for resources that need VPC placement"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Lambda functions"
  type        = list(string)
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch log retention value."
  }
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
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

variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch Serverless collection"
  type        = string
  default     = "search.t3.small.search"
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