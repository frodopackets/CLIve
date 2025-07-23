# Frontend Hosting Module

This Terraform module creates the infrastructure for hosting a static frontend application using Amazon S3 and CloudFront. It includes optional deployment pipeline capabilities using AWS CodeBuild and CodePipeline.

## Features

- **S3 Static Website Hosting**: Secure S3 bucket with website configuration
- **CloudFront Distribution**: Global content delivery with caching and compression
- **Origin Access Control (OAC)**: Secure access from CloudFront to S3
- **Custom Domain Support**: Optional custom domain with SSL/TLS certificates
- **Deployment Pipeline**: Optional CI/CD pipeline with GitHub integration
- **Security**: WAF integration, encryption at rest, and public access blocking
- **Monitoring**: CloudWatch alarms and logging for operational visibility

## Usage

### Basic Usage

```hcl
module "frontend_hosting" {
  source = "./modules/frontend-hosting"
  
  project_name = "my-app"
  environment  = "prod"
  aws_region   = "us-east-1"
  
  tags = {
    Environment = "prod"
    Project     = "my-app"
  }
}
```

### With Custom Domain

```hcl
module "frontend_hosting" {
  source = "./modules/frontend-hosting"
  
  project_name = "my-app"
  environment  = "prod"
  aws_region   = "us-east-1"
  
  # Custom domain configuration
  domain_name         = "app.example.com"
  domain_aliases      = ["www.app.example.com"]
  ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  
  tags = {
    Environment = "prod"
    Project     = "my-app"
  }
}
```

### With Deployment Pipeline

```hcl
module "frontend_hosting" {
  source = "./modules/frontend-hosting"
  
  project_name = "my-app"
  environment  = "prod"
  aws_region   = "us-east-1"
  
  # Deployment pipeline configuration
  enable_deployment_pipeline = true
  github_repo_owner          = "my-org"
  github_repo_name           = "my-app"
  github_branch              = "main"
  build_spec_path            = "frontend/buildspec.yml"
  build_output_dir           = "frontend/dist"
  
  tags = {
    Environment = "prod"
    Project     = "my-app"
  }
}
```

### With WAF Protection

