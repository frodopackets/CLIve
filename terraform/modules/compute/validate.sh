#!/bin/bash

# Validation script for compute module
set -e

echo "Validating Terraform compute module..."

# Check if required files exist
required_files=("main.tf" "variables.tf" "outputs.tf" "lambda_placeholder.py")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: Required file $file not found"
        exit 1
    fi
done

echo "✓ All required files present"

# Basic syntax validation using grep patterns
echo "Checking Terraform syntax patterns..."

# Check for balanced braces (basic check)
main_open=$(grep -o '{' main.tf | wc -l)
main_close=$(grep -o '}' main.tf | wc -l)
if [[ $main_open -ne $main_close ]]; then
    echo "ERROR: Unbalanced braces in main.tf (open: $main_open, close: $main_close)"
    exit 1
fi

echo "✓ Basic syntax validation passed"

# Check for required resources
required_resources=(
    "aws_lambda_function.*main"
    "aws_lambda_function.*websocket"
    "aws_lambda_function.*jwt_authorizer"
    "aws_api_gateway_rest_api.*main"
    "aws_apigatewayv2_api.*websocket"
    "aws_dynamodb_table.*sessions"
    "aws_cloudwatch_log_group"
)

for resource in "${required_resources[@]}"; do
    if ! grep -q "resource.*$resource" main.tf; then
        echo "ERROR: Required resource $resource not found"
        exit 1
    fi
done

echo "✓ All required resources present"

# Check variable definitions
required_vars=(
    "project_name"
    "environment"
    "aws_region"
    "vpc_id"
    "private_subnet_ids"
    "lambda_security_group_id"
    "lambda_bedrock_role_arn"
    "knowledge_base_id"
    "bedrock_models"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "variable.*\"$var\"" variables.tf; then
        echo "ERROR: Required variable $var not found"
        exit 1
    fi
done

echo "✓ All required variables defined"

# Check outputs
required_outputs=(
    "lambda_main_function_name"
    "api_gateway_rest_api_url"
    "api_gateway_websocket_url"
    "dynamodb_sessions_table_name"
    "compute_config"
)

for output in "${required_outputs[@]}"; do
    if ! grep -q "output.*\"$output\"" outputs.tf; then
        echo "ERROR: Required output $output not found"
        exit 1
    fi
done

echo "✓ All required outputs defined"

echo "✅ Compute module validation completed successfully!"
echo ""
echo "Module provides:"
echo "  - 3 Lambda functions (main, websocket, jwt-authorizer)"
echo "  - REST API Gateway with JWT authorization"
echo "  - WebSocket API Gateway"
echo "  - DynamoDB sessions table with TTL and GSI"
echo "  - CloudWatch logging and monitoring"
echo "  - 4 CloudWatch alarms for monitoring"
echo ""
echo "Next steps:"
echo "  1. Deploy the infrastructure with 'terraform apply'"
echo "  2. Deploy actual FastAPI code to replace placeholder functions"
echo "  3. Configure Identity Center issuer URL and JWT audience"
echo "  4. Test API endpoints and WebSocket connections"