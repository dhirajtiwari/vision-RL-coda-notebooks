# Architecture Diagrams (Graphviz)

> **C4 model (canonical):** See [`docs/c4/README.md`](../c4/README.md) for the full C4 L1–L4 + deployment + dynamic diagram set and Structurizr DSL source (`docs/c4/workspace.dsl`).

## Canonical set (use for reviews)

| ID | Source (`.dot`) | Rendered PNG | Level |
|----|-----------------|--------------|-------|
| **21** | `21-architecture-L1-system-context.dot` | `rendered/png/21-architecture-L1-system-context.png` | C4 L1 |
| **22** | `22-architecture-L2-container.dot` | `rendered/png/22-architecture-L2-container.png` | C4 L2 |
| **27** | `27-architecture-L2-enterprise-connectors.dot` | `rendered/png/27-architecture-L2-enterprise-connectors.png` | C4 L2 detail |
| **23** | `23-architecture-L3-component.dot` | `rendered/png/23-architecture-L3-component.png` | C4 L3 |
| **24** | `24-architecture-L4-code.dot` | `rendered/png/24-architecture-L4-code.png` | C4 L4 |
| **25** | `25-architecture-LLD-diagnosis-claim-sequence.dot` | `rendered/png/25-architecture-LLD-diagnosis-claim-sequence.png` | LLD |
| **28** | `28-architecture-LLD-etl-connector-pipeline.dot` | `rendered/png/28-architecture-LLD-etl-connector-pipeline.png` | LLD |
| **29** | `29-architecture-LLD-api-connector-routes.dot` | `rendered/png/29-architecture-LLD-api-connector-routes.png` | LLD |
| **30** | `30-architecture-LLD-deployment-k8s.dot` | `rendered/png/30-architecture-LLD-deployment-k8s.png` | LLD / K8s |
| **31** | `31-architecture-LLD-cicd-github-actions.dot` | `rendered/png/31-architecture-LLD-cicd-github-actions.png` | LLD / CI/CD |
| **32** | `32-architecture-LLD-multi-env-promotion.dot` | `rendered/png/32-architecture-LLD-multi-env-promotion.png` | LLD / promotion |
| **33** | `33-architecture-C4-notation-index.dot` | `rendered/png/33-architecture-C4-notation-index.png` | Index |
| **34** | `34-enterprise-blueprint-ERD.dot` | `rendered/png/34-enterprise-blueprint-ERD.png` | **ERD** (full ontology) |
| **35** | `35-layer-architecture-symmetric.dot` | `rendered/png/35-layer-architecture-symmetric.png` | **6-layer architecture** |
| **36** | `36-end-to-end-pipeline-io.dot` | `rendered/png/36-end-to-end-pipeline-io.png` | **Pipeline I/O** |
| **37** | `37-module-catalog-by-phase.dot` | `rendered/png/37-module-catalog-by-phase.png` | **Module catalog** |

SVG copies live alongside PNG under `rendered/svg/`.

**Narrative guide:** `docs/PIPELINE-AND-MODULE-GUIDE.md` — blueprint → graph → diagnosis → claim (files, formats, commands).

## Ontology (not C4 architecture)

| ID | File | Purpose |
|----|------|---------|
| **05** | `05-neo4j-ontology.dot` | Neo4j node/relationship schema |
| **26** | `26-enterprise-product-blueprint.dot` | Per-SKU OEM diagnostic ontology |

## Deprecated (superseded)

Do not use for architecture sign-off — titles are marked `[DEPRECATED]` in the `.dot` source:

- `01-system-context.dot` → **21**
- `02-module-block.dot` → **24**
- `06-etl-pipeline.dot` → **28**
- `08-runtime-sequence.dot` → **25**
- `09-enterprise-production.dot` → **30–32**
- `14-etl-to-runtime.dot` → **28 + 32**

Demo/session swimlanes (`10`–`20`) remain valid for presentations but are not C4/LLD architecture.

## Render all diagrams

```bash
bash docs/graphviz/render_all.sh
```

CI runs the same script on every PR (`.github/workflows/ci.yml`).

## Related deployment assets

| Asset | Location |
|-------|----------|
| Docker images | `docker/Dockerfile.{api,ui,mock,etl}` |
| Kubernetes (Kustomize) | `k8s/base/`, `k8s/overlays/staging/`, `k8s/overlays/prod/` |
| GitHub Actions CI | `.github/workflows/ci.yml` |
| GitHub Actions CD | `.github/workflows/cd.yml` |