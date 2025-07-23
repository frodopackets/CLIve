# Frontend Hosting Deployment Guide

This guide covers the deployment of the frontend hosting infrastructure for the AI Assistant CLI application.

## Overview

The frontend hosting module creates:
- **S3 Bucket**: Static website hosting with security configurations
- **CloudFront Distribution**: Global CDN with caching and compression
- **CodePipeline**: Automated deployment from GitHub (optional)
- **CodeBuild**: Build process for React application
- **CloudWatch**: Monitoring and alerting
- **IAM Roles**: Secure access permissions

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform installed** (>= 1.0)
3. **GitHub repository** with frontend code
4. **GitHub Personal Access Token** stored in AWS Secrets Manager (for pipeline)

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
make init ENV=dev
```

### 2. Plan Frontend Infrastructure

```bash
make frontend-plan ENV=dev
```

### 3. Deploy Frontend Infrastructure

```bash
make frontend-apply ENV=dev
```

### 4. Verify Deployment

```bash
# Check outputs
terraform output frontend_cloudfront_distribution_url
terraform output frontend_s3_bucket_name
```

## Configuration

### Environment-Specific Settings

The module supports three environments with different configurations:

#### Development (`dev`)
- **S3**: Force destroy enabled, versioning disabled
- **CloudFront**: PriceClass_100 (US, Canada, Europe)
- **Pipeline**: Uses `develop` branch
- **Monitoring**: Basic monitoring enabled
- **Domain**: Uses CloudFront default domain

#### Staging (`staging`)
- **S3**: Versioning enabled, force destroy disabled
- **CloudFront**: PriceClass_200 (US, Canada, Europe, Asia)
- **Pipeline**: Uses `staging` branch
- **Monitoring**: Full monitoring with alarms
- **Domain**: Optional custom staging domain

#### Production (`prod`)
- **S3**: Versioning enabled, force destroy disabled
- **CloudFront**: PriceClass_All (Global distribution)
- **Pipeline**: Uses `main` branch
- **Monitoring**: Full monitoring with alarms
- **Domain**: Custom production domain with SSL

### Required Configuration Updates

Before deployment, update the following in your environment `.tfvars` files:

```hcl
# GitHub repository settings (required for pipeline)
frontend_github_repo_owner = "your-github-username"
frontend_github_repo_name  = "your-repo-name"

# Custom domain settings (optional)
frontend_domain_name         = "app.yourdomain.com"
frontend_ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."

# WAF settings (recommended for production)
frontend_enable_waf    = true
frontend_waf_web_acl_id = "your-waf-web-acl-id"
```

## Deployment Pipeline Setup

### 1. GitHub Token Configuration

Store your GitHub personal access token in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name github-token \
  --description "GitHub personal access token for CodePipeline" \
  --secret-string '{"token":"your-github-token-here"}'
```

The token needs the following permissions:
- `repo` (Full control of private repositories)
- `admin:repo_hook` (Admin access to repository hooks)

### 2. Buildspec Configuration

Ensure your `frontend/buildspec.yml` is properly configured:

```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - cd frontend
      - npm ci
  build:
    commands:
      - npm run build
  post_build:
    commands:
      - aws s3 sync dist/ s3://$S3_BUCKET/ --delete
      - aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
```

### 3. Pipeline Execution

The pipeline automatically triggers on commits to the configured branch:

1. **Source Stage**: Pulls code from GitHub
2. **Build Stage**: Runs `npm ci` and `npm run build`
3. **Deploy Stage**: Syncs files to S3 and invalidates CloudFront

## Custom Domain Setup

### 1. SSL Certificate

Request an SSL certificate in AWS Certificate Manager (ACM):

