# Compute Module Deployment Guide

This guide provides step-by-step instructions for deploying the compute module of the AI Assistant CLI infrastructure.

## Prerequisites

Before deploying the compute module, ensure the following modules are already deployed:

1. **Networking Module** - VPC, subnets, and networking components
2. **Security Module** - Security groups and IAM roles
3. **AI Services Module** - Bedrock services and Knowledge Base

## Deployment Steps

### 1. Validate Configuration

First, validate the module configuration:

```bash
cd terraform/modules/compute
./validate.sh
```

### 2. Configure Environment Variables

Update the appropriate environment file with your specific values:

**For Development (`terraform/environments/dev.tfvars`):**
```hcl
# Authentication configuration
identity_center_issuer_url = "https://your-identity-center-domain.awsapps.com/start"
jwt_audience              = "your-jwt-audience-id"
```

**For Staging/Production:**
Update the corresponding `.tfvars` files with production values.

### 3. Deploy Infrastructure

From the main terraform directory:

```bash
# Initialize Terraform (if not already done)
terraform init -backend-config=environments/dev-backend.hcl

# Plan the deployment
terraform plan -var-file=environments/dev.tfvars

# Apply the changes
terraform apply -var-file=environments/dev.tfvars
```

### 4. Verify Deployment

After successful deployment, verify the resources:

```bash
# Check API Gateway URL
terraform output api_gateway_rest_api_url

# Check WebSocket URL
terraform output api_gateway_websocket_url

# Check Lambda functions
terraform output lambda_main_function_name
terraform output lambda_websocket_function_name

# Check DynamoDB table
terraform output dynamodb_sessions_table_name
```

## Post-Deployment Configuration

### 1. Test Health Endpoint

Test the health check endpoint (no authentication required):

```bash
# Get the API URL
API_URL=$(terraform output -raw api_gateway_rest_api_url)

# Test health endpoint
curl "${API_URL}/api/v1/health"
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "dev",
  "message": "AI Assistant CLI API is running",
  "timestamp": "request-id"
}
```

### 2. Configure Identity Center

1. **Set up Identity Center Application:**
   - Create a new application in AWS Identity Center
   - Configure OIDC/OAuth2 settings
   - Note the issuer URL and audience ID

2. **Update Terraform Variables:**
   ```hcl
   identity_center_issuer_url = "https://your-domain.awsapps.com/start"
   jwt_audience              = "your-audience-id"
   ```

3. **Redeploy with Authentication:**
   ```bash
   terraform apply -var-file=environments/dev.tfvars
   ```

### 3. Deploy FastAPI Application

The initial deployment uses placeholder Lambda functions. Deploy the actual FastAPI application:

1. **Package the FastAPI Application:**
   ```bash
   cd backend
   pip install -r requirements.txt -t package/
   cp -r . package/
   cd package && zip -r ../lambda-package.zip .
   ```

2. **Update Lambda Functions:**
   ```bash
   # Update main function
   aws lambda update-function-code \
     --function-name $(terraform output -raw lambda_main_function_name) \
     --zip-file fileb://lambda-package.zip

   # Update websocket function
   aws lambda update-function-code \
     --function-name $(terraform output -raw lambda_websocket_function_name) \
     --zip-file fileb://lambda-package.zip
   ```

### 4. Test WebSocket Connection

Test the WebSocket connection:

```bash
# Get WebSocket URL
WS_URL=$(terraform output -raw api_gateway_websocket_url)

# Test connection (requires wscat or similar tool)
wscat -c "${WS_URL}"
```

## Monitoring and Troubleshooting

### CloudWatch Logs

Monitor the application through CloudWatch logs:

```bash
# View API Gateway logs
aws logs tail /aws/apigateway/ai-assistant-cli-dev --follow

# View Lambda logs
aws logs tail /aws/lambda/ai-assistant-cli-dev-main --follow
aws logs tail /aws/lambda/ai-assistant-cli-dev-websocket --follow
```

### CloudWatch Alarms

The module creates several alarms for monitoring:

- **Lambda Errors**: Monitors error rates in Lambda functions
- **Lambda Duration**: Monitors execution time
- **API Gateway Errors**: Monitors 4XX error rates
- **DynamoDB Throttles**: Monitors table throttling

Check alarm status:
```bash
aws cloudwatch describe-alarms --alarm-names \
  "ai-assistant-cli-dev-lambda-errors" \
  "ai-assistant-cli-dev-lambda-duration" \
  "ai-assistant-cli-dev-api-gateway-errors" \
  "ai-assistant-cli-dev-dynamodb-throttles"
```

### Common Issues

#### 1. JWT Authorization Failures

**Symptoms:** 401 Unauthorized responses
**Solutions:**
- Verify Identity Center configuration
- Check JWT token format and expiration
- Validate issuer URL and audience

#### 2. Lambda Function Timeouts

**Symptoms:** 504 Gateway Timeout errors
**Solutions:**
- Increase Lambda timeout in variables
- Optimize function code
- Check VPC connectivity

#### 3. DynamoDB Access Issues

**Symptoms:** 500 Internal Server Error
**Solutions:**
- Verify IAM permissions
- Check DynamoDB table exists
- Validate table schema

#### 4. WebSocket Connection Issues

**Symptoms:** Connection failures or immediate disconnects
**Solutions:**
- Check WebSocket Lambda function logs
- Verify API Gateway WebSocket configuration
- Test connection with simple WebSocket client

## Environment-Specific Configurations

### Development Environment

- Lower resource limits for cost optimization
- Detailed logging enabled
- Point-in-time recovery disabled for DynamoDB
- Reduced Lambda concurrency

### Staging Environment

- Production-like configuration
- Full monitoring enabled
- Point-in-time recovery enabled
- Moderate resource limits

### Production Environment

- High availability configuration
- Full monitoring and alerting
- Point-in-time recovery enabled
- Higher resource limits and concurrency

## Security Considerations

1. **API Gateway Security:**
   - JWT authorization on all protected endpoints
   - CORS configuration for frontend access
   - Rate limiting and throttling enabled

2. **Lambda Security:**
   - Functions run in private subnets
   - Minimal IAM permissions
   - Environment variables for configuration

3. **DynamoDB Security:**
   - Encryption at rest enabled
   - TTL for automatic data cleanup
   - IAM-based access control

4. **CloudWatch Security:**
   - Log retention policies configured
   - No sensitive data in logs
   - Monitoring for security events

## Cleanup

To remove the compute infrastructure:

```bash
# Destroy resources
terraform destroy -var-file=environments/dev.tfvars

# Confirm destruction
# Type 'yes' when prompted
```

**Note:** This will permanently delete all compute resources including Lambda functions, API Gateway, and DynamoDB table with all data.

## Next Steps

After successful deployment:

1. **Deploy Frontend Module** - Set up S3 and CloudFront for frontend hosting
2. **Integration Testing** - Test end-to-end functionality
3. **Performance Optimization** - Monitor and optimize based on usage patterns
4. **Security Hardening** - Implement additional security measures as needed