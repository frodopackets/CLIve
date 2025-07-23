# Makefile for AI Assistant CLI Terraform operations

.PHONY: help init plan apply destroy validate format clean test test-frontend test-init

# Default environment
ENV ?= dev

# Help target
help:
	@echo "Available targets:"
	@echo "  init ENV=<env>     - Initialize Terraform with backend config"
	@echo "  plan ENV=<env>     - Plan Terraform changes"
	@echo "  apply ENV=<env>    - Apply Terraform changes"
	@echo "  destroy ENV=<env>  - Destroy Terraform resources"
	@echo "  validate          - Validate Terraform configuration"
	@echo "  format            - Format Terraform files"
	@echo "  test              - Run all Terraform tests"
	@echo "  test-frontend     - Run frontend hosting module tests"
	@echo "  test-init         - Initialize test dependencies"
	@echo "  clean             - Clean Terraform cache files"
	@echo ""
	@echo "Frontend-specific targets:"
	@echo "  frontend-plan     - Plan frontend hosting module changes"
	@echo "  frontend-apply    - Apply frontend hosting module changes"
	@echo "  frontend-destroy  - Destroy frontend hosting module resources"
	@echo ""
	@echo "Available environments: dev, staging, prod"
	@echo "Example: make plan ENV=staging"

# Initialize Terraform
init:
	@echo "Initializing Terraform for $(ENV) environment..."
	terraform init -backend-config=environments/$(ENV)-backend.hcl

# Plan changes
plan:
	@echo "Planning Terraform changes for $(ENV) environment..."
	terraform plan -var-file=environments/$(ENV).tfvars

# Apply changes
apply:
	@echo "Applying Terraform changes for $(ENV) environment..."
	terraform apply -var-file=environments/$(ENV).tfvars

# Destroy resources
destroy:
	@echo "Destroying Terraform resources for $(ENV) environment..."
	terraform destroy -var-file=environments/$(ENV).tfvars

# Validate configuration
validate:
	@echo "Validating Terraform configuration..."
	terraform validate
	@echo "Checking Terraform formatting..."
	terraform fmt -check

# Format Terraform files
format:
	@echo "Formatting Terraform files..."
	terraform fmt -recursive

# Clean cache files
clean:
	@echo "Cleaning Terraform cache files..."
	rm -rf .terraform/
	rm -f .terraform.lock.hcl
	rm -f terraform.tfstate*
	cd tests && rm -rf go.sum || true

# Test targets
test-init:
	@echo "Initializing test dependencies..."
	cd tests && go mod tidy

test: test-init
	@echo "Running all Terraform tests..."
	cd tests && go test -v -timeout 45m

test-frontend: test-init
	@echo "Running frontend hosting module tests..."
	cd tests && go test -v -timeout 30m -run TestFrontendHosting

# Frontend-specific targets
frontend-plan:
	@echo "Planning frontend hosting module changes for $(ENV) environment..."
	terraform plan -var-file=environments/$(ENV).tfvars -target=module.frontend_hosting

frontend-apply:
	@echo "Applying frontend hosting module changes for $(ENV) environment..."
	terraform apply -var-file=environments/$(ENV).tfvars -target=module.frontend_hosting

frontend-destroy:
	@echo "Destroying frontend hosting module resources for $(ENV) environment..."
	terraform destroy -var-file=environments/$(ENV).tfvars -target=module.frontend_hosting

# Quick development workflow
dev-init: ENV=dev
dev-init: init

dev-plan: ENV=dev
dev-plan: plan

dev-apply: ENV=dev
dev-apply: apply

dev-destroy: ENV=dev
dev-destroy: destroy