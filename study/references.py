"""Curated 'go deeper' literature for the Study Lab.

Every entry points at a **real, primary source** — a W3C standard, vendor docs,
a canonical paper, or a well-known book/repo — with the single idea to carry away
(`takeaway`) and why it matters for *this* warranty-diagnosis GraphRAG project
(`why`). The takeaways are distilled from reading the sources directly (W3C RDF
Primer, W3C SHACL Recommendation, Neo4j's GraphRAG guide, and Wozniak's SM-2
paper), not paraphrased from memory.

Keyed by module id so the store can attach them just like the Python cheat-codes.
`cross_cutting()` returns study-method + Python-fundamentals sources shown on
every module.
"""

from __future__ import annotations

from study.models import ReadingRef

_PY_DOCS = "Python docs"

# --- Sources every learner benefits from (study method + Python foundations) ---
_CROSS_CUTTING: list[ReadingRef] = [
    ReadingRef(
        title="SuperMemo: The SM-2 spaced-repetition algorithm",
        url="https://super-memory.com/english/ol/sm2.htm",
        author="P. A. Woźniak (1990)",
        kind="paper",
        level="core",
        takeaway=(
            "Intervals grow I(1)=1, I(2)=6, then I(n)=I(n-1)·EF; after each review "
            "EF' = EF + (0.1 − (5−q)(0.08 + (5−q)·0.02)), floored at 1.3; a grade "
            "q<3 resets the item to interval 1. Woźniak measured ~92% retention."
        ),
        why="This is the exact math behind the Today tab's Again/Hard/Good/Easy scheduler.",
    ),
    ReadingRef(
        title="The Zen of Python (PEP 20) & PEP 8 style guide",
        url="https://peps.python.org/pep-0020/",
        author="Tim Peters / Guido van Rossum et al.",
        kind="standard",
        level="intro",
        takeaway="'Explicit is better than implicit', 'Readability counts', 'There should be one obvious way'.",
        why="The style rules the codebase follows; interviewers expect you to name these.",
    ),
    ReadingRef(
        title="Fluent Python, 2nd ed. — idioms done the Pythonic way",
        url="https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/",
        author="Luciano Ramalho",
        kind="book",
        level="deep",
        takeaway="Data model (dunder methods), sequences, dict/set internals, closures, and typing — the 'why' behind idioms.",
        why="Best single reference to graduate from 'writing Python' to 'thinking in Python'.",
    ),
    ReadingRef(
        title="Real Python — practical, example-first tutorials",
        url="https://realpython.com/",
        author="Real Python",
        kind="tutorial",
        level="intro",
        takeaway="Searchable, task-focused walkthroughs (f-strings, context managers, type hints, asyncio, testing).",
        why="Quickest way to look up an unfamiliar idiom you meet in the code.",
    ),
]

