# Documentation reading order (WarrantyGraph / remote diagnostics)

Use this so older and newer docs do not fight each other.

## Always current (prefer these)

| Priority | Doc | Why |
|---------:|-----|-----|
| 1 | [`sdd/`](sdd/README.md) | Agent + platform contract (AS_BUILT, NEVER, MUST) |
| 2 | [`22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`](22-TBox-ABox-Multi-Source-Onboard-Mechanism.md) | How onboarding works day-to-day |
| 3 | [`24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md) | **Canonical** TBox origin, sparse data, scale, CAP, demo-vs-enterprise |
| 3b | [`25-Delta-Partitioning-Concurrency-Sharding-Implementation.md`](25-Delta-Partitioning-Concurrency-Sharding-Implementation.md) | Delta stepping, partition, threads, sharding — **as-built + how to implement** |
| 4 | [`15`](15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md)–[`21`](21-KG-Ingestion-Step-by-Step-Runbook.md) MD series | Build, runtime, landscape, indexes, ingest |
| 5 | [`interview/Master-This-Codebase.md`](interview/Master-This-Codebase.md) | Memorize / write / explain narrative |
| 6 | [`interview/Interview-Mastery-Guide.md`](interview/Interview-Mastery-Guide.md) | Persona Q&A appendix |

## Historical / supplementary (read with care)

| Set | Notes |
|-----|--------|
| `docs/01`–`14` **`.docx`** | Strong diagrams and early deep-dives. Some **predate TBox/ABox wording** and dual-graph multi-source detail. Prefer MD 15–24 for ontology platform truth. Doc **02** hybrid vector section = **target pattern**, not as-built (see doc 19 + 24). Doc **14** = operational chain; may omit TBox/ABox labels. |
| `docs/llmops-handbook/` | Human recipes — do not dump whole book into agent context |
| `docs/18` encyclopedia / multi-volume PDFs | Broad reference; still defer to AS_BUILT for “is it done?” |

## Interview study path

1. [`interview/README.md`](interview/README.md)
2. Master-This-Codebase (one module per sitting)
3. Doc 24 status tables
4. Persona Q&A drills

## One-line product truth

**Shared TBox once; multi-source ABox in; shape-check; promote staging→production; deterministic GraphRAG + Bayes out; LLM optional and off by default.**
