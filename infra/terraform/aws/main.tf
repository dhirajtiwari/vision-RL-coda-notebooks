# AWS placeholder (kickoff prompt §L) — NOT applied by the local demo.
# EKS + Secrets Manager + VPC. Fill account/region + backend before use.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Remote LOCKED state (create the bucket + lock table first).
  # backend "s3" {
  #   bucket         = "diagnostics-tfstate-<account>"
  #   key            = "diagnostics/aws/terraform.tfstate"
  #   region         = "eu-west-1"
  #   dynamodb_table = "diagnostics-tf-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region
  # Auth via OIDC short-lived role in CI — no static keys.
}

variable "region" {
  type    = string
  default = "eu-west-1" # EU region for data residency (GDPR)
}

variable "environment" {
  type    = string
  default = "dev"
}

# --- Example wiring (commented until a real deployment) ---------------------
# module "network" {
#   source      = "../modules/network"
#   environment = var.environment
# }
#
# module "eks" {
#   source      = "../modules/k8s-cluster"
#   environment = var.environment
#   subnet_ids  = module.network.private_subnet_ids
# }
#
# resource "aws_secretsmanager_secret" "neo4j_password" {
#   name = "diagnostics/${var.environment}/neo4j-password"
# }
#
# output "cluster_endpoint" { value = module.eks.endpoint }