REFERENCES: dict[str, list[ReadingRef]] = {
    # 01 — TBox/ABox, RDF, OWL (foundations)
    "01-tbox-abox-simple": [
        ReadingRef(
            title="RDF 1.1 Primer",
            url="https://www.w3.org/TR/rdf11-primer/",
            author="W3C (Schreiber & Raimond, eds.)",
            kind="standard",
            level="core",
            takeaway=(
                "Every fact is a triple ⟨subject, predicate, object⟩; IRIs are global "
                "identifiers usable by anyone; literals may appear ONLY in the object "
                "position; blank nodes name a thing without an IRI. Merging graphs = "
                "just union the triples."
            ),
            why="ABox (your instance data) is exactly a set of these triples.",
        ),
        ReadingRef(
            title="RDF Schema 1.1 (RDFS)",
            url="https://www.w3.org/TR/rdf-schema/",
            author="W3C (Brickley & Guha, eds.)",
            kind="standard",
            level="core",
            takeaway=(
                "rdfs:Class, rdf:type, rdfs:subClassOf, rdfs:domain/range let you "
                "declare a vocabulary. Entailment: 'bob knows alice' + 'knows domain "
                "Person' ⟹ 'bob a Person' is derivable."
            ),
            why="The TBox is this schema layer; sub-class/domain reasoning powers your diagnosis rules.",
        ),
        ReadingRef(
            title="OWL 2 Web Ontology Language — Primer",
            url="https://www.w3.org/TR/owl2-primer/",
            author="W3C OWL Working Group",
            kind="standard",
            level="deep",
            takeaway="OWL adds richer axioms (owl:sameAs, disjointness, cardinality, property characteristics) on top of RDF.",
            why="Explains how far a TBox can go beyond RDFS when you need real reasoning.",
        ),
    ],
    # 02 — Cypher / Neo4j (graph)
    "02-cypher-create-read": [
        ReadingRef(
            title="Neo4j Cypher Manual (current)",
            url="https://neo4j.com/docs/cypher-manual/current/",
            author="Neo4j",
            kind="docs",
            level="core",
            takeaway="Pattern syntax (node:Label)-[:REL]->(other); MERGE = get-or-create; parameters $x prevent injection & enable plan caching.",
            why="Every read/write in the graph layer is a Cypher statement of this shape.",
        ),
        ReadingRef(
            title="GQL — the ISO standard graph query language",
            url="https://www.iso.org/standard/76120.html",
            author="ISO/IEC 39075:2024",
            kind="standard",
            level="deep",
            takeaway="Graph querying is now an ISO standard (2024); Cypher is its most widely deployed dialect.",
            why="Context for why 'Cypher-like' patterns are a durable, transferable skill.",
        ),
    ],
    # 03 — ETL pipeline (pipeline)
    "03-etl-pipeline": [
        ReadingRef(
            title="Designing Data-Intensive Applications — Ch. 10-11 (batch/stream)",
            url="https://dataintensive.net/",
            author="Martin Kleppmann",
            kind="book",
            level="deep",
            takeaway="Idempotent, replayable stages with clear inputs/outputs; separate extract, transform, load so failures are recoverable.",
            why="The staging→validate→promote pipeline mirrors these batch-processing principles.",
        ),
        ReadingRef(
            title="The Log: real-time data's unifying abstraction",
            url="https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying-abstraction",
            author="Jay Kreps (LinkedIn)",
            kind="tutorial",
            level="core",
            takeaway="An append-only ordered log makes ingestion replayable and auditable — the backbone of reliable pipelines.",
            why="Explains why your provenance manifest/lineage is append-only.",
        ),
    ],
    # 04 — Caching (runtime)
    "04-caching": [
        ReadingRef(
            title="functools.lru_cache — Python standard library",
            url="https://docs.python.org/3/library/functools.html#functools.lru_cache",
            author=_PY_DOCS,
            kind="docs",
            level="intro",
            takeaway="@lru_cache(maxsize=N) memoises pure functions by args; least-recently-used eviction; .cache_clear() resets it.",
            why="The simplest correct cache in Python — used for hot, deterministic lookups.",
        ),
        ReadingRef(
            title="Caching at scale (cache-aside, TTL, invalidation)",
            url="https://redis.io/docs/latest/develop/use/patterns/",
            author="Redis",
            kind="docs",
            level="core",
            takeaway="Cache-aside: check cache → miss → load source → write cache with a TTL. Hardest part is invalidation, not lookup.",
            why="Your Redis-backed runtime cache follows the cache-aside pattern.",
        ),
    ],
    # 05 — Concurrency / threading (runtime)
    "05-multithreading": [
        ReadingRef(
            title="threading & the GIL",
            url="https://docs.python.org/3/library/threading.html",
            author=_PY_DOCS,
            kind="docs",
            level="core",
            takeaway="CPython's GIL means threads help I/O-bound work (waiting), not CPU-bound work — use processes for CPU parallelism.",
            why="Explains why the runtime uses threads for network/DB waits, not number crunching.",
        ),
        ReadingRef(
            title="concurrent.futures — high-level pools",
            url="https://docs.python.org/3/library/concurrent.futures.html",
            author=_PY_DOCS,
            kind="docs",
            level="intro",
            takeaway="ThreadPoolExecutor / ProcessPoolExecutor + submit()/map() give you futures without manual thread management.",
            why="The safe, modern way to fan out concurrent calls in the codebase.",
        ),
    ],
    # 06 — Partitioning / sharding (pipeline/runtime)
    "06-partitioning": [
        ReadingRef(
            title="Designing Data-Intensive Applications — Ch. 6 (Partitioning)",
            url="https://dataintensive.net/",
            author="Martin Kleppmann",
            kind="book",
            level="deep",
            takeaway="Partition by key range or hash to spread load; beware hot keys/skew; rebalancing must avoid moving all data.",
            why="Underlies how the graph/data layer is split for scale.",
        ),
    ],
    # 07 — GraphRAG retrieval + Bayesian ranking (agent/graph)
    "07-retrieval-bayes": [
        ReadingRef(
            title="What is GraphRAG?",
            url="https://neo4j.com/blog/genai/what-is-graphrag/",
            author="Michael Hunger, Neo4j",
            kind="docs",
            level="core",
            takeaway=(
                "RAG = retrieve → augment → generate, answering ONLY from retrieved "
                "context. Vector-only RAG returns isolated, unexplainable chunks; "
                "GraphRAG finds starting points (vector/fulltext) then traverses "
                "relationships (neighbourhood/path) for multi-hop, explainable answers."
            ),
            why="This is the core retrieval strategy your diagnosis engine implements.",
        ),
        ReadingRef(
            title="GraphRAG: unlocking LLM discovery on narrative private data",
            url="https://github.com/microsoft/graphrag",
            author="Microsoft Research",
            kind="repo",
            level="deep",
            takeaway="Community-detection + query-focused summarisation for global questions over a corpus.",
            why="The other major GraphRAG design; good contrast to Neo4j's traversal approach.",
        ),
        ReadingRef(
            title="neo4j-graphrag Python package",
            url="https://neo4j.com/blog/news/graphrag-python-package/",
            author="Neo4j",
            kind="tutorial",
            level="core",
            takeaway="VectorCypherRetriever: vector search for entry chunks, then a Cypher retrieval_query expands 1-2 hops.",
            why="A concrete, code-level template for the retrieve-then-traverse pattern.",
        ),
    ],
    # 08 — LangGraph agent (agent)
    "08-langgraph-agent": [
        ReadingRef(
            title="LangGraph documentation",
            url="https://langchain-ai.github.io/langgraph/",
            author="LangChain",
            kind="docs",
            level="core",
            takeaway="Model the agent as a state graph: nodes mutate a typed state, edges (incl. conditional) route control; supports checkpoints.",
            why="Your diagnosis_graph is exactly such a state machine of tool-using nodes.",
        ),
        ReadingRef(
            title="ReAct: Synergizing Reasoning and Acting in Language Models",
            url="https://arxiv.org/abs/2210.03629",
            author="Yao et al., 2022",
            kind="paper",
            level="deep",
            takeaway="Interleave 'thought → action → observation' loops so the model plans, calls tools, then revises.",
            why="The reasoning pattern behind tool-calling agents like yours.",
        ),
    ],
    # 09 — SHACL validation gates (foundations/pipeline)
    "09-shacl-gates": [
        ReadingRef(
            title="Shapes Constraint Language (SHACL) — W3C Recommendation",
            url="https://www.w3.org/TR/shacl/",
            author="W3C (Knublauch & Kontokostas, eds.)",
            kind="standard",
            level="core",
            takeaway=(
                "A shapes graph validates a data graph. NodeShape + sh:targetClass "
                "picks focus nodes; property shapes add sh:minCount/sh:datatype/"
                "sh:pattern/sh:class/sh:closed. Output is a ValidationReport with "
                "sh:conforms (bool) and one sh:result per violation, each with a "
                "severity (Info/Warning/Violation)."
            ),
            why="These are the exact gates that block bad data from promotion in your pipeline.",
        ),
        ReadingRef(
            title="SHACL Advanced Features & SPARQL constraints",
            url="https://www.w3.org/TR/shacl-af/",
            author="W3C",
            kind="standard",
            level="deep",
            takeaway="When Core shapes aren't enough, sh:sparql lets a SELECT/ASK query express arbitrary constraints.",
            why="Shows the escape hatch for validation rules your domain needs beyond Core.",
        ),
    ],
}


def reading_for(module_id: str) -> list[ReadingRef]:
    """Return curated further-reading for a module, always including the shared
    study-method + Python-foundations sources."""
    specific = REFERENCES.get(module_id, [])
    return [r.model_copy() for r in (specific + _CROSS_CUTTING)]


def cross_cutting() -> list[ReadingRef]:
    return [r.model_copy() for r in _CROSS_CUTTING]


def library() -> list[dict]:
    """All curated sources grouped for a global 'Library' view."""
    out: list[dict] = []
    for module_id, refs in REFERENCES.items():
        out.append({"module_id": module_id, "sources": [r.model_dump() for r in refs]})
    out.append({"module_id": "_cross_cutting", "sources": [r.model_dump() for r in _CROSS_CUTTING]})
    return out
