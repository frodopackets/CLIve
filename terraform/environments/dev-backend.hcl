# Development backend configuration
bucket         = "ai-assistant-cli-terraform-state-dev"
key            = "dev/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "ai-assistant-cli-terraform-locks-dev"