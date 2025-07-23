# AI Services module for AI Assistant CLI
terraform {
  required_providers {
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 0.70"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 Bucket for Knowledge Base data sources
resource "aws_s3_bucket" "knowledge_base_data" {
  bucket = "${local.name_prefix}-knowledge-base-data-${random_id.bucket_suffix.hex}"
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-knowledge-base-data"
    Type = "knowledge-base-storage"
  })
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "knowledge_base_data" {
  bucket = aws_s3_bucket.knowledge_base_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base_data" {
  bucket = aws_s3_bucket.knowledge_base_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "knowledge_base_data" {
  bucket = aws_s3_bucket.knowledge_base_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# OpenSearch Serverless Collection for Knowledge Base vector storage
resource "awscc_opensearchserverless_collection" "knowledge_base_vector_store" {
  name = "${local.name_prefix}-kb-vectors"
  type = "VECTORSEARCH"
  
  tags = [
    {
      key   = "Name"
      value = "${local.name_prefix}-kb-vectors"
    },
    {
      key   = "Environment"
      value = var.environment
    },
    {
      key   = "Project"
      value = var.project_name
    }
  ]
}

# OpenSearch Serverless Security Policy for the collection
resource "awscc_opensearchserverless_security_policy" "knowledge_base_encryption" {
  name = "${local.name_prefix}-kb-encryption-policy"
  type = "encryption"
  
  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource = [
          "collection/${awscc_opensearchserverless_collection.knowledge_base_vector_store.name}"
        ]
      }
    ]
    AWSOwnedKey = true
  })
}

resource "awscc_opensearchserverless_security_policy" "knowledge_base_network" {
  name = "${local.name_prefix}-kb-network-policy"
  type = "network"
  
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = [
            "collection/${awscc_opensearchserverless_collection.knowledge_base_vector_store.name}"
          ]
        },
        {
          ResourceType = "dashboard"
          Resource = [
            "collection/${awscc_opensearchserverless_collection.knowledge_base_vector_store.name}"
          ]
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# IAM Role for Bedrock Knowledge Base
resource "aws_iam_role" "bedrock_knowledge_base_role" {
  name = "${local.name_prefix}-bedrock-kb-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
          }
        }
      }
    ]
  })
  
  tags = var.tags
}

# IAM Policy for Bedrock Knowledge Base to access S3
resource "aws_iam_policy" "bedrock_knowledge_base_s3_policy" {
  name = "${local.name_prefix}-bedrock-kb-s3-policy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.knowledge_base_data.arn,
          "${aws_s3_bucket.knowledge_base_data.arn}/*"
        ]
      }
    ]
  })
  
  tags = var.tags
}

# IAM Policy for Bedrock Knowledge Base to access OpenSearch Serverless
resource "aws_iam_policy" "bedrock_knowledge_base_opensearch_policy" {
  name = "${local.name_prefix}-bedrock-kb-opensearch-policy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = awscc_opensearchserverless_collection.knowledge_base_vector_store.arn
      }
    ]
  })
  
  tags = var.tags
}

# IAM Policy for Bedrock Knowledge Base to access Bedrock models
resource "aws_iam_policy" "bedrock_knowledge_base_model_policy" {
  name = "${local.name_prefix}-bedrock-kb-model-policy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v1",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      }
    ]
  })
  
  tags = var.tags
}

# Attach policies to the Bedrock Knowledge Base role
resource "aws_iam_role_policy_attachment" "bedrock_knowledge_base_s3" {
  role       = aws_iam_role.bedrock_knowledge_base_role.name
  policy_arn = aws_iam_policy.bedrock_knowledge_base_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "bedrock_knowledge_base_opensearch" {
  role       = aws_iam_role.bedrock_knowledge_base_role.name
  policy_arn = aws_iam_policy.bedrock_knowledge_base_opensearch_policy.arn
}

resource "aws_iam_role_policy_attachment" "bedrock_knowledge_base_model" {
  role       = aws_iam_role.bedrock_knowledge_base_role.name
  policy_arn = aws_iam_policy.bedrock_knowledge_base_model_policy.arn
}

# OpenSearch Serverless Access Policy for Bedrock
resource "awscc_opensearchserverless_access_policy" "knowledge_base_access" {
  name = "${local.name_prefix}-kb-access-policy"
  type = "data"
  
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = [
            "collection/${awscc_opensearchserverless_collection.knowledge_base_vector_store.name}"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems", 
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index"
          Resource = [
            "index/${awscc_opensearchserverless_collection.knowledge_base_vector_store.name}/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ]
      Principal = [
        aws_iam_role.bedrock_knowledge_base_role.arn
      ]
    }
  ])
}

