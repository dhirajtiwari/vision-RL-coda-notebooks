# Infrastructure as Code (kickoff prompt §L, handbook ch12)

> **Runtime reality:** this project runs as a **local Docker demo on a Mac mini**.
> The Terraform below is a **placeholder/reference** for AWS, GCP, and Azure so the
> path to a real cloud is scaffolded, not improvised. Nothing here is applied by
> the demo. `terraform validate`/`fmt` run in CI; `plan`/`apply` are gated on OIDC
> credentials that do not exist in the demo.

## Layout
```
infra/
├── terraform/
│   ├── aws/          # EKS + Secrets Manager + VPC (placeholder)
│   ├── gcp/          # GKE + Secret Manager + VPC (placeholder)
│   ├── azure/        # AKS + Key Vault + VNet (placeholder)
│   └── modules/      # reusable, versioned modules (network, k8s, secrets)
└── policy/           # policy-as-code (checkov/OPA) — placeholder
```

## Principles (enforced when a real cloud is chosen)
- Remote, **locked** state (S3+DynamoDB / GCS / Azure Storage) — isolated per env.
- Reusable **versioned** modules; no copy-paste between envs.
- **OIDC short-lived** CI credentials — no long-lived cloud keys.
- `plan` on PR, `apply` on approval; policy-as-code gates (checkov/OPA/Sentinel).
- Secrets in the cloud secret manager, injected at runtime — never in state or repo.

## Local demo
No Terraform needed. Use:
```bash
make up        # docker compose stack
```