```bash
aws acm request-certificate \
  --domain-name app.yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

**Important**: The certificate must be in `us-east-1` region for CloudFront.

### 2. DNS Configuration

After deployment, create a CNAME record pointing to the CloudFront distribution:

```
app.yourdomain.com -> d123456789.cloudfront.net
```

### 3. Update Configuration

Update your environment `.tfvars` file:

```hcl
frontend_domain_name         = "app.yourdomain.com"
frontend_ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
```

Then redeploy:

```bash
make frontend-apply ENV=prod
```

## Monitoring and Troubleshooting

### CloudWatch Alarms

The module creates alarms for:
- **4xx Error Rate**: Threshold 5% (client errors)
- **5xx Error Rate**: Threshold 1% (server errors)

### Logs

- **CodeBuild Logs**: `/aws/codebuild/{project-name}-frontend-build`
- **CloudFront Logs**: Optional, can be enabled in CloudFront settings

### Common Issues

#### Pipeline Fails with GitHub Authentication
- Verify GitHub token is stored in Secrets Manager as `github-token`
- Check token permissions include `repo` scope
- Ensure repository owner/name are correct in tfvars

#### Build Fails
- Check `buildspec.yml` syntax and commands
- Verify Node.js version compatibility
- Check build output directory matches `build_output_dir` variable

#### CloudFront 403 Errors
- Verify S3 bucket policy allows CloudFront access
- Check Origin Access Control (OAC) configuration
- Ensure `index.html` exists in build output

#### Custom Domain Not Working
- Verify SSL certificate is in `us-east-1` region
- Check DNS CNAME record points to CloudFront distribution
- Wait for DNS propagation (up to 48 hours)

## Security Best Practices

### S3 Security
- ✅ Public access blocked by default
- ✅ Server-side encryption enabled
- ✅ Access only through CloudFront OAC
- ✅ Bucket policy restricts access to CloudFront

### CloudFront Security
- ✅ HTTPS redirect enforced
- ✅ Security headers can be added via Lambda@Edge
- ✅ WAF integration available
- ✅ Origin access control prevents direct S3 access

### Pipeline Security
- ✅ Least privilege IAM roles
- ✅ Encrypted artifacts bucket
- ✅ Secure GitHub token storage
- ✅ Build environment isolation

## Cost Optimization

### CloudFront Price Classes
- **PriceClass_100**: US, Canada, Europe (~$0.085/GB)
- **PriceClass_200**: Above + Asia Pacific (~$0.120/GB)
- **PriceClass_All**: Global distribution (~$0.170/GB)

### S3 Storage
- Use S3 Intelligent Tiering for cost optimization
- Enable lifecycle policies for old versions
- Consider S3 Transfer Acceleration for uploads

### Monitoring Costs
- Adjust log retention periods based on compliance needs
- Use CloudWatch cost allocation tags
- Monitor data transfer costs

## Testing

### Infrastructure Tests

Run Terratest-based infrastructure tests:

```bash
# Initialize test dependencies
make test-init

# Run all frontend tests
make test-frontend

# Run specific test
cd tests && go test -v -run TestFrontendHostingModule
```

### Manual Testing

1. **Basic Functionality**:
   ```bash
   curl -I https://$(terraform output -raw frontend_cloudfront_distribution_url)
   ```

2. **Custom Domain** (if configured):
   ```bash
   curl -I https://app.yourdomain.com
   ```

3. **Pipeline Testing**:
   - Push changes to configured branch
   - Monitor CodePipeline execution in AWS Console
   - Verify changes appear on website

## Cleanup

### Destroy Frontend Infrastructure

```bash
make frontend-destroy ENV=dev
```

### Complete Cleanup

```bash
# Destroy all infrastructure
make destroy ENV=dev

# Clean local files
make clean
```

**Warning**: This will permanently delete all resources including S3 buckets and their contents.

## Support and Troubleshooting

### Useful Commands

```bash
# Check Terraform state
terraform state list | grep frontend

# View specific resource
terraform state show module.frontend_hosting.aws_s3_bucket.frontend

# Import existing resource (if needed)
terraform import module.frontend_hosting.aws_s3_bucket.frontend bucket-name

# Refresh state
terraform refresh -var-file=environments/dev.tfvars
```

### AWS Console Resources

Monitor these AWS services:
- **S3**: Bucket contents and configuration
- **CloudFront**: Distribution status and metrics
- **CodePipeline**: Pipeline execution history
- **CodeBuild**: Build logs and history
- **CloudWatch**: Metrics and alarms
- **IAM**: Roles and policies

### Getting Help

1. Check the module README: `terraform/modules/frontend-hosting/README.md`
2. Review Terraform documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
3. AWS documentation for specific services
4. Run validation script: `./scripts/validate-frontend-hosting.sh`