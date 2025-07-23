# AI Assistant CLI - Deployment Guide

This document provides comprehensive instructions for deploying the AI Assistant CLI solution to AWS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [AWS Services Setup](#aws-services-setup)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Configuration](#configuration)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- AWS CLI v2.x configured with appropriate permissions
- Terraform >= 1.0
- Docker and Docker Compose
- Node.js >= 18.x
- Python >= 3.12
- Git

### AWS Permissions
The deployment requires the following AWS permissions:
- IAM: Full access for role and policy management
- EC2: Full access for VPC, security groups, and instances
- ECS: Full access for container orchestration
- ALB: Full access for load balancer management
- Route53: Full access for DNS management
- CloudFront: Full access for CDN
- S3: Full access for static hosting and storage
- DynamoDB: Full access for session storage
- Bedrock: Full access for AI model access
- CloudWatch: Full access for logging and monitoring
- AWS Identity Center: Admin access for authentication setup

## Architecture Overview

The solution consists of:
- **Frontend**: React TypeScript application hosted on S3 + CloudFront
- **Backend**: FastAPI application running on ECS Fargate
- **Authentication**: AWS Identity Center (SSO)
- **AI Services**: AWS Bedrock (Nova Pro model)
- **Knowledge Base**: AWS Bedrock Knowledge Bases
- **Session Storage**: DynamoDB
- **Agent Integration**: Birmingham weather/time agent
- **Load Balancer**: Application Load Balancer with WebSocket support
- **Monitoring**: CloudWatch Logs and Metrics

## AWS Services Setup

### 1. AWS Identity Center Configuration

```bash
# Enable AWS Identity Center in your AWS account
aws sso-admin list-instances

# Create permission sets for the application
aws sso-admin create-permission-set \
    --instance-arn "arn:aws:sso:::instance/ssoins-xxxxxxxxxx" \
    --name "AIAssistantCLIUsers" \
    --description "Permission set for AI Assistant CLI users"
```

### 2. Bedrock Model Access

```bash
# Request access to Nova Pro model in Bedrock
aws bedrock get-foundation-model \
    --model-identifier "amazon.nova-pro-v1:0" \
    --region us-east-1

# Enable model access if not already enabled
aws bedrock put-model-invocation-logging-configuration \
    --logging-config '{"cloudWatchConfig":{"logGroupName":"/aws/bedrock/modelinvocations","roleArn":"arn:aws:iam::ACCOUNT:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_XXXXX"}}'
```

### 3. Knowledge Base Setup

```bash
# Create S3 bucket for knowledge base documents
aws s3 mb s3://ai-assistant-cli-knowledge-base-ACCOUNT-REGION

# Create knowledge base (this requires manual setup in AWS Console)
# Navigate to Bedrock > Knowledge bases > Create knowledge base
```

## Infrastructure Deployment

### 1. Terraform Infrastructure

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
aws_region = "us-east-1"
environment = "production"
domain_name = "your-domain.com"
certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"
identity_center_instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxx"
bedrock_model_id = "amazon.nova-pro-v1:0"
knowledge_base_id = "XXXXXXXXXX"
EOF

# Plan deployment
terraform plan

# Deploy infrastructure
terraform apply
```

### 2. VPC and Networking

The Terraform configuration creates:
- VPC with public and private subnets across 2 AZs
- Internet Gateway and NAT Gateways
- Security Groups for ALB and ECS
- Route tables and associations

### 3. ECS Cluster Setup

```bash
# ECS cluster is created via Terraform
# Verify cluster creation
aws ecs describe-clusters --clusters ai-assistant-cli-cluster
```

## Backend Deployment

### 1. Container Image Build

```bash
# Navigate to backend directory
cd backend

# Build Docker image
docker build -t ai-assistant-cli-backend:latest .

# Tag for ECR
docker tag ai-assistant-cli-backend:latest \
    ACCOUNT.dkr.ecr.REGION.amazonaws.com/ai-assistant-cli-backend:latest

# Push to ECR
aws ecr get-login-password --region REGION | \
    docker login --username AWS --password-stdin \
    ACCOUNT.dkr.ecr.REGION.amazonaws.com

docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/ai-assistant-cli-backend:latest
```

### 2. ECS Service Deployment

```bash
# Update ECS service with new image
aws ecs update-service \
    --cluster ai-assistant-cli-cluster \
    --service ai-assistant-cli-backend \
    --force-new-deployment
```

### 3. Environment Variables

Set the following environment variables in ECS task definition:

```json
{
  "environment": [
    {
      "name": "AWS_REGION",
      "value": "us-east-1"
    },
    {
      "name": "BEDROCK_MODEL_ID",
      "value": "amazon.nova-pro-v1:0"
    },
    {
      "name": "BEDROCK_REGION",
      "value": "us-east-1"
    },
    {
      "name": "DYNAMODB_SESSIONS_TABLE",
      "value": "ai-assistant-sessions"
    },
    {
      "name": "JWT_SECRET",
      "value": "your-jwt-secret"
    },
    {
      "name": "JWT_ISSUER",
      "value": "aws-identity-center"
    },
    {
      "name": "LOG_LEVEL",
      "value": "INFO"
    }
  ]
}
```

## Frontend Deployment

### 1. Build Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
VITE_API_URL=https://api.your-domain.com
VITE_WEBSOCKET_URL=wss://api.your-domain.com
VITE_AUTH_AUTHORITY=https://portal.sso.us-east-1.amazonaws.com
VITE_AUTH_CLIENT_ID=your-client-id
VITE_AUTH_REDIRECT_URI=https://your-domain.com/callback
VITE_AUTH_POST_LOGOUT_REDIRECT_URI=https://your-domain.com
EOF

# Build for production
npm run build
```

### 2. Deploy to S3

```bash
# Sync build files to S3
aws s3 sync dist/ s3://ai-assistant-cli-frontend-ACCOUNT-REGION/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "*.html" \
    --exclude "service-worker.js"

# Upload HTML files with shorter cache
aws s3 sync dist/ s3://ai-assistant-cli-frontend-ACCOUNT-REGION/ \
    --delete \
    --cache-control "public, max-age=0, must-revalidate" \
    --include "*.html" \
    --include "service-worker.js"
```

### 3. CloudFront Invalidation

```bash
# Create CloudFront invalidation
aws cloudfront create-invalidation \
    --distribution-id DISTRIBUTION-ID \
    --paths "/*"
```

## Configuration

### 1. DNS Configuration

```bash
# Create Route53 hosted zone (if not exists)
aws route53 create-hosted-zone \
    --name your-domain.com \
    --caller-reference $(date +%s)

# Update domain registrar with Route53 name servers
```

### 2. SSL Certificate

```bash
# Request SSL certificate via ACM
aws acm request-certificate \
    --domain-name your-domain.com \
    --subject-alternative-names "*.your-domain.com" \
    --validation-method DNS \
    --region us-east-1
```

### 3. Identity Center Application

1. Navigate to AWS Identity Center console
2. Go to Applications > Add application
3. Select "Custom SAML 2.0 application"
4. Configure with your domain URLs
5. Assign users and groups

## Monitoring and Logging

### 1. CloudWatch Logs

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/ai-assistant-cli-backend
aws logs create-log-group --log-group-name /aws/bedrock/modelinvocations
aws logs create-log-group --log-group-name /aws/lambda/ai-assistant-cli
```

### 2. CloudWatch Metrics

Key metrics to monitor:
- ECS service CPU and memory utilization
- ALB request count and latency
- DynamoDB read/write capacity
- Bedrock model invocation count and latency
- CloudFront cache hit ratio

### 3. Alarms

```bash
# Create CloudWatch alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "AI-Assistant-CLI-High-CPU" \
    --alarm-description "High CPU utilization" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

## Security Considerations

### 1. IAM Roles and Policies

- ECS Task Role: Minimal permissions for Bedrock, DynamoDB, and CloudWatch
- ECS Execution Role: Permissions for ECR and CloudWatch Logs
- Lambda Execution Role: Permissions for specific functions

### 2. Security Groups

- ALB Security Group: Allow HTTP/HTTPS from internet
- ECS Security Group: Allow traffic only from ALB
- Database Security Group: Allow traffic only from ECS

### 3. Secrets Management

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "ai-assistant-cli/jwt-secret" \
    --description "JWT secret for AI Assistant CLI" \
    --secret-string "your-secure-jwt-secret"
```

### 4. WAF Configuration

```bash
# Create WAF web ACL
aws wafv2 create-web-acl \
    --name ai-assistant-cli-waf \
    --scope CLOUDFRONT \
    --default-action Allow={} \
    --rules file://waf-rules.json
```

## CI/CD Pipeline

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy AI Assistant CLI

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker image
        run: |
          cd backend
          docker build -t ai-assistant-cli-backend .
          # Push to ECR and update ECS service
  
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Build and deploy frontend
        run: |
          cd frontend
          npm ci
          npm run build
          aws s3 sync dist/ s3://your-frontend-bucket/
```

### 2. Terraform State Management

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://ai-assistant-cli-terraform-state-ACCOUNT-REGION

# Configure backend in Terraform
terraform {
  backend "s3" {
    bucket = "ai-assistant-cli-terraform-state-ACCOUNT-REGION"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Troubleshooting

### Common Issues

1. **ECS Service Won't Start**
   - Check CloudWatch logs for container errors
   - Verify IAM permissions
   - Check security group configurations

2. **WebSocket Connection Fails**
   - Verify ALB target group health
   - Check WebSocket upgrade headers
   - Verify security group allows WebSocket traffic

3. **Bedrock Access Denied**
   - Ensure model access is enabled in Bedrock console
   - Verify IAM permissions for Bedrock
   - Check region availability

4. **Frontend Authentication Issues**
   - Verify Identity Center configuration
   - Check CORS settings on backend
   - Validate JWT configuration

### Debugging Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster ai-assistant-cli-cluster --services ai-assistant-cli-backend

# View CloudWatch logs
aws logs tail /ecs/ai-assistant-cli-backend --follow

# Test backend health
curl https://api.your-domain.com/api/v1/health

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn TARGET-GROUP-ARN
```

## Scaling Considerations

### Auto Scaling

```bash
# Configure ECS service auto scaling
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/ai-assistant-cli-cluster/ai-assistant-cli-backend \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10
```

### Performance Optimization

1. **Backend Scaling**
   - Configure ECS auto scaling based on CPU/memory
   - Use multiple AZs for high availability
   - Implement connection pooling for DynamoDB

2. **Frontend Optimization**
   - Enable CloudFront compression
   - Configure appropriate cache headers
   - Use CloudFront edge locations

3. **Database Optimization**
   - Configure DynamoDB auto scaling
   - Use appropriate partition keys
   - Implement read replicas if needed

## Cost Optimization

1. **ECS Fargate Spot Instances**: Use for non-critical workloads
2. **S3 Intelligent Tiering**: For knowledge base documents
3. **CloudWatch Log Retention**: Set appropriate retention periods
4. **Reserved Capacity**: For predictable workloads

## Backup and Disaster Recovery

1. **DynamoDB Backups**: Enable point-in-time recovery
2. **S3 Cross-Region Replication**: For knowledge base documents
3. **Infrastructure as Code**: Terraform for quick recovery
4. **Database Snapshots**: Regular automated backups

This deployment guide provides a comprehensive approach to deploying the AI Assistant CLI solution to AWS with proper security, monitoring, and scalability considerations.