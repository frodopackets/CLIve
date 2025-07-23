# Security module for AI Assistant CLI
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
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Security Group for Lambda Functions
resource "awscc_ec2_security_group" "lambda" {
  group_name        = "${local.name_prefix}-lambda-sg"
  group_description = "Security group for Lambda functions"
  vpc_id            = var.vpc_id
  
  security_group_egress = [
    {
      ip_protocol                = "tcp"
      from_port                  = 443
      to_port                    = 443
      cidr_ip                    = "0.0.0.0/0"
      description                = "HTTPS outbound for AWS services"
    },
    {
      ip_protocol                = "tcp"
      from_port                  = 80
      to_port                    = 80
      cidr_ip                    = "0.0.0.0/0"
      description                = "HTTP outbound for package downloads"
    }
  ]
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-lambda-sg"
    Type = "lambda"
  })
}

# Security Group for API Gateway VPC Link (if needed)
resource "awscc_ec2_security_group" "api_gateway" {
  group_name        = "${local.name_prefix}-api-gateway-sg"
  group_description = "Security group for API Gateway VPC Link"
  vpc_id            = var.vpc_id
  
  security_group_ingress = [
    {
      ip_protocol                = "tcp"
      from_port                  = 443
      to_port                    = 443
      cidr_ip                    = "0.0.0.0/0"
      description                = "HTTPS inbound from internet"
    }
  ]
  
  security_group_egress = [
    {
      ip_protocol                = "tcp"
      from_port                  = 8000
      to_port                    = 8000
      source_security_group_id   = awscc_ec2_security_group.lambda.id
      description                = "HTTP to Lambda functions"
    }
  ]
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-gateway-sg"
    Type = "api-gateway"
  })
}

# Security Group for VPC Endpoints
resource "awscc_ec2_security_group" "vpc_endpoints" {
  group_name        = "${local.name_prefix}-vpc-endpoints-sg"
  group_description = "Security group for VPC endpoints"
  vpc_id            = var.vpc_id
  
  security_group_ingress = [
    {
      ip_protocol                = "tcp"
      from_port                  = 443
      to_port                    = 443
      source_security_group_id   = awscc_ec2_security_group.lambda.id
      description                = "HTTPS from Lambda functions"
    }
  ]
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-vpc-endpoints-sg"
    Type = "vpc-endpoints"
  })
}

# WAF Web ACL for API Gateway protection
resource "aws_wafv2_web_acl" "api_protection" {
  name  = "${local.name_prefix}-api-protection"
  scope = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    action {
      block {}
    }
    
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }
  
  # AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }
  
  # AWS Managed Rules - Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-bad-inputs"
      sampled_requests_enabled   = true
    }
  }
  
  tags = var.tags
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }
}

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "/aws/wafv2/${local.name_prefix}"
  retention_in_days = 30
  
  tags = var.tags
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "api_protection" {
  resource_arn            = aws_wafv2_web_acl.api_protection.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]
}