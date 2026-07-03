# Reusable Terraform modules (placeholder)

Versioned, cloud-agnostic-ish module interfaces referenced by `../aws|gcp|azure`.
Implement per-cloud when a real target is chosen. Keep inputs/outputs stable so
environments differ only by variables, never by copy-paste.

Planned modules:
- `network/` — VPC/VNet, subnets, NAT, security groups/firewall.
- `k8s-cluster/` — EKS/GKE/AKS with node pools, OIDC/IRSA, autoscaling.
- `secrets/` — secret-manager wiring + IAM bindings for the app identity.
- `vector-store/` — (only if embeddings are ever introduced) managed vector DB.

Each module must expose `environment` input and cluster/endpoint outputs.
