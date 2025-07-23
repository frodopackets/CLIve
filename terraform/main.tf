# Main Terraform configuration for AI Assistant CLI
terraform {
  required_version = ">= 1.0"
  required_providers {
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 0.70"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Configure the AWSCC Provider
provider "awscc" {
  region = var.aws_region
  
  default_tags {
    tags = var.tags
  }
}

# Configure the AWS Provider (for resources not yet supported by AWSCC)
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = var.tags
  }
}

# Local values for common configurations
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(var.tags, {
    Environment = var.environment
    Region      = var.aws_region
  })
}

# Data sources for existing resources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Module instantiations
module "networking" {
  source = "./modules/networking"
  
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
  tags         = local.common_tags
  
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
}

module "security" {
  source = "./modules/security"
  
  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
  
  vpc_id = module.networking.vpc_id
}

module "ai_services" {
  source = "./modules/ai-services"
  
  project_name             = var.project_name
  environment              = var.environment
  aws_region               = var.aws_region
  tags                     = local.common_tags
  
  vpc_id                   = module.networking.vpc_id
  private_subnet_ids       = module.networking.private_subnet_ids
  lambda_security_group_id = module.security.lambda_security_group_id
  
  # AI Services configuration
  log_retention_days                = var.log_retention_days
  knowledge_base_embedding_model    = var.knowledge_base_embedding_model
  knowledge_base_chunking_strategy  = var.knowledge_base_chunking_strategy
  knowledge_base_chunk_size         = var.knowledge_base_chunk_size
  knowledge_base_chunk_overlap      = var.knowledge_base_chunk_overlap
  bedrock_models                    = var.bedrock_models
  enable_bedrock_logging            = var.enable_bedrock_logging
  alarm_actions                     = var.alarm_actions
}

module "compute" {
  source = "./modules/compute"
  
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
  tags         = local.common_tags
  
  # Networking configuration
  vpc_id                    = module.networking.vpc_id
  private_subnet_ids        = module.networking.private_subnet_ids
  lambda_security_group_id  = module.security.lambda_security_group_id
  
  # AI Services integration
  lambda_bedrock_role_arn   = module.ai_services.lambda_bedrock_role_arn
  knowledge_base_id         = module.ai_services.knowledge_base_id
  bedrock_models            = var.bedrock_models
  
  # Lambda configuration
  lambda_runtime                    = var.lambda_runtime
  lambda_timeout                    = var.lambda_timeout
  lambda_memory_size                = var.lambda_memory_size
  lambda_reserved_concurrency       = var.lambda_reserved_concurrency
  
  # API Gateway configuration
  api_gateway_stage_name            = var.api_gateway_stage_name
  api_gateway_throttle_rate_limit   = var.api_gateway_throttle_rate_limit
  api_gateway_throttle_burst_limit  = var.api_gateway_throttle_burst_limit
  
  # DynamoDB configuration
  dynamodb_billing_mode             = var.dynamodb_billing_mode
  dynamodb_point_in_time_recovery   = var.dynamodb_point_in_time_recovery
  
  # CloudWatch configuration
  log_retention_days                = var.log_retention_days
  
  # Authentication configuration
  identity_center_issuer_url        = var.identity_center_issuer_url
  jwt_audience                      = var.jwt_audience
}

module "frontend_hosting" {
  source = "./modules/frontend-hosting"
  
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
  tags         = local.common_tags
  
  # S3 Configuration
  s3_bucket_name        = var.frontend_s3_bucket_name
  s3_force_destroy      = var.frontend_s3_force_destroy
  s3_versioning_enabled = var.frontend_s3_versioning_enabled
  
  # CloudFront Configuration
  cloudfront_price_class                = var.frontend_cloudfront_price_class
  cloudfront_default_root_object        = var.frontend_cloudfront_default_root_object
  cloudfront_custom_error_responses     = var.frontend_cloudfront_custom_error_responses
  cloudfront_cache_behaviors            = var.frontend_cloudfront_cache_behaviors
  
  # SSL/TLS Configuration
  ssl_certificate_arn = var.frontend_ssl_certificate_arn
  domain_name         = var.frontend_domain_name
  domain_aliases      = var.frontend_domain_aliases
  
  # Security Configuration
  enable_waf      = var.frontend_enable_waf
  waf_web_acl_id  = var.frontend_waf_web_acl_id
  
  # Deployment Configuration
  enable_deployment_pipeline = var.frontend_enable_deployment_pipeline
  github_repo_owner          = var.frontend_github_repo_owner
  github_repo_name           = var.frontend_github_repo_name
  github_branch              = var.frontend_github_branch
  build_spec_path            = var.frontend_build_spec_path
  source_dir                 = var.frontend_source_dir
  build_output_dir           = var.frontend_build_output_dir
  
  # Monitoring Configuration
  enable_cloudwatch_monitoring = var.frontend_enable_cloudwatch_monitoring
  log_retention_days           = var.log_retention_days
  alarm_actions                = var.alarm_actions
}