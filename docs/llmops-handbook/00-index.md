# The Enterprise LLMOps Handbook

> A production-ready, vendor-neutral reference companion and cookbook for AI architects and AI developers.
> **Content baseline: June 2026.**

This handbook is an **implementation manual**. It defines every concept you need to *learn*, *understand*, and *ship* enterprise-grade Large Language Model (LLM) systems, then backs each concept with copy-paste-ready configuration, manifests, pipelines, and checklists. It is deliberately **project-agnostic** — nothing here assumes a specific product, domain, or cloud. Use it as the spine for any new LLM initiative.

---

## Who this is for

| Reader | What you get |
|--------|--------------|
| **AI / Platform Architect** | Reference architectures, decision trees, control mappings (OWASP, NIST AI RMF, EU AI Act), and progressive-delivery blueprints. |
| **AI / ML Developer** | Runnable examples: prompt registries, eval harnesses, guardrails, CI/CD, Helm, Argo Rollouts, Flagger, OpenTelemetry. |
| **SRE / Platform Engineer** | Runbooks, rollback decision trees, canary gates, drift & quality monitoring. |
| **Security / GRC** | Threat models, OWASP LLM Top 10 mappings, governance and compliance readiness. |
| **Engineering Manager** | Production-readiness checklists and a portable project-kickoff prompt to standardize delivery. |

---

## How to use this handbook

1. **Learning path** — read Part I → Part V in order to build vocabulary and controls.
2. **Cookbook path** — jump to the chapter for the capability you are building (e.g. `03-ragops.md`) and lift the examples.
3. **Delivery path** — start every new project by pasting [`20-project-kickoff-prompt.md`](20-project-kickoff-prompt.md) into your AI coding agent (Codex, Claude Code, GitHub Copilot), scaffold the repo from [`21-reference-repository-blueprint.md`](21-reference-repository-blueprint.md), follow its phased sequence, and work the [production-readiness checklist](17-production-readiness-checklist.md) before go-live.

---

## Table of contents

### Part I — Foundations
- [`01-foundations.md`](01-foundations.md) — What LLMOps is, why it matters, LLMOps vs MLOps

### Part II — The Ops Disciplines
- [`02-promptops.md`](02-promptops.md) — PromptOps
- [`03-ragops.md`](03-ragops.md) — RAGOps
- [`04-evalops.md`](04-evalops.md) — EvalOps
- [`05-guardrails-ops.md`](05-guardrails-ops.md) — Guardrails Ops
- [`06-llm-finops.md`](06-llm-finops.md) — LLM FinOps
- [`07-model-gateway-and-modelops.md`](07-model-gateway-and-modelops.md) — Model Gateway & ModelOps

### Part III — Observability & Metrics
- [`08-observability-and-opentelemetry.md`](08-observability-and-opentelemetry.md) — Observability & OpenTelemetry
- [`09-llm-metric-catalog.md`](09-llm-metric-catalog.md) — LLM Metric Catalog

### Part IV — Security
- [`10-security-architecture.md`](10-security-architecture.md) — Security architecture, OWASP LLM Top 10, threat modeling

### Part V — Governance
- [`11-governance-and-compliance.md`](11-governance-and-compliance.md) — Governance, NIST AI RMF, EU AI Act readiness

### Part VI — Platform & DevOps
- [`12-platform-engineering-foundations.md`](12-platform-engineering-foundations.md) — DevOps foundations, repo structure, local dev, containerization, Terraform

### Part VII — CI/CD & Supply Chain
- [`13-cicd-for-llm-apps.md`](13-cicd-for-llm-apps.md) — CI/CD, GitHub Actions hardening, build/scan/SBOM/sign/evidence

### Part VIII — Progressive Delivery
- [`14-progressive-delivery.md`](14-progressive-delivery.md) — Deployment patterns, Helm, Argo Rollouts, Flagger, gates, rollback decision tree

### Part IX — Operations
- [`15-operations-runbook.md`](15-operations-runbook.md) — Drift, AI quality monitoring, production runbook

### Part X — Reference Implementations
- [`16-reference-implementations.md`](16-reference-implementations.md) — Claims Knowledge Assistant, Agentic Invoice Validation

### Part XI — Reference
- [`17-production-readiness-checklist.md`](17-production-readiness-checklist.md) — Production readiness checklist
- [`18-glossary.md`](18-glossary.md) — Glossary of key terms
- [`19-sources-and-references.md`](19-sources-and-references.md) — Sources, references & authority basis

### Part XII — Reusable Asset
- [`20-project-kickoff-prompt.md`](20-project-kickoff-prompt.md) — Copy-paste kickoff prompt for AI coding agents

### Part XIII — Build It End-to-End
- [`21-reference-repository-blueprint.md`](21-reference-repository-blueprint.md) — Complete reference repo tree, file-to-chapter matrix, and the phased Day-0→production implementation sequence
- [`LLMOPS-IMPLEMENTATION-PLAYBOOK.md`](LLMOPS-IMPLEMENTATION-PLAYBOOK.md) — Reusable, copy-paste field guide: the exact 9-step sequence, per-discipline code + significance/value/impact + pitfalls, a readiness checklist, and an adaptation guide by archetype

---

## Conventions used throughout

- **Note** — helpful context.
- **Practice** — a recommended, defensible default.
- **Warning** — a failure mode or footgun to avoid.
- Code blocks are labeled with their language and are intended to be copy-paste-ready. Replace `{{PLACEHOLDERS}}` with your values.
- Diagrams use [Mermaid](https://mermaid.js.org/); math uses KaTeX (`$...$`).
- Every chapter ends with a **checklist** and a **References** section that links into [`19-sources-and-references.md`](19-sources-and-references.md).

## Authority basis

This handbook synthesizes public, authoritative sources — including the OWASP GenAI/LLM projects, the NIST AI Risk Management Framework and its Generative AI Profile, the EU Artificial Intelligence Act, the OpenTelemetry Generative-AI semantic conventions, CNCF projects (Kubernetes, Argo Rollouts, Flagger, Helm), the SLSA supply-chain framework, and recognized practitioner literature. Full citations are consolidated in [`19-sources-and-references.md`](19-sources-and-references.md).

> **Warning — verify before you ship.** Standards evolve. Treat version-specific details (API versions, regulatory deadlines, CVE guidance) as *as-of June 2026* and re-check against the primary source before a production decision.
