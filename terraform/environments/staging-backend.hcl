# Staging backend configuration
bucket         = "ai-assistant-cli-terraform-state-staging"
key            = "staging/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "ai-assistant-cli-terraform-locks-staging"