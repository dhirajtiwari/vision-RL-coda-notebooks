# Interview & mastery materials

Study materials for explaining **this repository** end-to-end in interviews, design reviews, and academic panels.

## Start here (recommended order)

| Order | Doc | Style | Use when |
|------:|-----|--------|----------|
| **1** | [`Master-This-Codebase.md`](Master-This-Codebase.md) | **Story → annotated code → quiz → practice → final boss** | Primary memorize/write/explain path (same narrative style as the small LangGraph “smart Cypher” study guides, but for *this* product’s real architecture) |
| **2** | [`../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md) | Status-tagged theory (AS-BUILT / LITE / ROADMAP) | Deep dive TBox origin, sparse data, scale, CAP, demo-vs-enterprise table |
| **3** | [`Interview-Mastery-Guide.md`](Interview-Mastery-Guide.md) | Persona Q&A + diagrams | 45–60 min panel drills by interviewer type |
| **4** | [`Remote-Diagnostics-Interview-Mastery-Guide.pdf`](Remote-Diagnostics-Interview-Mastery-Guide.pdf) | PDF export of the Q&A guide | Offline reading (regenerate via `generate_interview_pdf.py`) |

## Companion architecture docs

| Topic | Doc |
|-------|-----|
| TBox/ABox operator mechanism | [`../22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`](../22-TBox-ABox-Multi-Source-Onboard-Mechanism.md) |
| Ontology build + RDF | [`../15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md`](../15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md) |
| Runtime cache / Redis | [`../16-Enterprise-Runtime-Capabilities.md`](../16-Enterprise-Runtime-Capabilities.md) |
| Landscape / traversal | [`../17-Enterprise-Landscape-Pipeline-and-Topology.md`](../17-Enterprise-Landscape-Pipeline-and-Topology.md) |
| Indexes honesty | [`../19-Indexes-Constraints-and-Lookup-Performance.md`](../19-Indexes-Constraints-and-Lookup-Performance.md) |
| Code-true state | [`../sdd/AS_BUILT.md`](../sdd/AS_BUILT.md) |
| Gaps | [`../sdd/08-GAPS.md`](../sdd/08-GAPS.md) |

## Critical contrast (do not mix up)

Tutorial agents often end as **“LLM writes Cypher.”**
This product is **deterministic GraphRAG** (fixed parameterized Cypher + FMEA/Bayes). LLM is optional wording only.

That contrast is taught explicitly in **Master-This-Codebase** Module 0 and Module 5.

## Regenerate PDF

```bash
# from repo root, with reportlab installed
python docs/interview/generate_interview_pdf.py
```

Note: the PDF generator currently renders the **persona Q&A** guide structure. The **Master-This-Codebase** narrative is Markdown-first for study; use it in the editor or export separately if needed.
