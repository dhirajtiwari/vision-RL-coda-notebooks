# Ontology Build Pipeline, RDF/OWL Export, and Topology Decision

**Audience:** engineers, solution architects, and OEM knowledge stewards
**Scope:** how the warranty-diagnosis ontology is authored, transformed, loaded, and optionally exported as RDF/OWL
**Related:** `docs/PIPELINE-AND-MODULE-GUIDE.md`, `docs/14-Enterprise-Warranty-Diagnosis-Ontology-and-Industry-Alignment.docx`, `graph/rdf_ontology_export.py`

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| **How is the ontology built?** | **Blueprints + connectors → `OntologyBuilder` → catalog JSON → `populate_graph` → Neo4j** |
| **Is “topology” a separate unfinished capability?** | **No.** For this application, product-structure / equipment-hierarchy concerns are already modeled inside the ontology (Component, BOM edges, Model/SKU). Infrastructure “topology” (K8s, connectors) is ops documentation, not a second knowledge model. |
| **Do we need a parallel Topology subsystem?** | **No** — building one would duplicate work and drift from the graph used by diagnosis. |
| **How do we get formal RDF/OWL?** | Export TBox + ABox via `python -m graph.rdf_ontology_export` (Turtle or RDF/XML). |

---

## 2. Topology vs ontology — authoritative distinction

### 2.1 What standards say

