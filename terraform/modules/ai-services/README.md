# AI Services Terraform Module

This module creates the AWS infrastructure required for AI services in the AI Assistant CLI application, including Bedrock services, Knowledge Base infrastructure, and associated IAM roles and policies.

## Features

- **AWS Bedrock Integration**: Configures access to Bedrock models (Nova Pro, Nova Lite)
- **Knowledge Base**: Sets up Bedrock Knowledge Base with OpenSearch Serverless for vector storage
- **S3 Data Source**: Creates S3 bucket for knowledge base document storage
- **IAM Roles and Policies**: Comprehensive IAM setup for secure access to AI services
- **Monitoring**: CloudWatch logs and alarms for Bedrock usage monitoring
- **Security**: Proper encryption, access controls, and security policies

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Lambda        │    │   Bedrock        │    │   Knowledge Base    │
│   Functions     │───▶│   Nova Pro/Lite  │    │   (OpenSearch)      │
│                 │    │   Models         │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │                        │
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   IAM Roles     │    │   CloudWatch     │    │   S3 Bucket         │
│   & Policies    │    │   Monitoring     │    │   (Data Source)     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## Usage

```hcl
module "ai_services" {
  source = "./modules/ai-services"
  
  project_name             = "ai-assistant-cli"
  environment              = "dev"
  aws_region               = "us-east-1"
  vpc_id                   = module.networking.vpc_id
  private_subnet_ids       = module.networking.private_subnet_ids
  lambda_security_group_id = module.security.lambda_security_group_id
  
  # Optional configurations
  log_retention_days                = 30
  knowledge_base_embedding_model    = "amazon.titan-embed-text-v2:0"
  knowledge_base_chunking_strategy  = "FIXED_SIZE"
  knowledge_base_chunk_size         = 300
  knowledge_base_chunk_overlap      = 20
  
  bedrock_models = [
    "amazon.nova-pro-v1:0",
    "amazon.nova-lite-v1:0"
  ]
  
  tags = {
    Environment = "dev"
    Project     = "ai-assistant-cli"
    ManagedBy   = "terraform"
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

## Resources Created

### Core AI Services
- `awscc_bedrock_knowledge_base.main` - Bedrock Knowledge Base
- `awscc_bedrock_data_source.main` - S3 data source for knowledge base
- `awscc_opensearchserverless_collection.knowledge_base_vector_store` - Vector storage

### Storage
- `aws_s3_bucket.knowledge_base_data` - S3 bucket for knowledge base documents
- S3 bucket configuration (versioning, encryption, public access block)

### Security
- `awscc_opensearchserverless_security_policy` - Encryption and network policies
- `awscc_opensearchserverless_access_policy` - Data access policy
- `aws_iam_role.bedrock_knowledge_base_role` - IAM role for Bedrock Knowledge Base
- `aws_iam_role.lambda_bedrock_role` - IAM role for Lambda functions
- Associated IAM policies for secure access

### Monitoring
- `aws_cloudwatch_log_group` - Log groups for Bedrock API and Knowledge Base
- `aws_cloudwatch_metric_alarm` - Alarms for error rate and throttling

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_name | Name of the project | `string` | n/a | yes |
| environment | Environment name (dev, staging, prod) | `string` | n/a | yes |
| aws_region | AWS region for resources | `string` | n/a | yes |
| vpc_id | VPC ID for resources that need VPC placement | `string` | n/a | yes |
| private_subnet_ids | Private subnet IDs for Lambda functions | `list(string)` | n/a | yes |
| lambda_security_group_id | Security group ID for Lambda functions | `string` | n/a | yes |
| tags | Common tags for all resources | `map(string)` | `{}` | no |
| log_retention_days | CloudWatch log retention in days | `number` | `30` | no |
| alarm_actions | List of ARNs to notify when alarm triggers | `list(string)` | `[]` | no |
| knowledge_base_embedding_model | Bedrock embedding model for knowledge base | `string` | `"amazon.titan-embed-text-v2:0"` | no |
| bedrock_models | List of Bedrock models to grant access to | `list(string)` | `["amazon.nova-pro-v1:0", "amazon.nova-lite-v1:0"]` | no |
| enable_bedrock_logging | Enable CloudWatch logging for Bedrock API calls | `bool` | `true` | no |
| knowledge_base_chunking_strategy | Chunking strategy for knowledge base documents | `string` | `"FIXED_SIZE"` | no |
| knowledge_base_chunk_size | Size of chunks for knowledge base documents | `number` | `300` | no |
| knowledge_base_chunk_overlap | Overlap between chunks for knowledge base documents | `number` | `20` | no |

## Outputs

| Name | Description |
|------|-------------|
| knowledge_base_id | ID of the Bedrock Knowledge Base |
| knowledge_base_arn | ARN of the Bedrock Knowledge Base |
| knowledge_base_s3_bucket_name | Name of the S3 bucket for knowledge base data sources |
| opensearch_collection_endpoint | Endpoint of the OpenSearch Serverless collection |
| bedrock_knowledge_base_role_arn | ARN of the IAM role for Bedrock Knowledge Base |
| lambda_bedrock_role_arn | ARN of the IAM role for Lambda functions to access Bedrock |
| ai_services_config | Configuration object for AI services |

## Testing

### Validation Script
Run the validation script to test the module:

```bash
./validate.sh
```

### Go Tests
Run the Go-based integration tests:

```bash
cd tests
go test -v -timeout 30m
```

## Security Considerations

1. **IAM Least Privilege**: All IAM roles follow the principle of least privilege
2. **Encryption**: S3 bucket uses server-side encryption
3. **Network Security**: OpenSearch Serverless uses proper security policies
4. **Access Control**: Bedrock access is restricted to specific models and operations
5. **Monitoring**: CloudWatch alarms monitor for errors and throttling

## Cost Optimization

1. **OpenSearch Serverless**: Uses serverless model for cost efficiency
2. **S3 Storage**: Standard storage class with lifecycle policies
3. **CloudWatch Logs**: Configurable retention periods
4. **Bedrock Models**: Access limited to required models only

## Troubleshooting

### Common Issues

1. **OpenSearch Collection Creation**: May take several minutes to complete
2. **IAM Role Propagation**: Allow time for IAM roles to propagate before use
3. **Knowledge Base Sync**: Initial data source sync may take time
4. **Model Access**: Ensure Bedrock models are enabled in your AWS account

### Debugging

1. Check CloudWatch logs for detailed error messages
2. Verify IAM permissions using AWS CLI
3. Test Bedrock model access independently
4. Validate OpenSearch collection status

## Contributing

When contributing to this module:

1. Run `terraform fmt` to format code
2. Run `terraform validate` to validate configuration
3. Run the validation script: `./validate.sh`
4. Update tests for new functionality
5. Update this README for any changes

## License

This module is part of the AI Assistant CLI project.