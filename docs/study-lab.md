# Study Lab — modular interview trainer

**UI:** [http://localhost:3000/study](http://localhost:3000/study)
**API:** `http://localhost:8080/study/*`
**Code:** `study/`, `api/study_routes.py`, `frontend/app/study/`

## Purpose

Learn and **memorize** the warranty-graph stack the same way the “Master This Code” guides work:

| Mode | What you do |
|------|-------------|
| Story | Retell the memory anchor |
| Annotated | Read code with line notes |
| Line quiz | Multiple choice per critical line |
| Fill blanks | Recall tokens |
| Blank write | Type the whole beat from memory |
| Flashcards | Concept terms |
| Self-quiz | Q&A without peeking |
| Final boss | Integrated oral / write checks |

Seed topics (from notebook + platform):

1. Platform lineage (dual graph / wizard)
2. RDF/OWL TBox→ABox + Turtle
3. SPARQL + Cypher create/read + shortestPath
4. LangGraph smart-Cypher tools **vs** deterministic GraphRAG
5. Cache / threads / partition
6. Fast accurate retrieval + Bayes
7. SHACL / quality gates
8. Auto module from `notebooks/rdf_owl_langgraph_tutorial.ipynb` (if present)

## Tomorrow’s topic = new module

1. Open **Study Lab → New module**
2. Upload `.md` / `.ipynb` / `.ttl` / `.cypher` / `.py` **or** paste markdown with fenced code
3. Backend **generates** story, beats, annotations, line quizzes, fill-blanks, concepts
4. Module appears in the sidebar under `data/study_modules/`

No LLM required (deterministic generator). Optional later: call gateway when `llm_enabled`.

## API

| Method | Path | Role |
|--------|------|------|
| GET | `/study/modules` | List summaries |
| GET | `/study/modules/{id}` | Full module |
| POST | `/study/modules/generate` | JSON text → module |
| POST | `/study/modules/upload` | multipart file → module |
| POST | `/study/grade/fill-blanks` | Score fill practice |
| POST | `/study/grade/line-quiz` | Score line MCQ |
| POST | `/study/reseed` | Rewrite seed JSON files |

## Reseed CLI

```bash
source venv/bin/activate
python -m study.seed_curriculum
```