| Source | What it defines | Relevance here |
|--------|-----------------|----------------|
| **[W3C OWL](https://www.w3.org/TR/owl-ref/)** / **[OWL 2](https://www.w3.org/TR/owl2-overview/)** | **Ontology** = classes, properties, individuals, axioms (schema + optional logic). | Our entity types (`Product`, `Symptom`, `FailureMode`, …) and object properties (`indicates`, `requiresPart`, …) are an OWL TBox when exported. |
| **[W3C RDF 1.1](https://www.w3.org/TR/rdf11-concepts/)** / **[RDFS](https://www.w3.org/TR/rdf-schema/)** | Graphs of subject–predicate–object triples; RDFS adds class/property hierarchy. | Catalog instances export as RDF ABox; Neo4j is the operational property-graph store for GraphRAG. |
| **[W3C SOSA/SSN](https://www.w3.org/TR/vocab-ssn/)** | Sensors, observations, procedures, features of interest. | Useful if we later attach live IoT observations; **not** required for current warranty chat diagnosis. |
| **W3C LBD [Building Topology Ontology (BOT)](https://www.w3.org/community/lbd/)** | **Topology of buildings**: storeys, spaces, containment, adjacency. | Domain-specific to AEC; **not** the right model for appliance warranty diagnosis. |
| **[ISO 14224](https://www.iso.org/standard/64076.html)** | Reliability data collection: **equipment hierarchy** + failure taxonomy (mode, cause, mechanism). | Equipment hierarchy ≈ our **Product → Component** structure; failure taxonomy ≈ **FailureMode** + links. |
| **[ISO/IEC 81346](https://www.iso.org/standard/82229.html)** | Reference designation: **function / product / location** aspects of system structure. | **Product aspect** of structure is our BOM/Component graph; we do not model plant-floor location aspect for this demo. |

### 2.2 Definitions used in this product

| Term | Meaning in *this* application |
|------|--------------------------------|
| **Ontology (schema / TBox)** | Allowed node labels, relationship types, properties, and meaning (what *can* connect to what). Exposed as ER-style UI via `get_ontology_schema()` and as OWL via RDF export. |
| **Knowledge graph (ABox)** | Concrete products, symptoms, parts, claims in Neo4j after ETL. |
| **Product structure (sometimes called “topology” in industry)** | Hierarchical composition: Product / Model / SKU / Component / Part. Implemented as ontology classes + edges `IMPACTS_COMPONENT`, `REALIZED_BY`, `COMPATIBLE_WITH`. |
| **Diagnostic path structure** | Decision tree of steps: `NEXT_STEP`, `CONFIRMS`, `RULES_OUT`. |
| **Deployment topology** | How API, Neo4j, UI, connectors are deployed (diagrams 27, 30). Ops concern only. |

### 2.3 Decision: no separate Topology workstream

Authoritative sources that use the word **topology** either:

1. mean **spatial/building topology** (BOT) — out of scope, or
2. mean **system / product structure** (ISO 14224 hierarchy, IEC 81346 product aspect) — **already in the warranty ontology**.

Therefore:

- We **do not** introduce `TopologyBuilder`, `Topology` nodes, or a parallel API.
- Product-structure requirements are satisfied by **extending the same ontology** (e.g. deeper BOM levels, `SUPERSEDES` for parts) if OEMs need more detail later.
- Connector/K8s diagrams remain the home for **deployment** topology.

---

## 3. How the ontology is built (end-to-end)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 0  OEM / legacy BLUEPRINTS                                        │
│  oem_product_catalog.py · warranty_catalog_extensions.py                 │
│  synthetic_data_generator.py                                             │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 1  FIXTURE SYNC (optional)                                        │
│  pim_blueprint_sync → pim_catalog.json · enterprise_knowledge_catalog    │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 2  CONNECTORS + OntologyBuilder                                   │
│  PIM · FSM · Claims · CRM  →  OntologyBuilder.build_catalog_payload()    │
│  → synthetic_diagnosis_data.json  (+ provenance, etl_batch_id)           │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Phase 3  populate_graph.py                                              │
│  MERGE nodes & relationships into Neo4j (operational knowledge graph)    │
└───────────────────────────────┬──────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Runtime   GraphRAG · reliability · diagnostic_engine · parts_predictor  │
│  Optional  python -m graph.rdf_ontology_export  →  Turtle / RDF-XML      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Phase 0 — Blueprints (authoritative product knowledge)

**Purpose:** encode OEM diagnostic knowledge before any ETL run.

| Module | Responsibility |
|--------|----------------|
| `graph/oem_product_catalog.py` | Per-SKU builders: symptoms, failure modes, steps, parts, error codes, components, link tables. |
| `graph/warranty_catalog_extensions.py` | Model/SKU, Component BOM, FM↔component, assets, policies, sample claims. |
| `graph/synthetic_data_generator.py` | Typed models (`Product`, `Symptom`, …) and legacy 3-product demo generators. |

**Conceptual object:** one nested Python/JSON product record with:

- entity lists (`symptoms`, `failure_modes`, `parts`, `components`, …)
- link lists (`symptom_failure_links`, `failure_mode_part_links`, `component_part_links`, …)

Those links are the **edges** of the future graph.

### 3.2 Phase 1 — Fixture sync

Command (when used):

```bash
python -m graph.enterprise_pipeline.transformers.pim_blueprint_sync
```

Writes enterprise-facing fixtures under `data/enterprise_sources/` and the full catalog `data/enterprise_knowledge_catalog.json`.

### 3.3 Phase 2 — Connectors + `OntologyBuilder`

Entry: `graph/enterprise_pipeline/pipelines/knowledge_etl.py` → `run_knowledge_etl()`.

1. **Extract** via connectors (`PIMConnector`, `FSMConnector`, `ClaimsConnector`, `CRMConnector`) — HTTP mock API or JSON fixture fallback.
2. **Transform** with `OntologyBuilder`:
   - map PIM products into `ProductKnowledge`
   - raise `INDICATES` confidence from FSM + claims co-occurrence
   - merge historical resolutions
   - attach PROV-style provenance dict
   - call `build_enterprise_catalog_payload()` for enterprise extensions
3. **Write** catalog JSON (`settings.data_file` / enterprise catalog).

Core transform (simplified):

```python
builder = OntologyBuilder(etl_batch_id=report.batch_id)
catalog = builder.build_catalog_payload(
    pim=fetched["PIM"],
    fsm=fetched["FSM"],
    claims=fetched["Claims"],
    crm=fetched.get("CRM"),
)
# catalog = { "products": [...], "provenance": {...}, "etl_batch_id": "...", ... }
```

### 3.4 Phase 3 — Load Neo4j

`graph/populate_graph.py` → `populate_graph(driver, data)`:

- creates uniqueness constraints per label
- `MERGE`s each entity
- `MERGE`s relationships (`HAS_SYMPTOM`, `INDICATES`, `REQUIRES_PART`, `IMPACTS_COMPONENT`, `REALIZED_BY`, …)

Neo4j is the **runtime** source of truth for diagnosis. RDF export is **interoperability / documentation**, not a second live store.

### 3.5 Runtime consumers

| Consumer | Graph usage |
|----------|-------------|
| `graph/graph_rag.py` | Match symptoms/error codes; rank failure modes |
| `graph/reliability.py` | FMEA S/O/D + Bayesian posterior from graph counts/edges |
| `graph/diagnostic_engine.py` | Walk diagnostic step graph |
| `graph/parts_predictor.py` | `REQUIRES_PART` + BOM path + SKU fit + claim precedent |

---

## 4. Entity–relationship contract (ontology schema)

### 4.1 Classes (node labels)

| Class | Identity key | Role |
|-------|--------------|------|
| Product | `product_id` | Catalog product family |
| Model | `model_id` | Engineering model |
| SKU | `sku_id` | Revision / sellable unit |
| Asset | `asset_id` | Installed serial |
| Symptom | `symptom_id` | Observed issue |
| ErrorCode | `error_code_id` | Device code |
| FailureMode | `failure_mode_id` | Diagnosed fault |
| DiagnosticStep | `step_id` | Troubleshoot / confirm |
| Component | `component_id` | BOM subsystem (**product structure**) |
| Part | `part_id` | Replaceable part |
| Claim | `claim_id` | Warranty case |
| HistoricalResolution | `resolution_id` | Closed repair precedent |
| WarrantyPolicy | `policy_id` | Coverage rules |

### 4.2 Core relationships

```
Product ──HAS_MODEL──► Model ──HAS_SKU──► SKU
Asset ──INSTANCE_OF──► Product
Asset ──BOUND_TO_SKU──► SKU
Product ──HAS_SYMPTOM──► Symptom ──INDICATES {confidence}──► FailureMode
Product ──HAS_ERROR_CODE──► ErrorCode ──INDICATES──► FailureMode
Product ──CAN_HAVE──► FailureMode
Product ──HAS_DIAGNOSTIC_STEP──► DiagnosticStep ──CONFIRMS|RULES_OUT──► FailureMode
DiagnosticStep ──NEXT_STEP──► DiagnosticStep
FailureMode ──IMPACTS_COMPONENT──► Component ──REALIZED_BY──► Part
FailureMode ──REQUIRES_PART {qty, probability}──► Part
SKU ──COMPATIBLE_WITH──► Part
Claim ──CONFIRMED──► FailureMode
Claim ──USED_PART──► Part
```

Static schema payload for UI: `graph/graph_visualization.get_ontology_schema()` → `GET /graph/ontology`.

### 4.3 Product structure vs “topology”

The **industrial product-structure** chain used for “which subsystem is hit?” is:

```
FailureMode ─IMPACTS_COMPONENT→ Component ─REALIZED_BY→ Part
```

This is the same concern ISO 14224 / IEC 81346 address as equipment/product hierarchy. It is **not** missing; it is **not** a second system.

---

## 5. Provenance and lineage

- **Per-entity provenance** on catalog load (`source_system`, `source_record_id`, `source_document_uri`, `approval_status`) — aligned with W3C **PROV-O** *entity/activity/agent* ideas in `graph/provenance.py`.
- **Batch lineage** in `data/lineage/etl_batches.jsonl` via `utils/lineage_store.py`.
- Demo fixtures may be tagged **simulated** so they are not mistaken for live SAP/PIM sync.

---

## 6. RDF and OWL — formal export

Runtime diagnosis uses **Neo4j property graphs**. Formal semantic-web interchange uses **RDF triples** and **OWL** vocabulary. Both describe the same conceptual model.

| Layer | Store / artifact | Role |
|-------|------------------|------|
| TBox (schema) | OWL classes + properties | Shared meaning |
| ABox (instances) | Product/symptom/… individuals | Data |
| Operational graph | Neo4j | Fast multi-hop Cypher for agents |

### 6.1 Run the exporter

```bash
# Full schema + instances (Turtle)
python -m graph.rdf_ontology_export

# Schema only
python -m graph.rdf_ontology_export --schema-only \
  --out docs/ontology/warranty-diagnosis-schema.ttl

# One product ABox + schema
python -m graph.rdf_ontology_export --product-id wm-001 \
  --out docs/ontology/wm-001.ttl

# RDF/XML (OWL document with schema + small example)
python -m graph.rdf_ontology_export --format rdfxml \
  --out docs/ontology/warranty-diagnosis.owl
```

Module: `graph/rdf_ontology_export.py` (stdlib only; no `rdflib` required).

### 6.2 Turtle example — TBox fragment

```turtle
@prefix wd:   <https://example.org/warranty-diagnosis#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

<https://example.org/warranty-diagnosis/ontology> a owl:Ontology ;
  rdfs:label "Enterprise Warranty Diagnosis Ontology" ;
  owl:versionInfo "1.0.0" .

wd:Product      a owl:Class ; rdfs:label "Product" .
wd:Symptom      a owl:Class ; rdfs:label "Symptom" .
wd:FailureMode  a owl:Class ; rdfs:label "FailureMode" .
wd:Component    a owl:Class ; rdfs:label "Component" .
wd:Part         a owl:Class ; rdfs:label "Part" .

wd:hasSymptom a owl:ObjectProperty ;
  rdfs:domain wd:Product ; rdfs:range wd:Symptom .

wd:indicates a owl:ObjectProperty ;
  rdfs:domain wd:Symptom ; rdfs:range wd:FailureMode .

wd:impactsComponent a owl:ObjectProperty ;
  rdfs:domain wd:FailureMode ; rdfs:range wd:Component .

wd:realizedBy a owl:ObjectProperty ;
  rdfs:domain wd:Component ; rdfs:range wd:Part .

wd:requiresPart a owl:ObjectProperty ;
  rdfs:domain wd:FailureMode ; rdfs:range wd:Part .
```

### 6.3 Turtle example — ABox fragment (washing machine drain path)

```turtle
wd:product_wm-001 a wd:Product ;
  wd:productId "wm-001" ;
  wd:name "AquaHome Front Load 8kg" ;
  wd:hasSymptom wd:symptom_wm-s03 ;
  wd:canHave wd:fm_wm-fm02 .

wd:symptom_wm-s03 a wd:Symptom ;
  wd:description "Will not drain / E21" ;
  wd:severity "high" ;
  wd:indicates wd:fm_wm-fm02 .

wd:fm_wm-fm02 a wd:FailureMode ;
  rdfs:label "Drain pump failure" ;
  wd:impactsComponent wd:component_wm-c02 ;
  wd:requiresPart wd:part_wm-p02 .

wd:component_wm-c02 a wd:Component ;
  rdfs:label "Drain System" ;
  wd:subsystem "Plumbing" ;
  wd:realizedBy wd:part_wm-p02 .

wd:part_wm-p02 a wd:Part ;
  rdfs:label "Drain pump" ;
  wd:partNumber "DP-8K-01" .
```

### 6.4 Python: write ontology RDF programmatically

The application module encapsulates this. Minimal **stdlib** pattern (same idea as the exporter):

```python
from pathlib import Path

WD = "https://example.org/warranty-diagnosis#"

def write_minimal_owl(path: Path) -> None:
    """Write a tiny OWL/RDF-XML file for Product → Symptom → FailureMode → Part."""
    rdf = f'''<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:wd="{WD}">
  <owl:Ontology rdf:about="https://example.org/warranty-diagnosis/ontology"/>
  <owl:Class rdf:about="{WD}Product"/>
  <owl:Class rdf:about="{WD}Symptom"/>
  <owl:Class rdf:about="{WD}FailureMode"/>
  <owl:Class rdf:about="{WD}Part"/>
  <owl:ObjectProperty rdf:about="{WD}hasSymptom">
    <rdfs:domain rdf:resource="{WD}Product"/>
    <rdfs:range rdf:resource="{WD}Symptom"/>
  </owl:ObjectProperty>
  <owl:ObjectProperty rdf:about="{WD}indicates">
    <rdfs:domain rdf:resource="{WD}Symptom"/>
    <rdfs:range rdf:resource="{WD}FailureMode"/>
  </owl:ObjectProperty>
  <owl:ObjectProperty rdf:about="{WD}requiresPart">
    <rdfs:domain rdf:resource="{WD}FailureMode"/>
    <rdfs:range rdf:resource="{WD}Part"/>
  </owl:ObjectProperty>
  <wd:Product rdf:about="{WD}product_wm-001">
    <wd:name>AquaHome Front Load 8kg</wd:name>
    <wd:hasSymptom rdf:resource="{WD}symptom_wm-s03"/>
  </wd:Product>
  <wd:Symptom rdf:about="{WD}symptom_wm-s03">
    <wd:description>Will not drain</wd:description>
    <wd:indicates rdf:resource="{WD}fm_wm-fm02"/>
  </wd:Symptom>
  <wd:FailureMode rdf:about="{WD}fm_wm-fm02">
    <rdfs:label>Drain pump failure</rdfs:label>
    <wd:requiresPart rdf:resource="{WD}part_wm-p02"/>
  </wd:FailureMode>
  <wd:Part rdf:about="{WD}part_wm-p02">
    <rdfs:label>Drain pump</rdfs:label>
  </wd:Part>
</rdf:RDF>
'''
    path.write_text(rdf, encoding="utf-8")

# write_minimal_owl(Path("docs/ontology/minimal-example.owl"))
```

Or export from the live catalog:

```python
from pathlib import Path
from graph.rdf_ontology_export import export_ontology, catalog_to_turtle, load_catalog

# Full pipeline export
export_ontology(
    out_path=Path("docs/ontology/warranty-diagnosis.ttl"),
    fmt="turtle",
    product_ids=["wm-001"],
)

# Or build a string in memory
ttl = catalog_to_turtle(load_catalog(), product_ids=["wm-001"])
print(ttl[:500])
```

### 6.5 Mapping Neo4j ↔ RDF

| Neo4j | RDF / OWL |
|-------|-----------|
| Node label `Product` | `rdf:type wd:Product` |
| Property `product_id` | `wd:productId` (datatype property) |
| Rel type `HAS_SYMPTOM` | Object property `wd:hasSymptom` |
| Rel type `INDICATES` + prop `confidence` | `wd:indicates` + OWL annotation axiom with `wd:confidence` |
| Rel type `IMPACTS_COMPONENT` | `wd:impactsComponent` (product structure) |
| Rel type `REALIZED_BY` | `wd:realizedBy` |

---

## 7. Worked pipeline commands

```bash
# Activate project venv
source venv/bin/activate

# 1) Authoritative catalog / synthetic refresh (as used in demo scripts)
python -m graph.synthetic_data_generator

# 2) Enterprise ETL (catalog only)
python -c "from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl; print(run_knowledge_etl())"

# 3) Load Neo4j
python graph/populate_graph.py

# 4) Export OWL/Turtle for review or enterprise semantic stack
python -m graph.rdf_ontology_export --product-id wm-001
```

Orchestrator entry (all batch pipelines):

```bash
python -m graph.enterprise_pipeline.orchestrator
```

---

## 8. What is deliberately *not* a separate “topology project”

| Request | Disposition |
|---------|-------------|
| Building-style spatial topology (BOT) | Out of scope for appliance warranty chat. |
| New `Topology` node type parallel to Component | Rejected — use Component/BOM edges. |
| Network device topology | Out of scope unless product domain changes. |
| Deployment topology | Already covered by architecture diagrams / K8s docs. |
| Multi-level nested BOM | **Future ontology extension**, not a new subsystem. |
| Part supersession chains | **Future ontology extension** (`SUPERSEDES`). |
| Richer NEXT_STEP trees | **Future diagnostic-structure extension** on existing classes. |

---

## 9. File map

| Path | Role |
|------|------|
| `graph/oem_product_catalog.py` | Blueprint authoring |
| `graph/warranty_catalog_extensions.py` | Model/SKU/BOM/asset/claim extensions |
| `graph/enterprise_pipeline/transformers/ontology_builder.py` | ETL transform → catalog |
| `graph/enterprise_pipeline/pipelines/knowledge_etl.py` | Extract → transform → write → optional load |
| `graph/populate_graph.py` | JSON → Neo4j MERGE |
| `graph/graph_visualization.py` | Schema + subgraph for UI/API |
| `graph/rdf_ontology_export.py` | RDF/OWL Turtle + RDF/XML export |
| `docs/ontology/` | Generated / sample ontology files |
| `data/synthetic_diagnosis_data.json` | Runtime catalog ABox source |

---

## 10. References (official / standards bodies)

1. W3C, *OWL Web Ontology Language Reference*, https://www.w3.org/TR/owl-ref/
2. W3C, *OWL 2 Web Ontology Language Document Overview*, https://www.w3.org/TR/owl2-overview/
3. W3C, *RDF 1.1 Concepts and Abstract Syntax*, https://www.w3.org/TR/rdf11-concepts/
4. W3C, *RDF Schema 1.1*, https://www.w3.org/TR/rdf-schema/
5. W3C, *Semantic Sensor Network Ontology (SOSA/SSN)*, https://www.w3.org/TR/vocab-ssn/
6. W3C Linked Building Data CG, Building Topology Ontology (BOT) materials, https://www.w3.org/community/lbd/
7. ISO 14224, *Petroleum, petrochemical and natural gas industries — Collection and exchange of reliability and maintenance data for equipment*, https://www.iso.org/standard/64076.html
8. ISO/IEC 81346 series, *Industrial systems, installations and equipment and industrial products — Structuring principles and reference designations*, https://www.iso.org/standard/82229.html
9. W3C, *PROV-O: The PROV Ontology*, https://www.w3.org/TR/prov-o/

---

## 11. Conclusion

- **Ontology construction** is a single pipeline: **blueprints + connectors → OntologyBuilder → catalog JSON → populate_graph → Neo4j**, with optional **RDF/OWL export**.
- **Topology**, in the only sense that applies to warranty diagnosis product structure, is **already implemented** as Component/BOM and Model/SKU structure inside that ontology.
- **No separate topology capability** should be built; deepen the same schema when OEMs need richer structure.
