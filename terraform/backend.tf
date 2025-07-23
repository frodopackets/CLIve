# Backend configuration for Terraform state management
terraform {
  backend "s3" {
    # Backend configuration will be provided via backend config files
    # or command line arguments during terraform init
  }
}