# Multi-Volume Project Documentation

Complete reference for the **entire WarrantyGraph project** — architecture, **algorithms & theory**, **annotated code**, **RDF/OWL/Turtle**, pipelines, deploy, and tests.

| Volume | PDF | Focus |
|--------|-----|--------|
| **00** | `00-Master-Index.pdf` | Map of volumes + reading order |
| **01** | `01-Architecture-and-System-Map.pdf` | Product, layers, packages, APIs, network |
| **02** | `02-Algorithms-and-Theory.pdf` | FMEA, Bayes, TF-IDF hybrid, GraphRAG, parts scoring, decision trees |
| **03** | `03-Code-Deep-Dive-Annotated.pdf` | Real code excerpts + **what/why** for each |
| **04** | `04-Ontology-RDF-OWL-Turtle.pdf` | Schema, Turtle, OWL/RDF-XML, Neo4j mapping |
| **05** | `05-Pipelines-Deploy-Tests-Data.pdf` | ETL, k8s, evals, tests, data, **indexes WWWH** |

### Indexes (also standalone)

| Doc | Content |
|-----|---------|
| [`../19-Indexes-Constraints-and-Lookup-Performance.md`](../19-Indexes-Constraints-and-Lookup-Performance.md) | Neo4j constraints + SQLite indexes — What/Where/When/How/Why |

All volumes use a consistent **What · Where · When · How · Why** card format for major topics (not only indexes).

### Generate all PDFs

```bash
source venv/bin/activate
python docs/multi-volume/generate_all_volumes.py
```

### Related single docs

| Doc | Role |
|-----|------|
| `docs/18-FULL-PROJECT-CODEBASE-ENCYCLOPEDIA.md` | Single-file full inventory |
| `docs/full-project/*.pdf` | Compact encyclopedia PDF |
| `docs/interview/*.pdf` | Interview Q&A prep |

**This multi-volume set is the deep technical library** (theory + code + RDF).