# IAM Role for Lambda functions to access Bedrock services
resource "aws_iam_role" "lambda_bedrock_role" {
  name = "${local.name_prefix}-lambda-bedrock-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# IAM Policy for Lambda to access Bedrock services
resource "aws_iam_policy" "lambda_bedrock_policy" {
  name = "${local.name_prefix}-lambda-bedrock-policy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.nova-pro-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.nova-lite-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListKnowledgeBases",
          "bedrock:GetKnowledgeBase",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = var.tags
}

# Basic Lambda execution policy
resource "aws_iam_policy" "lambda_basic_execution" {
  name = "${local.name_prefix}-lambda-basic-execution"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = var.tags
}

# Attach policies to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_bedrock" {
  role       = aws_iam_role.lambda_bedrock_role.name
  policy_arn = aws_iam_policy.lambda_bedrock_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_bedrock_role.name
  policy_arn = aws_iam_policy.lambda_basic_execution.arn
}

# CloudWatch Log Groups for monitoring
resource "aws_cloudwatch_log_group" "bedrock_api_logs" {
  name              = "/aws/bedrock/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  
  tags = var.tags
}

resource "aws_cloudwatch_log_group" "knowledge_base_logs" {
  name              = "/aws/bedrock/knowledge-base/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  
  tags = var.tags
}

# CloudWatch Alarms for monitoring Bedrock usage
resource "aws_cloudwatch_metric_alarm" "bedrock_error_rate" {
  alarm_name          = "${local.name_prefix}-bedrock-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Bedrock"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors bedrock error rate"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    ModelId = "amazon.nova-pro-v1:0"
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "bedrock_throttling" {
  alarm_name          = "${local.name_prefix}-bedrock-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Throttles"
  namespace           = "AWS/Bedrock"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors bedrock throttling"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    ModelId = "amazon.nova-pro-v1:0"
  }
  
  tags = var.tags
}

# Bedrock Knowledge Base
resource "awscc_bedrock_knowledge_base" "main" {
  name        = "${local.name_prefix}-knowledge-base"
  description = "Knowledge base for AI Assistant CLI"
  role_arn    = aws_iam_role.bedrock_knowledge_base_role.arn
  
  knowledge_base_configuration = {
    type = "VECTOR"
    vector_knowledge_base_configuration = {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/${var.knowledge_base_embedding_model}"
    }
  }
  
  storage_configuration = {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration = {
      collection_arn    = awscc_opensearchserverless_collection.knowledge_base_vector_store.arn
      vector_index_name = "bedrock-knowledge-base-default-index"
      field_mapping = {
        vector_field   = "bedrock-knowledge-base-default-vector"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        metadata_field = "AMAZON_BEDROCK_METADATA"
      }
    }
  }
  
  tags = {
    Name        = "${local.name_prefix}-knowledge-base"
    Environment = var.environment
    Project     = var.project_name
  }
  
  depends_on = [
    awscc_opensearchserverless_collection.knowledge_base_vector_store,
    awscc_opensearchserverless_access_policy.knowledge_base_access,
    aws_iam_role_policy_attachment.bedrock_knowledge_base_opensearch,
    aws_iam_role_policy_attachment.bedrock_knowledge_base_model
  ]
}

# Bedrock Data Source for Knowledge Base
resource "awscc_bedrock_data_source" "main" {
  knowledge_base_id = awscc_bedrock_knowledge_base.main.knowledge_base_id
  name              = "${local.name_prefix}-data-source"
  description       = "S3 data source for knowledge base"
  
  data_source_configuration = {
    type = "S3"
    s3_configuration = {
      bucket_arn = aws_s3_bucket.knowledge_base_data.arn
      inclusion_prefixes = ["documents/"]
    }
  }
  
  vector_ingestion_configuration = {
    chunking_configuration = {
      chunking_strategy = var.knowledge_base_chunking_strategy
      fixed_size_chunking_configuration = var.knowledge_base_chunking_strategy == "FIXED_SIZE" ? {
        max_tokens     = var.knowledge_base_chunk_size
        overlap_percentage = var.knowledge_base_chunk_overlap
      } : null
    }
  }
  
  depends_on = [
    awscc_bedrock_knowledge_base.main,
    aws_s3_bucket.knowledge_base_data
  ]
}