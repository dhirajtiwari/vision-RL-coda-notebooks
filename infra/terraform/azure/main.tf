# Azure placeholder (kickoff prompt §L) — NOT applied by the local demo.
# AKS + Key Vault + VNet + Azure AI Foundry. Fill subscription/rg + backend first.

terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  # Remote LOCKED state in an Azure Storage account.
  # backend "azurerm" {
  #   resource_group_name  = "diagnostics-tfstate"
  #   storage_account_name = "diagtfstate<unique>"
  #   container_name       = "tfstate"
  #   key                  = "diagnostics/azure/terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
  # Auth via OIDC federated credentials in CI — no client secrets.
}

variable "location" {
  type    = string
  default = "westeurope" # EU region for data residency (GDPR)
}

variable "environment" {
  type    = string
  default = "dev"
}

# --- Example wiring (commented until a real deployment) ---------------------
# resource "azurerm_resource_group" "main" {
#   name     = "diagnostics-${var.environment}"
#   location = var.location
# }
#
# module "aks" {
#   source              = "../modules/k8s-cluster"
#   environment         = var.environment
#   resource_group_name = azurerm_resource_group.main.name
#   location            = var.location
# }
#
# resource "azurerm_key_vault" "main" {
#   name                = "diag-kv-${var.environment}"
#   location            = var.location
#   resource_group_name = azurerm_resource_group.main.name
#   # ... tenant_id, sku_name, access policies ...
# }
#
# # Azure AI Foundry / Azure OpenAI for the optional LLM path (gateway provider).
# # resource "azurerm_cognitive_account" "openai" { kind = "OpenAI" ... }
