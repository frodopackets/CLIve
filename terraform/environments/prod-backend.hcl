# Production backend configuration
bucket         = "ai-assistant-cli-terraform-state-prod"
key            = "prod/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "ai-assistant-cli-terraform-locks-prod"