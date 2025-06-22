# main.tf - MSK cluster Terraform setup (updated for Terraform 1.8+)

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "eu-north-1"
}

# ---------------------------
# VPC and Subnets
# ---------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.1"

  name = "reddit-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["eu-north-1a", "eu-north-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.3.0/24", "10.0.4.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

# ---------------------------
# MSK Security Group
# ---------------------------
resource "aws_security_group" "msk_sg" {
  name        = "msk-sg"
  description = "Allow Kafka access from ECS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    description     = "Allow Kafka from ECS"
    cidr_blocks     = ["10.0.0.0/16"] # Replace with ECS task SG if needed
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------
# MSK Cluster
# ---------------------------
resource "aws_msk_cluster" "reddit_msk" {
  cluster_name           = "reddit-msk"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 2

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.msk_sg.id]

    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "PLAINTEXT"
      in_cluster    = true
    }
  }

  tags = {
    Name        = "reddit-msk"
    Environment = "dev"
  }
}

# ---------------------------
# Output Bootstrap Brokers
# ---------------------------
output "kafka_bootstrap_brokers" {
  value = aws_msk_cluster.reddit_msk.bootstrap_brokers
}
