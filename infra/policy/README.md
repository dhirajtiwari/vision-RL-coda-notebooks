# Policy-as-code (kickoff prompt §L/§M, handbook ch12/ch13)

Placeholder for infrastructure + supply-chain policy gates. Wire into CI
(`infra.yaml`) once a real cloud target exists.

Planned:
- **checkov** — scan Terraform for misconfig (public buckets, open SGs, unencrypted
  storage). Run: `checkov -d infra/terraform`.
- **OPA/Conftest** — custom Rego policies (e.g. "all storage encrypted", "no
  long-lived keys", "EU region only for data residency").
- **Kyverno/Gatekeeper** — admission policy in-cluster verifying image signatures
  (see `deploy/policy/verify-images.yaml`).

Example Rego intent (data residency):
```rego
# deny non-EU regions for GDPR
deny[msg] {
  input.resource.aws_instance
  not startswith(input.resource.aws_instance.region, "eu-")
  msg := "resources must be in an EU region (GDPR data residency)"
}
```
