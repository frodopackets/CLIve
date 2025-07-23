# Frontend hosting module for AI Assistant CLI
# This module creates S3 bucket for static website hosting, CloudFront distribution, and deployment pipeline

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

# Local values for common configurations
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(var.tags, {
    Module = "frontend-hosting"
  })
  
  # Generate bucket name if not provided
  bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.name_prefix}-frontend-${random_id.bucket_suffix.hex}"
  
  # Domain configuration
  has_custom_domain = var.domain_name != ""
  domain_aliases = var.domain_name != "" ? concat([var.domain_name], var.domain_aliases) : var.domain_aliases
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Random ID for bucket name uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

#
# S3 Bucket for Static Website Hosting
#
resource "aws_s3_bucket" "frontend" {
  bucket        = local.bucket_name
  force_destroy = var.s3_force_destroy

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-bucket"
    Purpose = "Static website hosting"
  })
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = var.s3_versioning_enabled ? "Enabled" : "Suspended"
  }
}

# S3 Bucket Server Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Website Configuration
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = var.cloudfront_default_root_object
  }

  error_document {
    key = var.cloudfront_default_root_object
  }
}

# S3 Bucket Policy for CloudFront OAC
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
  
  depends_on = [aws_cloudfront_distribution.frontend]
}

#
# CloudFront Origin Access Control
#
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  description                       = "Origin Access Control for ${local.name_prefix} frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

#
# CloudFront Distribution
#
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = var.cloudfront_default_root_object
  price_class         = var.cloudfront_price_class
  web_acl_id          = var.enable_waf && var.waf_web_acl_id != "" ? var.waf_web_acl_id : null

  aliases = local.domain_aliases

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.frontend.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Additional cache behaviors for static assets
  dynamic "ordered_cache_behavior" {
    for_each = var.cloudfront_cache_behaviors
    content {
      path_pattern           = ordered_cache_behavior.value.path_pattern
      allowed_methods        = ordered_cache_behavior.value.allowed_methods
      cached_methods         = ordered_cache_behavior.value.cached_methods
      target_origin_id       = "S3-${aws_s3_bucket.frontend.bucket}"
      compress               = ordered_cache_behavior.value.compress
      viewer_protocol_policy = "redirect-to-https"

      forwarded_values {
        query_string = false
        cookies {
          forward = "none"
        }
      }

      min_ttl     = ordered_cache_behavior.value.min_ttl
      default_ttl = ordered_cache_behavior.value.default_ttl
      max_ttl     = ordered_cache_behavior.value.max_ttl
    }
  }

  # Custom error responses for SPA routing
  dynamic "custom_error_response" {
    for_each = var.cloudfront_custom_error_responses
    content {
      error_code            = custom_error_response.value.error_code
      response_code         = custom_error_response.value.response_code
      response_page_path    = custom_error_response.value.response_page_path
      error_caching_min_ttl = custom_error_response.value.error_caching_min_ttl
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    # Use custom SSL certificate if provided, otherwise use CloudFront default
    dynamic "acm_certificate_arn" {
      for_each = var.ssl_certificate_arn != "" ? [var.ssl_certificate_arn] : []
      content {
        acm_certificate_arn      = var.ssl_certificate_arn
        ssl_support_method       = "sni-only"
        minimum_protocol_version = "TLSv1.2_2021"
      }
    }
    
    dynamic "cloudfront_default_certificate" {
      for_each = var.ssl_certificate_arn == "" ? [true] : []
      content {
        cloudfront_default_certificate = true
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-distribution"
    Purpose = "Frontend content delivery"
  })
}

#
# CloudWatch Log Group for Deployment Pipeline
#
resource "aws_cloudwatch_log_group" "deployment" {
  count             = var.enable_deployment_pipeline ? 1 : 0
  name              = "/aws/codebuild/${local.name_prefix}-frontend-build"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-deployment-logs"
  })
}

