# C4 Model — Enterprise Warranty Diagnostics Platform

Complete [C4 model](https://c4model.com/) for the diagnostic-chatbot platform.

## Source of truth

| Format | Path | Use |
|--------|------|-----|
| **Structurizr DSL** | `workspace.dsl` | Edit in [Structurizr DSL](https://structurizr.com/dsl) or Structurizr Lite |
| **Graphviz (rendered)** | `graphviz/*.dot` | Local PNG/SVG via `render.sh` |

## C4 diagram set

### Static views

| C4 Level | Diagram | Graphviz source | Description |
|----------|---------|-----------------|-------------|
| **L1** | System Context | `c4-L1-system-context.dot` | People, platform, external systems |
| **L2** | Containers | `c4-L2-containers.dot` | Deployable/runtime containers |
| **L3** | Platform (overview) | `c4-L3-platform-components.dot` | All components |
| **L3** | Web App (zoom) | `c4-L3-webapp-components.dot` | Streamlit tabs |
| **L3** | REST API (zoom) | `c4-L3-api-components.dot` | FastAPI controllers |
| **L3** | ETL (zoom) | `c4-L3-etl-components.dot` | Batch pipeline |
| **L3** | Graph Intelligence (zoom) | `c4-L3-graph-intelligence-components.dot` | GraphRAG stack |
| **L3** | Blueprint Authoring (zoom) | `c4-L3-blueprint-components.dot` | OEM → graph load |
| **L4** | Code | `c4-L4-code-modules.dot` | Key Python modules |
| **Deployment** | Kubernetes | `c4-deployment-kubernetes.dot` | K8s staging/prod |

### Dynamic views (interaction flows)

| Flow | Diagram |
|------|---------|
| Diagnosis | `c4-dynamic-diagnosis.dot` |
| Warranty claim | `c4-dynamic-claim.dot` |
| ETL batch | `c4-dynamic-etl.dot` |
| OEM blueprint | `c4-dynamic-blueprint.dot` |

### Supplementary (non-C4 but related)

| Topic | Location |
|-------|----------|
| Enterprise ERD | `../graphviz/34-enterprise-blueprint-ERD.dot` |
| Pipeline I/O | `../graphviz/36-end-to-end-pipeline-io.dot` |
| 6-layer architecture | `../graphviz/35-layer-architecture-symmetric.dot` |
| Module guide | `../PIPELINE-AND-MODULE-GUIDE.md` |

## Render

```bash
bash docs/c4/render.sh
```

Output: `docs/c4/rendered/png/` and `docs/c4/rendered/svg/`

**View on Mac:**
```bash
open docs/c4/rendered/png/c4-L2-containers.png
open docs/c4/rendered/png/   # all diagrams
```

## Structurizr Lite (optional)

```bash
brew install structurizr-cli   # if available
# Or download structurizr-lite.jar from structurizr.com
java -jar structurizr-lite.jar -workspace docs/c4
```

Open `http://localhost:8080` to browse interactive C4 views from `workspace.dsl`.

## C4 element legend

| Element | Shape / Color | Our examples |
|---------|---------------|--------------|
| Person | Blue ellipse | Customer, Agent, SME, Ops |
| Software System | Dark blue box | Diagnostics Platform, PIM, CRM |
| Container | Medium blue box | Streamlit, FastAPI, Neo4j, ETL |
| Component | Light blue box | GraphRAG, Claims Workflow, Orchestrator |
| Relationship | Labelled arrow | HTTPS, Cypher, Python invoke |

## Mapping to legacy diagrams

| C4 (canonical) | Legacy graphviz |
|----------------|-----------------|
| c4-L1 | 21-architecture-L1-system-context |
| c4-L2 | 22-architecture-L2-container |
| c4-L3-platform | 23-architecture-L3-component |
| c4-L4 | 24-architecture-L4-code |
| c4-deployment | 30-architecture-LLD-deployment-k8s |
| c4-dynamic-* | 25, 28, 36 |