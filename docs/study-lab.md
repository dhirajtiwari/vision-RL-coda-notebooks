# Study Lab — grounded interview trainer

**URL:** http://localhost:3000/study
**API:** `/study/*`

## Honest note on content changes

The “grounded” update **replaced** sparse auto/notebook-generated modules with shorter hand-authored lessons (clearer path, denser practice). That removed bulk from mock-derived notebook dumps — not to hide material, but to stop low-signal noise.

**Now restored/expanded:** a full **Flashcards master deck** (5W+H + authoritative sources) covering RDF/OWL/SHACL, Cypher, ETL, cache, threads, partition/CAP, Bayes/FMEA, LangGraph, ISO inspiration, and code snippets.

## Design principles

1. **Hand-authored lessons + authoritative flashcards** — not mock ETL dumps.
2. **Flashcards hub:** run every concept one-by-one with What/How/Where/When/Who/Why + citations.
3. **Lessons hub:** Learn → Say → Code → Quiz → Rewrite → Boss.
4. **Small code bites** in lessons; **code cards** in the deck.
5. Upload notes is **advanced** only (`grounded=false`).

## Curriculum order

### Graph / knowledge core
| # | Lesson | Track |
|---|--------|--------|
| 1 | TBox vs ABox | Foundations |
| 2 | Cypher create + read | Graph |
| 3 | ETL pipeline | Pipeline |
| 4 | Caching | Runtime |
| 5 | Multi-threading | Runtime |
| 6 | Partitioning | Runtime |
| 7 | Retrieval + Bayes | Graph |
| 8 | LangGraph agent | Agent |
| 9 | SHACL gates | Pipeline |

### Platform / LLMOps / ops expansion
| # | Lesson | Track |
|---|--------|--------|
| 10 | LLMOps disciplines map | LLMOps |
| 11 | Observability & monitoring | Observability |
| 12 | EvalOps gates | EvalOps |
| 13 | CI/CD GitHub Actions | CI/CD |
| 14 | Docker & Compose | Infra |
| 15 | Kubernetes, Helm, rollouts | Infra |
| 16 | Terraform / IaC | Infra |
| 17 | FinOps & cost estimation | FinOps |
| 18 | Security & guardrails | Security |
| 19 | Integrations (CRM/claims) | Integrations |
| 20 | Synthetic data, MLOps, images, AIOps | MLOps |

Flashcards hub expands the same topics with **5W+H + citations** (W3C, Neo4j, SRE, OWASP LLM, Helm, Terraform, FinOps Foundation, DDPM, etc.).

## How to practice (20–30 min per lesson)

1. **Learn** — read story + cheat sheet once.
2. **Say** — check every spoken line without peeking.
3. **Code** — read one bite; do fill-blanks.
4. **Quiz** — line MCQ + concept Q.
5. **Rewrite** — type beat from memory (≥70% token overlap as a guide).
6. **Boss** — oral/paper checklist; mark complete.

## Reset curriculum

```bash
python -m study.seed_curriculum
# or UI: Reset curriculum
# or POST /study/reseed
```

Wipes non-upload seed JSON and rewrites the 9 grounded modules.

## Code map

| Path | Role |
|------|------|
| `study/seed_curriculum.py` | Hand-authored modules |
| `study/generator.py` | Optional upload parser |
| `api/study_routes.py` | REST |
| `frontend/app/study/page.tsx` | Linear UI |
| `data/study_modules/` | JSON on disk |
