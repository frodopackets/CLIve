# Compute Module

This Terraform module creates the compute and API infrastructure for the AI Assistant CLI application.

## Overview

The compute module provisions:

- **Lambda Functions**: FastAPI backend, WebSocket handler, and JWT authorizer
- **API Gateway**: REST API and WebSocket API with JWT authorization
- **DynamoDB**: Session storage with TTL and GSI for user queries
- **CloudWatch**: Logging and monitoring with alarms

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   Lambda        │
│   (Browser)     │───▶│   - REST API     │───▶│   - FastAPI     │
│                 │    │   - WebSocket    │    │   - WebSocket   │
└─────────────────┘    │   - JWT Auth     │    │   - Authorizer  │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   CloudWatch     │    │   DynamoDB      │
                       │   - Logs         │    │   - Sessions    │
                       │   - Alarms       │    │   - TTL         │
                       └──────────────────┘    └─────────────────┘
```

## Resources Created

### Lambda Functions

1. **Main Function** (`${project_name}-${environment}-main`)
   - Handles REST API requests
   - FastAPI application
   - Integrates with Bedrock and Knowledge Base

2. **WebSocket Function** (`${project_name}-${environment}-websocket`)
   - Handles WebSocket connections
   - Real-time communication
   - Connection management

3. **JWT Authorizer** (`${project_name}-${environment}-jwt-authorizer`)
   - Validates JWT tokens from Identity Center
   - Custom authorizer for API Gateway
   - Returns authorization policies

### API Gateway

1. **REST API**
   - `/api/v1/health` - Health check (no auth)
   - `/api/v1/sessions` - Session management (auth required)
   - `/api/v1/sessions/{session_id}` - Individual session operations
   - `/api/v1/knowledge-bases` - Knowledge base listing

2. **WebSocket API**
   - `$connect` - Connection establishment
   - `$disconnect` - Connection cleanup
   - `$default` - Message handling

### DynamoDB Table

- **Sessions Table** (`${project_name}-${environment}-sessions`)
  - Hash Key: `session_id`
  - GSI: `UserIndex` (user_id, last_activity)
  - TTL: `expires_at`
  - Point-in-time recovery (configurable)

### CloudWatch Resources

- **Log Groups**
  - API Gateway logs
  - Lambda function logs
  - Configurable retention period

- **Alarms**
  - Lambda errors and duration
  - API Gateway 4XX errors
  - DynamoDB throttling

## Variables

### Required Variables

| Name | Description | Type |
|------|-------------|------|
| `project_name` | Name of the project | `string` |
| `environment` | Environment name | `string` |
| `aws_region` | AWS region | `string` |
| `tags` | Common tags | `map(string)` |
| `vpc_id` | VPC ID | `string` |
| `private_subnet_ids` | Private subnet IDs | `list(string)` |
| `lambda_security_group_id` | Lambda security group ID | `string` |
| `lambda_bedrock_role_arn` | Lambda IAM role ARN | `string` |
| `knowledge_base_id` | Bedrock Knowledge Base ID | `string` |
| `bedrock_models` | List of Bedrock models | `list(string)` |

### Optional Variables

| Name | Description | Default |
|------|-------------|---------|
| `lambda_runtime` | Lambda runtime | `python3.11` |
| `lambda_timeout` | Lambda timeout (seconds) | `30` |
| `lambda_memory_size` | Lambda memory (MB) | `512` |
| `lambda_reserved_concurrency` | Reserved concurrency | `10` |
| `api_gateway_stage_name` | API Gateway stage | `v1` |
| `api_gateway_throttle_rate_limit` | Rate limit (req/sec) | `1000` |
| `api_gateway_throttle_burst_limit` | Burst limit | `2000` |
| `dynamodb_billing_mode` | DynamoDB billing mode | `PAY_PER_REQUEST` |
| `dynamodb_point_in_time_recovery` | Enable PITR | `true` |
| `log_retention_days` | Log retention days | `30` |
| `identity_center_issuer_url` | Identity Center issuer URL | `""` |
| `jwt_audience` | JWT audience | `""` |

## Outputs

### API Endpoints

- `api_gateway_rest_api_url` - REST API URL
- `api_gateway_websocket_url` - WebSocket API URL

### Lambda Functions

- `lambda_main_function_name` - Main function name
- `lambda_websocket_function_name` - WebSocket function name
- `lambda_jwt_authorizer_function_name` - Authorizer function name

### Storage

- `dynamodb_sessions_table_name` - Sessions table name

### Configuration

- `compute_config` - Complete configuration object for integration

## Usage

```hcl
module "compute" {
  source = "./modules/compute"
  
  project_name = "ai-assistant-cli"
  environment  = "dev"
  aws_region   = "us-east-1"
  tags         = local.common_tags
  
  # Networking
  vpc_id                    = module.networking.vpc_id
  private_subnet_ids        = module.networking.private_subnet_ids
  lambda_security_group_id  = module.security.lambda_security_group_id
  
  # AI Services integration
  lambda_bedrock_role_arn   = module.ai_services.lambda_bedrock_role_arn
  knowledge_base_id         = module.ai_services.knowledge_base_id
  bedrock_models            = var.bedrock_models
  
  # Authentication
  identity_center_issuer_url = var.identity_center_issuer_url
  jwt_audience              = var.jwt_audience
}
```

## Security Considerations

1. **Authentication**: All API endpoints (except health check) require JWT authentication
2. **Authorization**: Custom JWT authorizer validates tokens from Identity Center
3. **Network Security**: Lambda functions run in private subnets
4. **Data Encryption**: DynamoDB encryption at rest enabled
5. **Logging**: All API calls and Lambda executions are logged
6. **Monitoring**: CloudWatch alarms for error detection

## Deployment Notes

1. **Placeholder Functions**: Initial deployment uses placeholder Lambda functions
2. **Code Deployment**: Actual FastAPI code should be deployed separately
3. **Authentication Setup**: Identity Center configuration required for JWT validation
4. **Environment Variables**: Lambda functions receive necessary environment variables
5. **VPC Configuration**: Lambda functions have VPC access for AI services integration

## Monitoring and Troubleshooting

### CloudWatch Alarms

- **Lambda Errors**: Triggers when error rate exceeds threshold
- **Lambda Duration**: Monitors function execution time
- **API Gateway Errors**: Tracks 4XX error rates
- **DynamoDB Throttles**: Monitors table throttling

### Log Groups

- `/aws/apigateway/${project_name}-${environment}` - API Gateway logs
- `/aws/lambda/${project_name}-${environment}-main` - Main Lambda logs
- `/aws/lambda/${project_name}-${environment}-websocket` - WebSocket Lambda logs

### Common Issues

1. **JWT Validation Failures**: Check Identity Center configuration
2. **Lambda Timeouts**: Increase timeout or optimize code
3. **DynamoDB Throttling**: Consider provisioned capacity
4. **VPC Connectivity**: Verify security groups and routing