#
# IAM Role for CodeBuild
#
resource "aws_iam_role" "codebuild" {
  count = var.enable_deployment_pipeline ? 1 : 0
  name  = "${local.name_prefix}-frontend-codebuild-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for CodeBuild
resource "aws_iam_role_policy" "codebuild" {
  count = var.enable_deployment_pipeline ? 1 : 0
  name  = "${local.name_prefix}-frontend-codebuild-policy"
  role  = aws_iam_role.codebuild[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/codebuild/${local.name_prefix}-frontend-build*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.frontend.arn,
          "${aws_s3_bucket.frontend.arn}/*",
          aws_s3_bucket.artifacts[0].arn,
          "${aws_s3_bucket.artifacts[0].arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Resource = aws_cloudfront_distribution.frontend.arn
      }
    ]
  })
}

#
# S3 Bucket for CodePipeline Artifacts
#
resource "aws_s3_bucket" "artifacts" {
  count         = var.enable_deployment_pipeline ? 1 : 0
  bucket        = "${local.name_prefix}-frontend-artifacts-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-artifacts"
    Purpose = "CodePipeline artifacts storage"
  })
}

# S3 Bucket Server Side Encryption for Artifacts
resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  count  = var.enable_deployment_pipeline ? 1 : 0
  bucket = aws_s3_bucket.artifacts[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket Public Access Block for Artifacts
resource "aws_s3_bucket_public_access_block" "artifacts" {
  count  = var.enable_deployment_pipeline ? 1 : 0
  bucket = aws_s3_bucket.artifacts[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

#
# CodeBuild Project
#
resource "aws_codebuild_project" "frontend" {
  count         = var.enable_deployment_pipeline ? 1 : 0
  name          = "${local.name_prefix}-frontend-build"
  description   = "Build project for ${local.name_prefix} frontend"
  service_role  = aws_iam_role.codebuild[0].arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "S3_BUCKET"
      value = aws_s3_bucket.frontend.bucket
    }

    environment_variable {
      name  = "CLOUDFRONT_DISTRIBUTION_ID"
      value = aws_cloudfront_distribution.frontend.id
    }

    environment_variable {
      name  = "BUILD_OUTPUT_DIR"
      value = var.build_output_dir
    }
  }

  source {
    type = "CODEPIPELINE"
    buildspec = var.build_spec_path
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-build"
  })
}

#
# IAM Role for CodePipeline
#
resource "aws_iam_role" "codepipeline" {
  count = var.enable_deployment_pipeline ? 1 : 0
  name  = "${local.name_prefix}-frontend-codepipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for CodePipeline
resource "aws_iam_role_policy" "codepipeline" {
  count = var.enable_deployment_pipeline ? 1 : 0
  name  = "${local.name_prefix}-frontend-codepipeline-policy"
  role  = aws_iam_role.codepipeline[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          aws_s3_bucket.artifacts[0].arn,
          "${aws_s3_bucket.artifacts[0].arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild"
        ]
        Resource = aws_codebuild_project.frontend[0].arn
      }
    ]
  })
}

#
# CodePipeline
#
resource "aws_codepipeline" "frontend" {
  count    = var.enable_deployment_pipeline && var.github_repo_owner != "" && var.github_repo_name != "" ? 1 : 0
  name     = "${local.name_prefix}-frontend-pipeline"
  role_arn = aws_iam_role.codepipeline[0].arn

  artifact_store {
    location = aws_s3_bucket.artifacts[0].bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        Owner      = var.github_repo_owner
        Repo       = var.github_repo_name
        Branch     = var.github_branch
        OAuthToken = "{{resolve:secretsmanager:github-token:SecretString:token}}"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.frontend[0].name
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-pipeline"
  })
}

#
# CloudWatch Monitoring (if enabled)
#
resource "aws_cloudwatch_metric_alarm" "cloudfront_4xx_errors" {
  count               = var.enable_cloudwatch_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-frontend-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "This metric monitors CloudFront 4xx error rate"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DistributionId = aws_cloudfront_distribution.frontend.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "cloudfront_5xx_errors" {
  count               = var.enable_cloudwatch_monitoring ? 1 : 0
  alarm_name          = "${local.name_prefix}-frontend-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors CloudFront 5xx error rate"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DistributionId = aws_cloudfront_distribution.frontend.id
  }

  tags = local.common_tags
}