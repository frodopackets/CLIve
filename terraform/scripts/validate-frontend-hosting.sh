#!/bin/bash

# Validation script for frontend hosting module
# This script validates the Terraform configuration and runs basic checks

set -e

echo "🔍 Validating Frontend Hosting Module..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "ℹ️  $message"
            ;;
    esac
}

# Check if we're in the terraform directory
if [ ! -f "main.tf" ]; then
    print_status "ERROR" "Please run this script from the terraform directory"
    exit 1
fi

# Check if frontend-hosting module exists
if [ ! -d "modules/frontend-hosting" ]; then
    print_status "ERROR" "Frontend hosting module directory not found"
    exit 1
fi

print_status "INFO" "Checking Terraform configuration..."

# Validate Terraform syntax
print_status "INFO" "Running terraform validate..."
if terraform validate; then
    print_status "SUCCESS" "Terraform configuration is valid"
else
    print_status "ERROR" "Terraform validation failed"
    exit 1
fi

# Check Terraform formatting
print_status "INFO" "Checking Terraform formatting..."
if terraform fmt -check -recursive; then
    print_status "SUCCESS" "Terraform files are properly formatted"
else
    print_status "WARNING" "Some Terraform files need formatting. Run 'terraform fmt -recursive' to fix."
fi

# Validate frontend-hosting module specifically
print_status "INFO" "Validating frontend-hosting module..."
cd modules/frontend-hosting

if terraform validate; then
    print_status "SUCCESS" "Frontend hosting module is valid"
else
    print_status "ERROR" "Frontend hosting module validation failed"
    exit 1
fi

cd ../..

# Check if buildspec.yml exists
if [ -f "../../frontend/buildspec.yml" ]; then
    print_status "SUCCESS" "Frontend buildspec.yml found"
else
    print_status "WARNING" "Frontend buildspec.yml not found at frontend/buildspec.yml"
fi

# Check required files
required_files=(
    "modules/frontend-hosting/main.tf"
    "modules/frontend-hosting/variables.tf"
    "modules/frontend-hosting/outputs.tf"
    "modules/frontend-hosting/README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "SUCCESS" "Required file found: $file"
    else
        print_status "ERROR" "Required file missing: $file"
        exit 1
    fi
done

# Check environment configurations
environments=("dev" "staging" "prod")
for env in "${environments[@]}"; do
    if [ -f "environments/${env}.tfvars" ]; then
        print_status "SUCCESS" "Environment configuration found: $env"
        
        # Check if frontend variables are present
        if grep -q "frontend_" "environments/${env}.tfvars"; then
            print_status "SUCCESS" "Frontend variables found in $env configuration"
        else
            print_status "WARNING" "Frontend variables not found in $env configuration"
        fi
    else
        print_status "ERROR" "Environment configuration missing: $env"
        exit 1
    fi
done

# Check if tests exist
if [ -f "tests/frontend_hosting_test.go" ]; then
    print_status "SUCCESS" "Frontend hosting tests found"
    
    # Check if go.mod exists for tests
    if [ -f "tests/go.mod" ]; then
        print_status "SUCCESS" "Test dependencies configuration found"
    else
        print_status "WARNING" "Test dependencies configuration missing (tests/go.mod)"
    fi
else
    print_status "WARNING" "Frontend hosting tests not found"
fi

# Validate that main.tf includes the frontend_hosting module
if grep -q "module \"frontend_hosting\"" main.tf; then
    print_status "SUCCESS" "Frontend hosting module is included in main configuration"
else
    print_status "ERROR" "Frontend hosting module is not included in main.tf"
    exit 1
fi

# Check outputs.tf includes frontend outputs
if grep -q "frontend_" outputs.tf; then
    print_status "SUCCESS" "Frontend outputs are included in main outputs"
else
    print_status "WARNING" "Frontend outputs not found in main outputs.tf"
fi

# Check variables.tf includes frontend variables
if grep -q "frontend_" variables.tf; then
    print_status "SUCCESS" "Frontend variables are included in main variables"
else
    print_status "ERROR" "Frontend variables not found in main variables.tf"
    exit 1
fi

print_status "SUCCESS" "Frontend hosting module validation completed successfully!"

echo ""
echo "📋 Next steps:"
echo "1. Initialize Terraform: make init ENV=dev"
echo "2. Plan deployment: make frontend-plan ENV=dev"
echo "3. Apply changes: make frontend-apply ENV=dev"
echo "4. Run tests: make test-frontend"
echo ""
echo "🔧 Configuration tips:"
echo "- Update GitHub repository settings in environment tfvars files"
echo "- Configure custom domain and SSL certificate ARNs if needed"
echo "- Set up AWS Secrets Manager with 'github-token' for pipeline"
echo "- Review CloudFront price class settings for cost optimization"