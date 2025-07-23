# Outputs for frontend hosting module

# S3 Bucket outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for frontend hosting"
  value       = aws_s3_bucket.frontend.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for frontend hosting"
  value       = aws_s3_bucket.frontend.arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.frontend.bucket_domain_name
}

output "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "s3_website_endpoint" {
  description = "Website endpoint of the S3 bucket"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

# CloudFront outputs
output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "Hosted zone ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.hosted_zone_id
}

output "cloudfront_distribution_url" {
  description = "URL of the CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

# Custom domain outputs (if configured)
output "custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : ""
}

output "domain_aliases" {
  description = "List of domain aliases configured for CloudFront"
  value       = local.domain_aliases
}

# Deployment pipeline outputs
output "codebuild_project_name" {
  description = "Name of the CodeBuild project"
  value       = var.enable_deployment_pipeline ? aws_codebuild_project.frontend[0].name : ""
}

output "codebuild_project_arn" {
  description = "ARN of the CodeBuild project"
  value       = var.enable_deployment_pipeline ? aws_codebuild_project.frontend[0].arn : ""
}

output "codepipeline_name" {
  description = "Name of the CodePipeline"
  value       = var.enable_deployment_pipeline && var.github_repo_owner != "" && var.github_repo_name != "" ? aws_codepipeline.frontend[0].name : ""
}

output "codepipeline_arn" {
  description = "ARN of the CodePipeline"
  value       = var.enable_deployment_pipeline && var.github_repo_owner != "" && var.github_repo_name != "" ? aws_codepipeline.frontend[0].arn : ""
}

output "artifacts_bucket_name" {
  description = "Name of the S3 bucket for pipeline artifacts"
  value       = var.enable_deployment_pipeline ? aws_s3_bucket.artifacts[0].bucket : ""
}

output "artifacts_bucket_arn" {
  description = "ARN of the S3 bucket for pipeline artifacts"
  value       = var.enable_deployment_pipeline ? aws_s3_bucket.artifacts[0].arn : ""
}

# IAM Role outputs
output "codebuild_role_arn" {
  description = "ARN of the CodeBuild IAM role"
  value       = var.enable_deployment_pipeline ? aws_iam_role.codebuild[0].arn : ""
}

output "codepipeline_role_arn" {
  description = "ARN of the CodePipeline IAM role"
  value       = var.enable_deployment_pipeline ? aws_iam_role.codepipeline[0].arn : ""
}

# Monitoring outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for deployment"
  value       = var.enable_deployment_pipeline ? aws_cloudwatch_log_group.deployment[0].name : ""
}

output "cloudwatch_4xx_alarm_name" {
  description = "Name of the CloudWatch alarm for 4xx errors"
  value       = var.enable_cloudwatch_monitoring ? aws_cloudwatch_metric_alarm.cloudfront_4xx_errors[0].alarm_name : ""
}

output "cloudwatch_5xx_alarm_name" {
  description = "Name of the CloudWatch alarm for 5xx errors"
  value       = var.enable_cloudwatch_monitoring ? aws_cloudwatch_metric_alarm.cloudfront_5xx_errors[0].alarm_name : ""
}

# Configuration summary
output "frontend_hosting_config" {
  description = "Complete frontend hosting configuration"
  value = {
    environment = var.environment
    region      = var.aws_region
    
    s3_bucket = {
      name                = aws_s3_bucket.frontend.bucket
      website_endpoint    = aws_s3_bucket_website_configuration.frontend.website_endpoint
      versioning_enabled  = var.s3_versioning_enabled
    }
    
    cloudfront = {
      distribution_id = aws_cloudfront_distribution.frontend.id
      domain_name     = aws_cloudfront_distribution.frontend.domain_name
      url             = "https://${aws_cloudfront_distribution.frontend.domain_name}"
      custom_domain   = var.domain_name != "" ? "https://${var.domain_name}" : null
      price_class     = var.cloudfront_price_class
    }
    
    deployment = {
      pipeline_enabled = var.enable_deployment_pipeline
      codebuild_project = var.enable_deployment_pipeline ? aws_codebuild_project.frontend[0].name : null
      pipeline_name    = var.enable_deployment_pipeline && var.github_repo_owner != "" && var.github_repo_name != "" ? aws_codepipeline.frontend[0].name : null
      artifacts_bucket = var.enable_deployment_pipeline ? aws_s3_bucket.artifacts[0].bucket : null
    }
    
    monitoring = {
      enabled = var.enable_cloudwatch_monitoring
      log_group = var.enable_deployment_pipeline ? aws_cloudwatch_log_group.deployment[0].name : null
    }
  }
  sensitive = false
}