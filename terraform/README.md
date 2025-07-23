# AI Assistant CLI - Terraform Infrastructure

This directory contains the Terraform configuration for deploying the AI Assistant CLI infrastructure on AWS using the AWSCC provider.

## Architecture

The infrastructure is organized into modular components:

- **Networking Module**: VPC, subnets, NAT gateways, route tables, and VPC endpoints
- **Security Module**: Security groups, WAF rules, and access controls
- **AI Services Module**: Bedrock services and Knowledge Base infrastructure
- **Compute Module**: Lambda functions, API Gateway, and DynamoDB
- **Frontend Module**: S3 hosting and CloudFront distribution

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **S3 bucket** for Terraform state storage (create manually before first deployment)
4. **DynamoDB table** for state locking (create manually before first deployment)

## Directory Structure

```
terraform/
├── main.tf                    # Main configuration and module calls
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output values
├── backend.tf                 # Backend configuration
├── environments/              # Environment-specific configurations
│   ├── dev.tfvars            # Development variables
│   ├── staging.tfvars        # Staging variables
│   ├── prod.tfvars           # Production variables
│   ├── dev-backend.hcl       # Development backend config
│   ├── staging-backend.hcl   # Staging backend config
│   └── prod-backend.hcl      # Production backend config
└── modules/                   # Reusable modules
    ├── networking/           # VPC and networking resources
    ├── security/             # Security groups and WAF
    ├── ai-services/          # Bedrock and AI services
    ├── compute/              # Lambda and API Gateway
    └── frontend/             # S3 and CloudFront
```

## Usage

### Initial Setup

1. **Create S3 buckets for state storage** (one per environment):
   ```bash
   aws s3 mb s3://ai-assistant-cli-terraform-state-dev
   aws s3 mb s3://ai-assistant-cli-terraform-state-staging
   aws s3 mb s3://ai-assistant-cli-terraform-state-prod
   ```

2. **Create DynamoDB tables for state locking**:
   ```bash
   aws dynamodb create-table \
     --table-name ai-assistant-cli-terraform-locks-dev \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
   ```

### Deployment

1. **Initialize Terraform** with environment-specific backend:
   ```bash
   # For development
   terraform init -backend-config=environments/dev-backend.hcl
   
   # For staging
   terraform init -backend-config=environments/staging-backend.hcl
   
   # For production
   terraform init -backend-config=environments/prod-backend.hcl
   ```

2. **Plan the deployment**:
   ```bash
   # For development
   terraform plan -var-file=environments/dev.tfvars
   
   # For staging
   terraform plan -var-file=environments/staging.tfvars
   
   # For production
   terraform plan -var-file=environments/prod.tfvars
   ```

3. **Apply the configuration**:
   ```bash
   # For development
   terraform apply -var-file=environments/dev.tfvars
   
   # For staging
   terraform apply -var-file=environments/staging.tfvars
   
   # For production
   terraform apply -var-file=environments/prod.tfvars
   ```

### Environment Management

Each environment has its own:
- Variable file (`environments/{env}.tfvars`)
- Backend configuration (`environments/{env}-backend.hcl`)
- Separate state file in S3
- Separate DynamoDB table for locking

### Module Development

When adding new modules:

1. Create the module directory under `modules/`
2. Include `main.tf`, `variables.tf`, and `outputs.tf`
3. Add the module call to the main `main.tf`
4. Update environment variable files as needed

### Validation

Run Terraform validation:
```bash
terraform validate
terraform fmt -check
```

### Cleanup

To destroy resources:
```bash
terraform destroy -var-file=environments/{env}.tfvars
```

## Security Considerations

- All resources are tagged for cost tracking and management
- WAF protection is enabled for API Gateway
- VPC endpoints reduce NAT Gateway costs and improve security
- Security groups follow least-privilege principles
- State files are encrypted in S3
- DynamoDB state locking prevents concurrent modifications

## Cost Optimization

- VPC endpoints for S3 and DynamoDB reduce NAT Gateway costs
- Lambda functions use ARM64 architecture where possible
- CloudFront caching reduces origin requests
- DynamoDB uses on-demand billing for variable workloads

## Monitoring

- CloudWatch logs for all services
- WAF metrics and logging
- VPC Flow Logs (can be enabled per environment)
- Cost and usage monitoring through tags