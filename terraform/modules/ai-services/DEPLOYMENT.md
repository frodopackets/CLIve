# AI Services Module Deployment Guide

## Overview

This document provides deployment instructions for the AI Services Terraform module, which creates the infrastructure for AWS Bedrock services and Knowledge Base functionality.

## Prerequisites

1. **AWS Account Setup**:
   - AWS CLI configured with appropriate credentials
   - Bedrock service enabled in your AWS account
   - Required Bedrock models enabled (Nova Pro, Nova Lite, Titan Embed)

2. **Terraform Setup**:
   - Terraform >= 1.0 installed
   - AWS provider >= 5.0
   - AWSCC provider >= 0.70

3. **Permissions Required**:
   - IAM permissions to create roles and policies
   - S3 permissions for bucket creation
   - Bedrock permissions for Knowledge Base creation
   - OpenSearch Serverless permissions
   - CloudWatch permissions for logging and monitoring

## Deployment Steps

### 1. Enable Bedrock Models

Before deploying, ensure the required Bedrock models are enabled in your AWS account:

```bash
# Check available models
aws bedrock list-foundation-models --region us-east-1

# Enable models if needed (through AWS Console)
# - amazon.nova-pro-v1:0
# - amazon.nova-lite-v1:0  
# - amazon.titan-embed-text-v2:0
```

### 2. Deploy Infrastructure

From the main terraform directory:

```bash
# Initialize Terraform
terraform init -backend-config=environments/dev-backend.hcl

# Plan deployment
terraform plan -var-file=environments/dev.tfvars

# Apply changes
terraform apply -var-file=environments/dev.tfvars
```

### 3. Verify Deployment

After deployment, verify the resources:

```bash
# Check Knowledge Base
aws bedrock list-knowledge-bases --region us-east-1

# Check S3 bucket
aws s3 ls | grep knowledge-base-data

# Check OpenSearch collection
aws opensearchserverless list-collections --region us-east-1
```

## Configuration Options

### Environment-Specific Settings

#### Development
- Log retention: 7 days
- Basic monitoring
- Cost-optimized settings

#### Staging  
- Log retention: 30 days
- Enhanced monitoring
- Production-like configuration

#### Production
- Log retention: 90 days
- Full monitoring and alerting
- High availability configuration

### Customization Variables

Key variables you can customize:

```hcl
# Model configuration
bedrock_models = [
  "amazon.nova-pro-v1:0",
  "amazon.nova-lite-v1:0"
]

# Knowledge Base settings
knowledge_base_embedding_model = "amazon.titan-embed-text-v2:0"
knowledge_base_chunk_size = 300
knowledge_base_chunk_overlap = 20

# Monitoring
log_retention_days = 30
alarm_actions = ["arn:aws:sns:us-east-1:123456789012:alerts"]
```

## Post-Deployment Setup

### 1. Upload Knowledge Base Documents

Upload documents to the S3 bucket under the `documents/` prefix:

```bash
# Get bucket name from Terraform output
BUCKET_NAME=$(terraform output -raw knowledge_base_s3_bucket_name)

# Upload documents
aws s3 cp ./docs/ s3://$BUCKET_NAME/documents/ --recursive
```

### 2. Sync Knowledge Base

After uploading documents, sync the Knowledge Base:

```bash
# Get Knowledge Base ID
KB_ID=$(terraform output -raw knowledge_base_id)

# Start ingestion job
aws bedrock start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id <data-source-id>
```

### 3. Test AI Services

Test the deployed services:

```bash
# Test Bedrock model access
aws bedrock invoke-model \
  --model-id amazon.nova-lite-v1:0 \
  --body '{"inputText":"Hello, world!","textGenerationConfig":{"maxTokenCount":100}}' \
  --content-type application/json \
  --accept application/json \
  output.json

# Test Knowledge Base retrieval
aws bedrock retrieve-and-generate \
  --retrieval-configuration '{"vectorSearchConfiguration":{"knowledgeBaseId":"'$KB_ID'"}}' \
  --input '{"text":"What is this about?"}'
```

## Monitoring and Maintenance

### CloudWatch Dashboards

The module creates CloudWatch alarms for:
- Bedrock error rates
- Bedrock throttling
- Knowledge Base sync failures

### Log Groups

Monitor these log groups:
- `/aws/bedrock/{project-name}-{environment}`
- `/aws/bedrock/knowledge-base/{project-name}-{environment}`

### Cost Monitoring

Key cost components:
- OpenSearch Serverless collection
- Bedrock model invocations
- S3 storage for documents
- CloudWatch logs storage

## Troubleshooting

### Common Issues

1. **Knowledge Base Creation Fails**
   - Verify IAM permissions
   - Check OpenSearch collection status
   - Ensure embedding model is enabled

2. **Document Ingestion Fails**
   - Check S3 bucket permissions
   - Verify document format (PDF, TXT, DOCX)
   - Check document size limits

3. **Model Access Denied**
   - Verify Bedrock models are enabled
   - Check IAM role permissions
   - Confirm model IDs are correct

### Debug Commands

```bash
# Check IAM role trust relationships
aws iam get-role --role-name {project-name}-{environment}-bedrock-kb-role

# Check OpenSearch collection status
aws opensearchserverless batch-get-collection --names {collection-name}

# Check Knowledge Base status
aws bedrock get-knowledge-base --knowledge-base-id $KB_ID
```

## Security Considerations

1. **IAM Roles**: Follow least privilege principle
2. **S3 Bucket**: Public access blocked by default
3. **Encryption**: Server-side encryption enabled
4. **Network**: Resources deployed in private subnets
5. **Monitoring**: CloudWatch alarms for security events

## Cleanup

To destroy the infrastructure:

```bash
# Empty S3 bucket first (if needed)
aws s3 rm s3://$BUCKET_NAME --recursive

# Destroy infrastructure
terraform destroy -var-file=environments/dev.tfvars
```

## Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review AWS Bedrock documentation
3. Consult Terraform AWS provider documentation
4. Contact the development team