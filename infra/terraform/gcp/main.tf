# GCP placeholder (kickoff prompt §L) — NOT applied by the local demo.
# GKE + Secret Manager + VPC. Fill project/region + backend before use.

terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # Remote LOCKED state in GCS.
  # backend "gcs" {
  #   bucket = "diagnostics-tfstate-<project>"
  #   prefix = "diagnostics/gcp"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
  # Auth via Workload Identity Federation (OIDC) in CI — no key files.
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1" # EU region for data residency (GDPR)
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
# module "gke" {
#   source      = "../modules/k8s-cluster"
#   environment = var.environment
#   network     = module.network.network_self_link
# }
#
# resource "google_secret_manager_secret" "neo4j_password" {
#   secret_id = "diagnostics-${var.environment}-neo4j-password"
#   replication { auto {} }
# }
#
# output "cluster_endpoint" { value = module.gke.endpoint }
