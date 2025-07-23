# Variables for frontend hosting module

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

# S3 Configuration
variable "s3_bucket_name" {
  description = "Name of the S3 bucket for frontend hosting (optional, will be generated if not provided)"
  type        = string
  default     = ""
}

variable "s3_force_destroy" {
  description = "Force destroy S3 bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "s3_versioning_enabled" {
  description = "Enable versioning on S3 bucket"
  type        = bool
  default     = true
}

# CloudFront Configuration
variable "cloudfront_price_class" {
  description = "Price class for CloudFront distribution"
  type        = string
  default     = "PriceClass_100"
  
  validation {
    condition = contains([
      "PriceClass_All",
      "PriceClass_200", 
      "PriceClass_100"
    ], var.cloudfront_price_class)
    error_message = "CloudFront price class must be one of: PriceClass_All, PriceClass_200, PriceClass_100."
  }
}

variable "cloudfront_default_root_object" {
  description = "Default root object for CloudFront distribution"
  type        = string
  default     = "index.html"
}

variable "cloudfront_custom_error_responses" {
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

variable "cloudfront_cache_behaviors" {
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

# SSL/TLS Configuration
variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for CloudFront (optional, will use CloudFront default if not provided)"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Custom domain name for the frontend (optional)"
  type        = string
  default     = ""
}

variable "domain_aliases" {
  description = "Additional domain aliases for CloudFront distribution"
  type        = list(string)
  default     = []
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF for CloudFront distribution"
  type        = bool
  default     = false
}

variable "waf_web_acl_id" {
  description = "ID of WAF Web ACL to associate with CloudFront distribution"
  type        = string
  default     = ""
}

# Deployment Configuration
variable "enable_deployment_pipeline" {
  description = "Enable CodePipeline for frontend deployment"
  type        = bool
  default     = true
}

variable "github_repo_owner" {
  description = "GitHub repository owner for deployment pipeline"
  type        = string
  default     = ""
}

variable "github_repo_name" {
  description = "GitHub repository name for deployment pipeline"
  type        = string
  default     = ""
}

variable "github_branch" {
  description = "GitHub branch for deployment pipeline"
  type        = string
  default     = "main"
}

variable "build_spec_path" {
  description = "Path to buildspec.yml file for CodeBuild"
  type        = string
  default     = "frontend/buildspec.yml"
}

variable "source_dir" {
  description = "Source directory for frontend files"
  type        = string
  default     = "frontend/"
}

variable "build_output_dir" {
  description = "Build output directory for frontend files"
  type        = string
  default     = "frontend/dist"
}

# Monitoring Configuration
variable "enable_cloudwatch_monitoring" {
  description = "Enable CloudWatch monitoring for CloudFront"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarms trigger"
  type        = list(string)
  default     = []
}