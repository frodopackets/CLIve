#!/bin/bash

# Terraform validation script for AI Services module
set -e

echo "Starting Terraform validation for AI Services module..."

# Change to module directory
cd "$(dirname "$0")"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -backend=false

# Validate Terraform configuration
echo "Validating Terraform configuration..."
terraform validate

# Format check
echo "Checking Terraform formatting..."
terraform fmt -check=true -diff=true

# Security scan with tfsec (if available)
if command -v tfsec &> /dev/null; then
    echo "Running security scan with tfsec..."
    tfsec .
else
    echo "tfsec not found, skipping security scan"
fi

# Plan with example variables
echo "Testing Terraform plan with example variables..."
terraform plan \
    -var="project_name=test-ai-assistant" \
    -var="environment=test" \
    -var="aws_region=us-east-1" \
    -var="vpc_id=vpc-12345678" \
    -var="private_subnet_ids=[\"subnet-12345678\",\"subnet-87654321\"]" \
    -var="lambda_security_group_id=sg-12345678" \
    -var="tags={Environment=\"test\",Project=\"test-ai-assistant\"}" \
    -out=tfplan

# Show plan
echo "Showing Terraform plan..."
terraform show -no-color tfplan

# Clean up
rm -f tfplan
rm -rf .terraform

echo "Terraform validation completed successfully!"