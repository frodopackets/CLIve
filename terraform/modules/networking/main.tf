# Networking module for AI Assistant CLI
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

# VPC
resource "awscc_ec2_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# Internet Gateway
resource "awscc_ec2_internet_gateway" "main" {
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-igw"
  })
}

# VPC Gateway Attachment
resource "awscc_ec2_vpc_gateway_attachment" "main" {
  vpc_id              = awscc_ec2_vpc.main.id
  internet_gateway_id = awscc_ec2_internet_gateway.main.id
}

# Public Subnets
resource "awscc_ec2_subnet" "public" {
  count = length(var.public_subnet_cidrs)
  
  vpc_id                  = awscc_ec2_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-public-subnet-${count.index + 1}"
    Type = "public"
  })
}

# Private Subnets
resource "awscc_ec2_subnet" "private" {
  count = length(var.private_subnet_cidrs)
  
  vpc_id            = awscc_ec2_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-private-subnet-${count.index + 1}"
    Type = "private"
  })
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = length(var.public_subnet_cidrs)
  
  domain = "vpc"
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-nat-eip-${count.index + 1}"
  })
  
  depends_on = [awscc_ec2_vpc_gateway_attachment.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = length(var.public_subnet_cidrs)
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = awscc_ec2_subnet.public[count.index].id
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-nat-gateway-${count.index + 1}"
  })
  
  depends_on = [awscc_ec2_vpc_gateway_attachment.main]
}

# Public Route Table
resource "awscc_ec2_route_table" "public" {
  vpc_id = awscc_ec2_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-public-rt"
    Type = "public"
  })
}

# Public Route to Internet Gateway
resource "awscc_ec2_route" "public_internet" {
  route_table_id         = awscc_ec2_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = awscc_ec2_internet_gateway.main.id
}

# Public Subnet Route Table Associations
resource "awscc_ec2_subnet_route_table_association" "public" {
  count = length(var.public_subnet_cidrs)
  
  subnet_id      = awscc_ec2_subnet.public[count.index].id
  route_table_id = awscc_ec2_route_table.public.id
}

# Private Route Tables (one per AZ for high availability)
resource "awscc_ec2_route_table" "private" {
  count = length(var.private_subnet_cidrs)
  
  vpc_id = awscc_ec2_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-private-rt-${count.index + 1}"
    Type = "private"
  })
}

# Private Routes to NAT Gateways
resource "aws_route" "private_nat" {
  count = length(var.private_subnet_cidrs)
  
  route_table_id         = awscc_ec2_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

# Private Subnet Route Table Associations
resource "awscc_ec2_subnet_route_table_association" "private" {
  count = length(var.private_subnet_cidrs)
  
  subnet_id      = awscc_ec2_subnet.private[count.index].id
  route_table_id = awscc_ec2_route_table.private[count.index].id
}

# VPC Endpoints for AWS services (to reduce NAT Gateway costs)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = awscc_ec2_vpc.main.id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-s3-endpoint"
  })
}

resource "aws_vpc_endpoint_route_table_association" "s3_private" {
  count = length(awscc_ec2_route_table.private)
  
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  route_table_id  = awscc_ec2_route_table.private[count.index].id
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id       = awscc_ec2_vpc.main.id
  service_name = "com.amazonaws.${var.aws_region}.dynamodb"
  
  tags = merge(var.tags, {
    Name = "${local.name_prefix}-dynamodb-endpoint"
  })
}

resource "aws_vpc_endpoint_route_table_association" "dynamodb_private" {
  count = length(awscc_ec2_route_table.private)
  
  vpc_endpoint_id = aws_vpc_endpoint.dynamodb.id
  route_table_id  = awscc_ec2_route_table.private[count.index].id
}