```hcl
module "frontend_hosting" {
  source = "./modules/frontend-hosting"
  
  project_name = "my-app"
  environment  = "prod"
  aws_region   = "us-east-1"
  
  # Security configuration
  enable_waf      = true
  waf_web_acl_id  = "12345678-1234-1234-1234-123456789012"
  
  tags = {
    Environment = "prod"
    Project     = "my-app"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| awscc | ~> 0.70 |
| aws | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| awscc | ~> 0.70 |
| aws | ~> 5.0 |
| random | n/a |

## Resources

### S3 Resources
- `aws_s3_bucket` - Main frontend hosting bucket
- `aws_s3_bucket_versioning` - Bucket versioning configuration
- `aws_s3_bucket_server_side_encryption_configuration` - Bucket encryption
- `aws_s3_bucket_public_access_block` - Public access blocking
- `aws_s3_bucket_website_configuration` - Website hosting configuration
- `aws_s3_bucket_policy` - Bucket policy for CloudFront access
- `aws_s3_bucket` - Artifacts bucket (if pipeline enabled)

### CloudFront Resources
- `aws_cloudfront_origin_access_control` - Origin access control
- `aws_cloudfront_distribution` - Content delivery network

### Deployment Pipeline Resources (Optional)
- `aws_codebuild_project` - Build project for frontend
- `aws_codepipeline` - Deployment pipeline
- `aws_iam_role` - IAM roles for CodeBuild and CodePipeline
- `aws_iam_role_policy` - IAM policies for pipeline permissions

### Monitoring Resources (Optional)
- `aws_cloudwatch_log_group` - Log group for deployment logs
- `aws_cloudwatch_metric_alarm` - CloudFront error rate alarms

## Inputs

### Required Variables

| Name | Description | Type |
|------|-------------|------|
| project_name | Name of the project | `string` |
| environment | Environment name (dev, staging, prod) | `string` |
| aws_region | AWS region for resources | `string` |
| tags | Common tags for all resources | `map(string)` |

### Optional Variables

#### S3 Configuration
| Name | Description | Type | Default |
|------|-------------|------|---------|
| s3_bucket_name | Name of the S3 bucket (auto-generated if empty) | `string` | `""` |
| s3_force_destroy | Force destroy S3 bucket even if it contains objects | `bool` | `false` |
| s3_versioning_enabled | Enable versioning on S3 bucket | `bool` | `true` |

#### CloudFront Configuration
| Name | Description | Type | Default |
|------|-------------|------|---------|
| cloudfront_price_class | Price class for CloudFront distribution | `string` | `"PriceClass_100"` |
| cloudfront_default_root_object | Default root object for CloudFront | `string` | `"index.html"` |
| cloudfront_custom_error_responses | Custom error responses for SPA routing | `list(object)` | See variables.tf |
| cloudfront_cache_behaviors | Additional cache behaviors | `list(object)` | See variables.tf |

#### Domain Configuration
| Name | Description | Type | Default |
|------|-------------|------|---------|
| ssl_certificate_arn | ARN of SSL certificate for custom domain | `string` | `""` |
| domain_name | Custom domain name | `string` | `""` |
| domain_aliases | Additional domain aliases | `list(string)` | `[]` |

#### Security Configuration
| Name | Description | Type | Default |
|------|-------------|------|---------|
| enable_waf | Enable AWS WAF for CloudFront | `bool` | `false` |
| waf_web_acl_id | ID of WAF Web ACL | `string` | `""` |

#### Deployment Configuration
| Name | Description | Type | Default |
|------|-------------|------|---------|
| enable_deployment_pipeline | Enable CodePipeline for deployment | `bool` | `true` |
| github_repo_owner | GitHub repository owner | `string` | `""` |
| github_repo_name | GitHub repository name | `string` | `""` |
| github_branch | GitHub branch for deployment | `string` | `"main"` |
| build_spec_path | Path to buildspec.yml file | `string` | `"frontend/buildspec.yml"` |
| source_dir | Source directory for frontend files | `string` | `"frontend/"` |
| build_output_dir | Build output directory | `string` | `"frontend/dist"` |

#### Monitoring Configuration
| Name | Description | Type | Default |
|------|-------------|------|---------|
| enable_cloudwatch_monitoring | Enable CloudWatch monitoring | `bool` | `true` |
| log_retention_days | CloudWatch log retention in days | `number` | `30` |
| alarm_actions | List of ARNs to notify when alarms trigger | `list(string)` | `[]` |

## Outputs

### S3 Outputs
| Name | Description |
|------|-------------|
| s3_bucket_name | Name of the S3 bucket |
| s3_bucket_arn | ARN of the S3 bucket |
| s3_website_endpoint | Website endpoint of the S3 bucket |

### CloudFront Outputs
| Name | Description |
|------|-------------|
| cloudfront_distribution_id | ID of the CloudFront distribution |
| cloudfront_distribution_arn | ARN of the CloudFront distribution |
| cloudfront_domain_name | Domain name of the CloudFront distribution |
| cloudfront_distribution_url | HTTPS URL of the CloudFront distribution |

### Domain Outputs
| Name | Description |
|------|-------------|
| custom_domain_url | Custom domain URL (if configured) |
| domain_aliases | List of configured domain aliases |

### Deployment Pipeline Outputs
| Name | Description |
|------|-------------|
| codebuild_project_name | Name of the CodeBuild project |
| codepipeline_name | Name of the CodePipeline |
| artifacts_bucket_name | Name of the artifacts S3 bucket |

### Configuration Summary
| Name | Description |
|------|-------------|
| frontend_hosting_config | Complete configuration object with all settings |

## Deployment Pipeline

The module can optionally create a CI/CD pipeline using AWS CodePipeline and CodeBuild. The pipeline:

1. **Source Stage**: Pulls code from GitHub repository
2. **Build Stage**: Runs the build process using the provided buildspec.yml
3. **Deploy Stage**: Syncs built files to S3 and invalidates CloudFront cache

### Buildspec Requirements

Your `buildspec.yml` file should:
- Install dependencies (e.g., `npm ci`)
- Build the application (e.g., `npm run build`)
- The build output should be in the directory specified by `build_output_dir`

Example buildspec.yml structure:
```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - npm ci
  build:
    commands:
      - npm run build
  post_build:
    commands:
      - aws s3 sync $BUILD_OUTPUT_DIR/ s3://$S3_BUCKET/ --delete
      - aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
```

### GitHub Integration

To use the deployment pipeline:
1. Store your GitHub personal access token in AWS Secrets Manager with the name `github-token`
2. The token should have `repo` permissions for the specified repository
3. Configure the `github_repo_owner`, `github_repo_name`, and `github_branch` variables

## Security Considerations

### S3 Security
- Public access is blocked by default
- Server-side encryption (AES256) is enabled
- Access is only allowed through CloudFront via Origin Access Control

### CloudFront Security
- HTTPS redirect is enforced
- Optional WAF integration for additional protection
- Custom SSL certificates supported for custom domains

### IAM Security
- Least privilege IAM roles for CodeBuild and CodePipeline
- Specific resource-based permissions
- No overly broad permissions granted

## Monitoring and Alerting

The module creates CloudWatch alarms for:
- 4xx error rate (threshold: 5%)
- 5xx error rate (threshold: 1%)

Deployment logs are stored in CloudWatch Logs with configurable retention.

## Cost Optimization

- S3 storage class optimization can be configured
- CloudFront price class can be adjusted based on global reach requirements
- Log retention periods can be tuned for cost vs. compliance needs
- Versioning can be disabled in non-production environments

## Testing

The module includes comprehensive tests using Terratest:

```bash
# Run all tests
make test

# Run only frontend hosting tests
make test-frontend

# Initialize test dependencies
make test-init
```

Tests cover:
- Resource creation and configuration
- Security settings validation
- Output value verification
- Custom domain configuration
- Deployment pipeline functionality

## Examples

See the `examples/` directory for complete usage examples:
- Basic static website hosting
- Custom domain with SSL
- Full CI/CD pipeline setup
- Multi-environment configuration