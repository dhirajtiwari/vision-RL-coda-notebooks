"""
Authoritative flashcard deck for Study Lab.

Cards are hand-authored with 5W+H and citations to standards/docs/papers.
This is NOT derived from mock ETL dumps.
"""

from __future__ import annotations

import json
from pathlib import Path

from study.models import FlashCard, SourceRef
from study.store import MODULES_DIR

FLASH_DIR = MODULES_DIR.parent / "study_flashcards"
FLASH_FILE = FLASH_DIR / "deck.json"


def _s(title: str, url: str = "", kind: str = "docs") -> SourceRef:
    return SourceRef(title=title, url=url, kind=kind)  # type: ignore[arg-type]


def build_deck() -> list[FlashCard]:
    cards: list[FlashCard] = []

    # ── RDF / OWL / DL ────────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-rdf-triple",
            front="RDF triple",
            track="foundations",
            tags=["rdf", "graph", "data-model"],
            kind="concept",
            what="The atomic fact in RDF: subject–predicate–object (s, p, o).",
            how="Assert with rdflib Graph.add((s,p,o)) or write Turtle; store as a directed labeled edge.",
            where="Semantic web stacks, ontology exports (docs/ontology/*.ttl), knowledge interchange.",
            when="When you need a formal, mergeable, schema-aware graph of facts across systems.",
            who="Knowledge engineers, data stewards; W3C RDF Working Group defines the model.",
            why="One shared data model for meaning + facts; tools can reason and validate over it.",
            analogy="One spreadsheet cell relation, but globally named with IRIs.",
            code="g.add((WD.Symptom, WD.indicates, WD.FailureMode))",
            language="python",
            say_aloud="An RDF triple is one subject-predicate-object fact.",
            sources=[
                _s(
                    "W3C RDF 1.1 Concepts and Abstract Syntax",
                    "https://www.w3.org/TR/rdf11-concepts/",
                    "standard",
                ),
            ],
            related_module_ids=["01-tbox-abox-simple"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-tbox",
            front="TBox (Terminological Box)",
            track="foundations",
            tags=["tbox", "owl", "schema", "dl"],
            kind="theory",
            what="The schema layer in Description Logic / OWL: classes, properties, axioms (the vocabulary).",
            how="Declare owl:Class, ObjectProperty/DatatypeProperty, domain/range, optional restrictions.",
            where="Shared domain ontology (rdf_ontology_export, warranty-diagnosis-schema.ttl) — not per product.",
            when="Once per domain; change only when new kinds of entities/relations appear.",
            who="Ontology/governance owners; formalized in Baader et al. Description Logic handbook tradition.",
            why="One rule book scales; new products become ABox without inventing new languages.",
            analogy="SQL CREATE TABLE / ER schema.",
            code="g.add((WD.Product, RDF.type, OWL.Class))",
            language="python",
            pitfalls=["Creating a new TBox file per SKU", "Confusing Neo4j labels with a governed TBox"],
            say_aloud="TBox is the rule book of classes and relationships.",
            sources=[
                _s("W3C OWL 2 Primer", "https://www.w3.org/TR/owl2-primer/", "standard"),
                _s(
                    "Baader et al., The Description Logic Handbook (Cambridge)",
                    "https://www.cambridge.org/core/books/description-logic-handbook/",
                    "book",
                ),
            ],
            related_module_ids=["01-tbox-abox-simple"],
        ),
        FlashCard(
            id="fc-abox",
            front="ABox (Assertional Box)",
            track="foundations",
            tags=["abox", "instances", "owl"],
            kind="theory",
            what="Instance facts: this individual is a Product; this Symptom INDICATES that FailureMode.",
            how="Create individuals typed by TBox classes; assert property links between them.",
            where="Product packs, catalog JSON, Neo4j operational graph after promote.",
            when="Every new product, bulletin, claim precedent, or asset registration.",
            who="Data pipelines / OntologyBuilder / field knowledge stewards.",
            why="High-volume change lives in ABox; TBox stays stable.",
            analogy="SQL INSERT rows under fixed tables.",
            code='g.add((WD["wm-001"], RDF.type, WD.Product))',
            language="python",
            say_aloud="ABox is the boxes of facts on the shelves.",
            sources=[
                _s("W3C OWL 2 Primer (TBox vs ABox)", "https://www.w3.org/TR/owl2-primer/", "standard"),
            ],
            related_module_ids=["01-tbox-abox-simple", "03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-owl",
            front="OWL (Web Ontology Language)",
            track="foundations",
            tags=["owl", "w3c", "ontology"],
            kind="concept",
            what="W3C language for ontologies on top of RDF, grounded in Description Logic fragments.",
            how="Classes, properties, axioms (disjoint, equivalentClass, restrictions); serialize Turtle/RDF/XML.",
            where="Formal export/interchange; optional offline reasoners — not required on our diagnose path.",
            when="When you need shared meaning across tools or regulatory/semantic interoperability.",
            who="W3C OWL Working Group; enterprise knowledge teams.",
            why="Machine-interpretable meaning beyond ad-hoc JSON keys.",
            pitfalls=["Assuming HermiT runs in every API request", "Open-world surprises vs closed-world apps"],
            say_aloud="OWL formalizes the schema; our chat still reads Neo4j ABox at runtime.",
            sources=[
                _s("W3C OWL 2 Overview", "https://www.w3.org/TR/owl2-overview/", "standard"),
            ],
            related_module_ids=["01-tbox-abox-simple", "09-shacl-gates"],
        ),
        FlashCard(
            id="fc-shacl",
            front="SHACL",
            track="pipeline",
            tags=["shacl", "validation", "quality"],
            kind="concept",
            what="Shapes Constraint Language — closed-world validation of RDF/instance graphs.",
            how="NodeShapes/PropertyShapes with minCount, datatype, class; engines like pyshacl validate data graphs.",
            where="Before materialize/promote (our lite Python shapes mirror this job).",
            when="On every ABox pack before it can affect production diagnosis.",
            who="Data quality / knowledge platform owners.",
            why="OWL open-world inference ≠ 'is this pack complete enough to ship?'",
            code="MIN_SYMPTOMS = 1\nMIN_INDICATES_LINKS = 1",
            language="python",
            say_aloud="SHACL is the clipboard at the loading dock before promote.",
            sources=[
                _s("W3C SHACL", "https://www.w3.org/TR/shacl/", "standard"),
            ],
            related_module_ids=["09-shacl-gates", "03-etl-pipeline"],
        ),
    ]

    # ── Cypher / Neo4j ────────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-property-graph",
            front="Property graph (Neo4j)",
            track="graph",
            tags=["neo4j", "cypher", "graph"],
            kind="concept",
            what="Graph model of labeled nodes and typed relationships, both with properties.",
            how="Query with Cypher MATCH/MERGE; index by business keys (product_id, …).",
            where="Operational ABox for GraphRAG diagnosis (prod :7687, staging :7688).",
            when="Runtime multi-hop diagnostic retrieval and load after ETL.",
            who="Platform engineers; model inspired by Labeled Property Graph practice (Neo4j).",
            why="Fast typed path queries for explainable diagnosis.",
            sources=[
                _s(
                    "Neo4j Cypher Manual",
                    "https://neo4j.com/docs/cypher-manual/current/",
                    "docs",
                ),
                _s(
                    "Angles & Gutierrez, Survey of Graph Database Models (ACM CSUR)",
                    "https://dl.acm.org/doi/10.1145/1322432.1322433",
                    "paper",
                ),
            ],
            related_module_ids=["02-cypher-create-read"],
        ),
        FlashCard(
            id="fc-cypher-merge",
            front="Cypher MERGE",
            track="graph",
            tags=["cypher", "write", "upsert"],
            kind="command",
            what="Idempotent create-if-missing for nodes/patterns.",
            how="MERGE (n:Label {key: $id}) ON CREATE SET … then MERGE relationships.",
            where="populate_graph / promote path when loading ABox.",
            when="ETL load and any upsert of business entities.",
            who="Pipeline loaders.",
            why="Re-running loads must not duplicate the world.",
            code="MERGE (p:Product {product_id: $product_id})\n  ON CREATE SET p.name = $name",
            language="cypher",
            pitfalls=["MERGE without a unique key", "String-building ids into Cypher"],
            say_aloud="MERGE upserts by business key using $parameters.",
            sources=[
                _s(
                    "Neo4j Cypher Manual — MERGE",
                    "https://neo4j.com/docs/cypher-manual/current/clauses/merge/",
                    "docs",
                ),
            ],
            related_module_ids=["02-cypher-create-read", "03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-cypher-params",
            front="Parameterized Cypher ($params)",
            track="graph",
            tags=["cypher", "security", "performance"],
            kind="pattern",
            what="Bind values separately from query text.",
            how="session.run(query, product_id=…); never f-string user input into Cypher.",
            where="All production GraphRAG queries.",
            when="Always for user or external input.",
            who="Every developer writing Cypher.",
            why="Injection safety + query plan cache reuse.",
            code='session.run("MATCH (p:Product {product_id: $id}) RETURN p", id=pid)',
            language="python",
            sources=[
                _s(
                    "Neo4j Driver Manual — queries and parameters",
                    "https://neo4j.com/docs/python-manual/current/query-simple/",
                    "docs",
                ),
                _s(
                    "OWASP Query Parameterization Cheat Sheet",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html",
                    "docs",
                ),
            ],
            related_module_ids=["02-cypher-create-read"],
        ),
        FlashCard(
            id="fc-shortestpath",
            front="shortestPath (Cypher)",
            track="graph",
            tags=["cypher", "retrieval", "path"],
            kind="command",
            what="Find a minimum-hop path between two nodes under relationship constraints.",
            how="MATCH path = shortestPath((a)-[:REL*1..N]-(b)) RETURN path — always bound N.",
            where="Explainable trails symptom→FM→part when needed.",
            when="Compact diagnostic explanation, not unbounded exploration.",
            who="GraphRAG / analytics queries.",
            why="Bounded hops keep latency predictable.",
            pitfalls=["Unbounded [*] variable length on large graphs"],
            sources=[
                _s(
                    "Neo4j Cypher Manual — shortestPath",
                    "https://neo4j.com/docs/cypher-manual/current/patterns/shortest-paths/",
                    "docs",
                ),
            ],
            related_module_ids=["02-cypher-create-read", "07-retrieval-bayes"],
        ),
    ]

    # ── ETL / dual graph ──────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-etl",
            front="ETL (Extract–Transform–Load)",
            track="pipeline",
            tags=["etl", "pipeline", "data"],
            kind="process",
            what="Classic data integration pattern: pull sources, map to target model, load store.",
            how="Extract connectors → OntologyBuilder ABox → validate → MERGE Neo4j.",
            where="graph/enterprise_pipeline control plane + Admin wizard.",
            when="Bootstrap, incremental sync, product onboard, bulletin packs.",
            who="Data platform / knowledge ops.",
            why="Chat must not invent knowledge; it must be governed and loaded.",
            analogy="Warehouse receiving dock → resticker → shelf.",
            say_aloud="Extract sources, transform to ABox, validate, load staging, promote production.",
            sources=[
                _s(
                    "Kimball & Ross, The Data Warehouse Toolkit (ETL themes)",
                    "https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/books/data-warehouse-dw-toolkit/",
                    "book",
                ),
                _s(
                    "Inmon, Building the Data Warehouse (integration discipline)",
                    "",
                    "book",
                ),
            ],
            related_module_ids=["03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-dual-graph",
            front="Dual graph (staging vs production)",
            track="pipeline",
            tags=["neo4j", "promote", "safety"],
            kind="pattern",
            what="Two Neo4j environments: staging for safe MERGE, production for diagnose reads.",
            how="Promote staging (:7688) first; after smoke, promote production (:7687).",
            where="docker dual Neo4j; promote_graph pipeline.",
            when="Every knowledge change that will affect chat.",
            who="Admin operators / CI promote jobs.",
            why="Blast-radius control — bad ABox never hits customer chat first.",
            code="staging :7688  →  smoke  →  production :7687",
            language="text",
            say_aloud="Chat reads production only; staging is the back room.",
            sources=[
                _s(
                    "Continuous Delivery (Humble & Farley) — staged releases",
                    "",
                    "book",
                ),
            ],
            related_module_ids=["03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-operator-chant",
            front="Operator chant (knowledge promote)",
            track="pipeline",
            tags=["etl", "ops", "memorize"],
            kind="process",
            what="Fixed order of Admin steps for safe onboard.",
            how="Sources→Fetch→Select→Validate ABox→Materialize→Smoke→Approve→Promote staging→Promote production→Invalidate caches.",
            where="Admin Control Room UI + control plane APIs.",
            when="Every NEW/UPDATE knowledge batch.",
            who="Knowledge operator.",
            why="Skipping validate/smoke is how bad packs reach diagnosis.",
            say_aloud="Fetch select validate materialize smoke approve stage prod invalidate.",
            sources=[
                _s("Project docs: 22-TBox-ABox-Multi-Source-Onboard-Mechanism", "", "docs"),
            ],
            related_module_ids=["03-etl-pipeline"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-ontology-builder",
            front="OntologyBuilder",
            track="pipeline",
            tags=["abox", "transform", "etl"],
            kind="pattern",
            what="Anti-corruption transform: source records → catalog ABox under shared TBox.",
            how="Map PIM/FSM/Claims/CRM fields into ProductKnowledge structures + links.",
            where="graph/enterprise_pipeline/transformers/ontology_builder.py",
            when="knowledge_materialize pipeline stage.",
            who="Platform transform layer (not per-product OWL authors).",
            why="Sources stay ugly; canonical ABox stays clean.",
            sources=[
                _s(
                    "Evans, Domain-Driven Design — anti-corruption layer",
                    "",
                    "book",
                ),
            ],
            related_module_ids=["03-etl-pipeline", "01-tbox-abox-simple"],
        ),
    ]

    # ── Caching ───────────────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-cache-ttl",
            front="TTL cache",
            track="runtime",
            tags=["cache", "ttl", "performance"],
            kind="concept",
            what="Store computed results with a maximum age (time-to-live).",
            how="get → if miss compute → set(key, value, ttl); expire automatically.",
            where="runtime/cache.py named caches (ontology ~300s, subgraph ~60s, diagnose ~90s).",
            when="Hot stable reads; not forever for changing graph data.",
            who="API runtime.",
            why="Cut Neo4j load and latency on repeated reads.",
            code="hit = cache.get(key)\nif hit is None:\n    hit = compute()\n    cache.set(key, hit, ttl_seconds=60)",
            language="python",
            pitfalls=["Key missing a dimension", "No invalidation after promote"],
            say_aloud="TTL caps how old a cached answer may be.",
            sources=[
                _s(
                    "Redis docs — Expiration / TTL",
                    "https://redis.io/docs/latest/develop/use/keyspace/",
                    "docs",
                ),
                _s(
                    "MDN HTTP Caching (conceptual TTL)",
                    "https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching",
                    "docs",
                ),
            ],
            related_module_ids=["04-caching"],
        ),
        FlashCard(
            id="fc-cache-key",
            front="Cache key design",
            track="runtime",
            tags=["cache", "key", "correctness"],
            kind="pattern",
            what="The string that uniquely identifies a cached result.",
            how="Include every input that changes the answer (tenant, product, symptoms, …).",
            where="All named caches and rate-limit keys.",
            when="Designing any memoization.",
            who="API engineers.",
            why="Wrong keys cause silent wrong answers or cross-tenant bleed.",
            code='key = f"subgraph:{tenant}:{product_id}"',
            language="python",
            say_aloud="The key must include every input that changes the answer.",
            sources=[
                _s(
                    "Redis best practices — key naming",
                    "https://redis.io/docs/latest/develop/use/keyspace/",
                    "docs",
                ),
            ],
            related_module_ids=["04-caching", "06-partitioning"],
        ),
        FlashCard(
            id="fc-redis-shared",
            front="Redis as shared cache / limits",
            track="runtime",
            tags=["redis", "multi-pod", "cache"],
            kind="concept",
            what="In-memory data store used as shared cache, rate-limit windows, admission counters.",
            how="Set REDIS_URL; same API falls back to process memory if empty.",
            where="Multi-replica API fleets.",
            when="More than one API process/pod.",
            who="Platform / SRE.",
            why="Otherwise each pod has a different notepad for limits and caches.",
            analogy="One whiteboard for ten cashiers.",
            sources=[
                _s("Redis documentation", "https://redis.io/docs/", "docs"),
            ],
            related_module_ids=["04-caching", "05-multithreading"],
        ),
        FlashCard(
            id="fc-cache-invalidation",
            front="Cache invalidation after promote",
            track="runtime",
            tags=["cache", "etl", "correctness"],
            kind="process",
            what="Delete or expire cache entries when underlying graph data changes.",
            how="invalidate_all_named_caches() after successful load/promote.",
            where="End of ETL/promote pipelines.",
            when="Every graph write that affects reads.",
            who="Pipeline runner.",
            why="Stale subgraphs are silent production bugs.",
            say_aloud="After promote I invalidate named caches.",
            sources=[
                _s(
                    "Phil Karlton (attrib.): cache invalidation is hard — industry lore; pair with explicit invalidation APIs",
                    "",
                    "docs",
                ),
            ],
            related_module_ids=["04-caching", "03-etl-pipeline"],
        ),
    ]

    # ── Threading / concurrency ───────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-io-vs-cpu",
            front="I/O-bound vs CPU-bound work",
            track="runtime",
            tags=["threading", "performance"],
            kind="theory",
            what="I/O-bound waits on network/disk; CPU-bound burns cores on computation.",
            how="Parallelize independent I/O with a thread pool; keep heavy deterministic ranking serial.",
            where="ETL extract vs Bayes ranking.",
            when="Designing concurrency for pipelines and APIs.",
            who="Backend engineers.",
            why="Threads help waits; pure-Python CPU parallelism is limited by the GIL.",
            sources=[
                _s(
                    "Python docs — concurrent.futures",
                    "https://docs.python.org/3/library/concurrent.futures.html",
                    "docs",
                ),
                _s(
                    "Beazley — Understanding the Python GIL (talk/notes)",
                    "https://www.dabeaz.com/python/UnderstandingGIL.pdf",
                    "paper",
                ),
            ],
            related_module_ids=["05-multithreading"],
        ),
        FlashCard(
            id="fc-threadpool",
            front="ThreadPoolExecutor (bounded)",
            track="runtime",
            tags=["threading", "python"],
            kind="code",
            what="Pool of worker threads with a max concurrency ceiling.",
            how="with ThreadPoolExecutor(max_workers=4) as pool: pool.map(fn, items)",
            where="Parallel connector extract.",
            when="Multiple independent network fetches.",
            who="ETL runners.",
            why="Bound protects file descriptors and source systems.",
            code="with ThreadPoolExecutor(max_workers=4) as pool:\n    return list(pool.map(lambda f: f(), fetch_fns))",
            language="python",
            pitfalls=["Unbounded thread-per-request"],
            sources=[
                _s(
                    "Python concurrent.futures.ThreadPoolExecutor",
                    "https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor",
                    "docs",
                ),
            ],
            related_module_ids=["05-multithreading", "03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-admission",
            front="Admission control (in-flight limit)",
            track="runtime",
            tags=["concurrency", "reliability"],
            kind="pattern",
            what="Cap how many expensive requests run at once.",
            how="Semaphore / Redis INCR with max_in_flight; reject with 429/503 when full; always release in finally.",
            where="Diagnose path ConcurrencyLimiter.",
            when="Traffic spikes that would crush Neo4j.",
            who="API gateway/runtime.",
            why="Protect p99 latency and downstream pools (bulkhead idea).",
            sources=[
                _s(
                    "Nygard, Release It! — bulkheads / load shedding",
                    "",
                    "book",
                ),
                _s(
                    "Google SRE Book — handling overload",
                    "https://sre.google/sre-book/handling-overload/",
                    "docs",
                ),
            ],
            related_module_ids=["05-multithreading"],
        ),
    ]

    # ── Partitioning / CAP ────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-partition-logical",
            front="Logical partitioning keys",
            track="runtime",
            tags=["partition", "tenant", "scale"],
            kind="pattern",
            what="String keys that name a slice of the world (tenant|product|…).",
            how="partition_key(tenant, product); reuse for cache and rate limits.",
            where="runtime/partitioning.py; ETL product_ids selection.",
            when="Multi-tenant SaaS and multi-product catalogs.",
            who="Platform engineers.",
            why="Prevent cross-tenant bleed; prepare for physical shards later.",
            code='"|".join([f"tenant={t}", f"product={p}"])',
            language="python",
            sources=[
                _s(
                    "Kafka docs — partitions (work division analogy)",
                    "https://kafka.apache.org/documentation/#intro_topics",
                    "docs",
                ),
            ],
            related_module_ids=["06-partitioning"],
        ),
        FlashCard(
            id="fc-cap",
            front="CAP theorem (for diagnosis knowledge)",
            track="runtime",
            tags=["cap", "consistency", "distributed"],
            kind="theory",
            what="In a partition, a system cannot simultaneously guarantee perfect Consistency and Availability.",
            how="Choose tradeoffs: we prefer consistent diagnostic knowledge (promote fail-closed) over serving stale/wrong ABox.",
            where="Dual-graph promote design; not multi-region active-active without conflict design.",
            when="Discussing HA vs correctness for warranty answers.",
            who="Architects (Brewer’s conjecture; formalized by Gilbert & Lynch).",
            why="Wrong diagnosis is worse than a slow or unavailable answer.",
            sources=[
                _s(
                    "Gilbert & Lynch, Brewer’s Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services (ACM SIGACT 2002)",
                    "https://dl.acm.org/doi/10.1145/564585.564601",
                    "paper",
                ),
                _s(
                    "Brewer, CAP Twelve Years Later (IEEE Computer)",
                    "https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/",
                    "paper",
                ),
            ],
            related_module_ids=["06-partitioning", "03-etl-pipeline"],
            difficulty="hard",
        ),
    ]

    # ── Retrieval / Bayes / FMEA ──────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-graphrag",
            front="GraphRAG (this product)",
            track="graph",
            tags=["graphrag", "retrieval", "rag"],
            kind="pattern",
            what="Retrieve typed multi-hop evidence from a knowledge graph, then ground the answer (LLM optional).",
            how="Scope product → match symptoms → Cypher INDICATES → rank → format with provenance.",
            where="graph/graph_rag.py + LangGraph run_diagnosis node.",
            when="Every customer/agent diagnosis request.",
            who="Diagnosis service.",
            why="Explainable paths beat opaque vector-only answers for warranty.",
            sources=[
                _s(
                    "Lewis et al., Retrieval-Augmented Generation (NeurIPS 2020)",
                    "https://arxiv.org/abs/2005.11401",
                    "paper",
                ),
                _s(
                    "Microsoft GraphRAG (research blog/docs) — graph-augmented RAG patterns",
                    "https://www.microsoft.com/en-us/research/project/graphrag/",
                    "docs",
                ),
            ],
            related_module_ids=["07-retrieval-bayes", "08-langgraph-agent"],
        ),
        FlashCard(
            id="fc-naive-bayes",
            front="Naive Bayes diagnostic ranking",
            track="graph",
            tags=["bayes", "ranking", "ml-classic"],
            kind="theory",
            what="Posterior ∝ prior × ∏ likelihoods under conditional independence assumption.",
            how="prior from occurrence; likelihood from INDICATES.confidence; miss likelihood if edge absent; normalize.",
            where="graph/reliability.py bayesian_posteriors.",
            when="Ranking failure modes given observed symptoms.",
            who="Reliability / GraphRAG ranking.",
            why="Principled combination of soft evidence; well-known baseline in probabilistic IR/diagnosis.",
            code="score = prior\nfor s in observed:\n    score *= likelihoods.get((s, fm), miss)\n# normalize across fm",
            language="python",
            sources=[
                _s(
                    "Russell & Norvig, AIMA — Bayesian networks / naive Bayes",
                    "",
                    "book",
                ),
                _s(
                    "Manning et al., Introduction to Information Retrieval — text classification / NB",
                    "https://nlp.stanford.edu/IR-book/",
                    "book",
                ),
            ],
            related_module_ids=["07-retrieval-bayes"],
        ),
        FlashCard(
            id="fc-fmea",
            front="FMEA S/O/D & Action Priority",
            track="graph",
            tags=["fmea", "reliability", "iso"],
            kind="concept",
            what="Failure Mode and Effects Analysis signals: Severity, Occurrence, Detection (AIAG-VDA emphasizes Action Priority over raw RPN).",
            how="Map graph evidence to S/O/D ratings; use for risk context while ranking primarily by posterior.",
            where="reliability.py + ranked failure mode payload.",
            when="Presenting risk alongside probabilistic rank.",
            who="Reliability engineering practice (AIAG/VDA).",
            why="Industry-common language for service/engineering stakeholders.",
            pitfalls=["Treating RPN as a probability"],
            sources=[
                _s(
                    "AIAG & VDA FMEA Handbook (Action Priority)",
                    "https://www.aiag.org/",
                    "standard",
                ),
                _s(
                    "IEC 60812 — FMEA procedures (family of reliability standards)",
                    "https://webstore.iec.ch/",
                    "standard",
                ),
            ],
            related_module_ids=["07-retrieval-bayes"],
        ),
        FlashCard(
            id="fc-miss-likelihood",
            front="Miss likelihood (sparse edges)",
            track="graph",
            tags=["sparse", "bayes", "graphrag"],
            kind="pattern",
            what="Default P(s|fm) when INDICATES edge is absent.",
            how="likelihoods.get((s, fm), miss) with small miss (e.g. 0.05).",
            where="bayesian_posteriors.",
            when="Sparse warranty graphs — normal in the real world.",
            who="Ranking code.",
            why="Avoid zeroing candidates harshly; still prefer growing real ABox edges over silent KGE invention in v1.",
            sources=[
                _s(
                    "Naive Bayes smoothing / missing features — classic ML practice (AIMA / IR book)",
                    "https://nlp.stanford.edu/IR-book/",
                    "book",
                ),
            ],
            related_module_ids=["07-retrieval-bayes"],
        ),
    ]

    # ── LangGraph / agents ────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-langgraph",
            front="LangGraph StateGraph",
            track="agent",
            tags=["langgraph", "agent", "orchestration"],
            kind="concept",
            what="Library for stateful agent workflows as graphs of nodes and edges.",
            how="StateGraph → add_node → add_edge / conditional_edges → compile().",
            where="agents/diagnosis_graph.py",
            when="Orchestrating multi-step diagnose flows.",
            who="Agent application developers (LangChain ecosystem).",
            why="Explicit control flow beats ad-hoc call stacks for tools and branching.",
            code="g = StateGraph(State)\ng.add_node(...)\ng.set_entry_point(...)\napp = g.compile()",
            language="python",
            sources=[
                _s(
                    "LangGraph documentation",
                    "https://langchain-ai.github.io/langgraph/",
                    "docs",
                ),
            ],
            related_module_ids=["08-langgraph-agent"],
        ),
        FlashCard(
            id="fc-four-nodes",
            front="Production four-node diagnose belt",
            track="agent",
            tags=["langgraph", "diagnose"],
            kind="process",
            what="detect_product → run_diagnosis → format_response → handle_escalation",
            how="Fixed edges; run_diagnosis calls GraphRAG tools with parameterized Cypher.",
            where="agents/diagnosis_graph.py",
            when="Every diagnose request.",
            who="API/agent runtime.",
            why="Deterministic, auditable path for warranty.",
            say_aloud="Detect, diagnose, format, escalate — LLM optional for wording only.",
            sources=[
                _s("Project agents/diagnosis_graph.py", "", "docs"),
            ],
            related_module_ids=["08-langgraph-agent"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-smart-cypher",
            front="Smart Cypher tool pattern (interview alt)",
            track="agent",
            tags=["llm", "cypher", "tools"],
            kind="pattern",
            what="Outer LLM routes to a tool; inner LLM writes Cypher; tool executes with try/except.",
            how="Prompt includes schema labels; strip fences; catch query errors; return string error not crash.",
            where="Tutorials / flexible analytics — NOT our default diagnose path.",
            when="Interview discussions of flexibility vs determinism.",
            who="Agent demos; researchers.",
            why="High flexibility; medium determinism; risk of invented labels.",
            pitfalls=["No schema in prompt", "No try/except", "Confusing with this product"],
            sources=[
                _s(
                    "LangChain tools / agents docs",
                    "https://python.langchain.com/docs/concepts/tools/",
                    "docs",
                ),
            ],
            related_module_ids=["08-langgraph-agent"],
        ),
    ]

    # ── ISO / industry modeling ───────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-iso-14224",
            front="ISO 14224 (modeling inspiration)",
            track="foundations",
            tags=["iso", "reliability", "industry"],
            kind="concept",
            what="Standard for reliability/maintenance data collection: equipment hierarchy + failure taxonomy.",
            how="We map hierarchy ideas to Product→Component and failures to FailureMode — not a certified implementation claim.",
            where="Ontology design rationale (docs/15, industry alignment).",
            when="Explaining industrial alignment in interviews.",
            who="Oil & gas / reliability data community; ISO.",
            why="Shared vocabulary with asset-intensive industries.",
            sources=[
                _s(
                    "ISO 14224 — Petroleum, petrochemical and natural gas industries — Collection and exchange of reliability and maintenance data",
                    "https://www.iso.org/standard/64076.html",
                    "standard",
                ),
            ],
            related_module_ids=["01-tbox-abox-simple"],
        ),
        FlashCard(
            id="fc-iso-81346",
            front="IEC 81346 product aspect (inspiration)",
            track="foundations",
            tags=["iec", "structure", "bom"],
            kind="concept",
            what="Reference designation: function / product / location aspects of system structure.",
            how="We emphasize product/BOM structure as Component and parts links.",
            where="Ontology product structure edges.",
            when="Discussing topology vs ontology (product structure is in-ontology).",
            who="IEC systems engineering standards community.",
            why="Separates plant location topology from product diagnostic structure.",
            sources=[
                _s(
                    "IEC 81346 series — Industrial systems reference designation",
                    "https://www.iso.org/standard/82229.html",
                    "standard",
                ),
            ],
            related_module_ids=["01-tbox-abox-simple"],
        ),
    ]

    # ── Code snippets pack ────────────────────────────────────────────────
    cards += [
        FlashCard(
            id="fc-code-triple-add",
            front="rdflib: add a triple",
            track="foundations",
            tags=["code", "rdf", "python"],
            kind="code",
            what="Assert one RDF fact into a Graph.",
            how="Graph.add((subject, predicate, object))",
            where="Ontology export / tutorials.",
            when="Building TBox or ABox programmatically.",
            who="Knowledge engineer scripting.",
            why="Atomic unit of RDF construction.",
            code="from rdflib import Graph, RDF, OWL\ng = Graph()\ng.add((WD.Product, RDF.type, OWL.Class))",
            language="python",
            sources=[_s("rdflib documentation", "https://rdflib.readthedocs.io/", "docs")],
            related_module_ids=["01-tbox-abox-simple"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-code-bayes",
            front="Code: naive Bayes loop",
            track="graph",
            tags=["code", "bayes", "python"],
            kind="code",
            what="Multiply prior by likelihoods; normalize.",
            how="See snippet; use miss default.",
            where="reliability.bayesian_posteriors",
            when="Ranking FMs.",
            who="GraphRAG ranking.",
            why="Core whiteboard skill.",
            code="score = max(priors.get(fm, 0.0), 0.0)\nfor s in observed:\n    score *= likelihoods.get((s, fm), miss)\nscores[fm] = score\n# then divide by sum(scores.values())",
            language="python",
            sources=[
                _s("Russell & Norvig AIMA", "", "book"),
            ],
            related_module_ids=["07-retrieval-bayes"],
        ),
        FlashCard(
            id="fc-code-cache",
            front="Code: cache get-or-set",
            track="runtime",
            tags=["code", "cache", "python"],
            kind="code",
            what="Standard memoization control flow.",
            how="get; on miss compute; set with TTL.",
            where="runtime caches.",
            when="Hot reads.",
            who="API runtime.",
            why="Latency + load.",
            code="v = cache.get(key)\nif v is None:\n    v = compute()\n    cache.set(key, v, ttl_seconds=60)\nreturn v",
            language="python",
            sources=[_s("Redis TTL docs", "https://redis.io/docs/", "docs")],
            related_module_ids=["04-caching"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-code-threadpool",
            front="Code: ThreadPoolExecutor map",
            track="runtime",
            tags=["code", "threading", "python"],
            kind="code",
            what="Bounded parallel map over callables.",
            how="max_workers ceiling + map.",
            where="ETL extract.",
            when="Independent I/O.",
            who="Pipeline.",
            why="Faster waits.",
            code="with ThreadPoolExecutor(max_workers=4) as pool:\n    return list(pool.map(lambda fn: fn(), fetch_fns))",
            language="python",
            sources=[
                _s(
                    "Python concurrent.futures",
                    "https://docs.python.org/3/library/concurrent.futures.html",
                    "docs",
                )
            ],
            related_module_ids=["05-multithreading"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-code-cypher-scope",
            front="Code: product-scoped MATCH",
            track="graph",
            tags=["code", "cypher"],
            kind="code",
            what="Always bind Product first.",
            how="MATCH (p:Product {product_id: $product_id})-…",
            where="GraphRAG ranking queries.",
            when="Every diagnose retrieval.",
            who="graph_rag.",
            why="Scope = speed + accuracy.",
            code="MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)\nOPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\nWHERE s.symptom_id IN $symptom_ids\nRETURN fm, sum(coalesce(ind.confidence,0)) AS score\nORDER BY score DESC",
            language="cypher",
            sources=[_s("Neo4j Cypher Manual", "https://neo4j.com/docs/cypher-manual/current/", "docs")],
            related_module_ids=["02-cypher-create-read", "07-retrieval-bayes"],
        ),
    ]

    # ── Source-backed deep-dives (verified from primary sources, 2026) ─────
    cards += [
        FlashCard(
            id="fc-iri",
            front="IRI (Internationalized Resource Identifier)",
            track="foundations",
            tags=["rdf", "iri", "identity"],
            kind="concept",
            what="A global identifier for a resource; a generalization of URI allowing non-ASCII characters.",
            how="Use a namespaced IRI (e.g. wd:FailureMode -> http://.../FailureMode); can sit in subject, predicate, OR object position.",
            where="Every RDF triple; ontology exports; linked-data joins across datasets.",
            when="Whenever you name a thing you want other systems to reference unambiguously.",
            who="W3C RDF WG; knowledge engineers assigning stable identifiers.",
            why="Global scope means the same IRI denotes the same thing everywhere - the basis of mergeable data.",
            analogy="A phone number for a concept: dial it from anywhere and reach the same entity.",
            code="WD = Namespace('http://example.org/warranty#')\ng.add((WD.Pump, RDF.type, OWL.Class))  # WD.Pump is an IRI",
            language="python",
            pitfalls=[
                "TRICK: prefer REUSING an existing IRI (FOAF, schema.org, Dublin Core) over minting a new one - reuse creates the network effect.",
                "Literals may NOT appear in the subject or predicate position - only IRIs (and blank nodes for subject).",
                "A relative IRI like 'bob#me' resolves against the document BASE - forgetting BASE breaks merges.",
            ],
            say_aloud="An IRI is a globally unique name so the same identifier means the same thing everywhere.",
            sources=[_s("W3C RDF 1.1 Primer section 3.2", "https://www.w3.org/TR/rdf11-primer/", "standard")],
            related_module_ids=["01-tbox-abox-simple"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-blank-node",
            front="Blank node",
            track="foundations",
            tags=["rdf", "blank-node"],
            kind="concept",
            what="A resource with no global IRI - 'some thing exists' without naming it (like a variable in algebra).",
            how="Turtle uses _:x or [ ... ]; may appear only in subject or object position, never as a predicate.",
            where="Modeling an intermediate/anonymous node (e.g. an address, a reified statement).",
            when="When a value has structure but doesn't deserve a stable public identifier.",
            who="RDF authors; SHACL uses blank nodes heavily for property shapes.",
            why="Lets you attach structure locally without polluting the global namespace.",
            analogy="An unnamed cypress tree 'in the background of the Mona Lisa' - you know it exists without giving it an ID.",
            code="_:x a wd:Address ; wd:city wd:Berlin .   # Turtle blank node",
            language="turtle",
            pitfalls=[
                "GOTCHA: blank node ids are LOCAL to a document - _:x in file A != _:x in file B, so they don't merge across graphs.",
                "TRICK: if a node might be referenced or deactivated later (e.g. a SHACL shape), give it an IRI instead of a blank node.",
            ],
            say_aloud="A blank node says 'a thing exists here' without giving it a global name.",
            sources=[_s("W3C RDF 1.1 Primer section 3.4", "https://www.w3.org/TR/rdf11-primer/", "standard")],
            related_module_ids=["01-tbox-abox-simple", "09-shacl-gates"],
        ),
        FlashCard(
            id="fc-named-graph",
            front="Named graph / RDF dataset",
            track="foundations",
            tags=["rdf", "named-graph", "provenance"],
            kind="concept",
            what="A set of triples grouped under a graph-name IRI; a dataset = one default graph + zero-or-more named graphs.",
            how="TriG {} blocks or N-Quads (4th element = graph IRI); query per-graph with SPARQL GRAPH.",
            where="Provenance / lineage: keep 'who said this' with the facts (your provenance_manifest).",
            when="When the SOURCE of a fact matters as much as the fact - staging vs promoted, vendor A vs vendor B.",
            who="Data stewards; SPARQL introduced named graphs, RDF 1.1 standardized them.",
            why="Lets you attribute, version, and selectively trust subsets of triples.",
            analogy="Folders for triples: same statements, but you know which drawer they came from.",
            code="GRAPH <http://ex.org/vendorA> { wd:Pump wd:mtbf 5000 . }",
            language="turtle",
            pitfalls=[
                "GOTCHA: RDF gives graph-names NO built-in meaning - 'the name = the source' is a convention you must document (out-of-band).",
                "TRICK: use named graphs to promote/rollback a whole source atomically instead of per-triple bookkeeping.",
            ],
            say_aloud="A named graph tags a bundle of triples with where they came from.",
            sources=[_s("W3C RDF 1.1 Primer section 3.5", "https://www.w3.org/TR/rdf11-primer/", "standard")],
            related_module_ids=["01-tbox-abox-simple", "03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-rdfs-entailment",
            front="RDFS entailment (inference)",
            track="foundations",
            tags=["rdfs", "reasoning", "entailment"],
            kind="theory",
            what="Deriving new true triples from stated ones using RDFS semantics (domain/range/subClassOf).",
            how="Declare rdfs:domain/range; a reasoner adds the implied rdf:type triples.",
            where="TBox reasoning; SHACL can run over pre-entailed graphs.",
            when="When you want types/relationships inferred instead of asserted everywhere.",
            who="Reasoners (e.g. owlrl, GraphDB); the W3C RDF Semantics doc defines it.",
            why="Less redundant data: state the rule once, derive the consequences.",
            analogy="'X knows Y' + 'knows requires People' => X and Y are People, automatically.",
            code="# ex:bob ex:knows ex:alice .\n# ex:knows rdfs:domain ex:Person .\n# => entails: ex:bob rdf:type ex:Person .",
            language="turtle",
            pitfalls=[
                "GOTCHA: 'ex:age \"forty\"^^xsd:integer' is a logical INCONSISTENCY - the literal violates the integer datatype.",
                "TRICK: RDFS lets the SAME entity be both a class and an instance (e.g. Elephant) - freedom SQL doesn't allow.",
                "Some entailment regimes are cheap; full reasoning can be expensive - pick the regime deliberately.",
            ],
            say_aloud="RDFS entailment derives new facts from domain, range, and subclass rules.",
            sources=[_s("W3C RDF 1.1 Primer section 6 (Semantics)", "https://www.w3.org/TR/rdf11-primer/", "standard")],
            related_module_ids=["01-tbox-abox-simple"],
            difficulty="hard",
        ),
        FlashCard(
            id="fc-turtle-sugar",
            front="Turtle syntactic sugar",
            track="foundations",
            tags=["turtle", "syntax", "rdf"],
            kind="code",
            what="Turtle = N-Triples + shorthands: prefixes, 'a', ';' and ',' groupers, [] blank nodes.",
            how="Use @prefix / PREFIX; 'a' = rdf:type; ';' repeats the subject; ',' repeats subject+predicate.",
            where="Reading/writing ontologies (.ttl) by hand.",
            when="Any hand-authored RDF - Turtle is the readable default of the family.",
            who="Ontology authors; Prud'hommeaux & Carothers (Turtle spec).",
            why="Far less repetition than N-Triples while producing the exact same triples.",
            analogy="Abbreviations in shorthand writing - same sentence, fewer keystrokes.",
            code='wd:bob a foaf:Person ;\n       foaf:knows wd:alice ;\n       schema:birthDate "1990-07-04"^^xsd:date .',
            language="turtle",
            pitfalls=[
                "TRICK: 'a' is literally rdf:type - it reads like English ('bob a Person') and is the #1 time-saver.",
                "GOTCHA: the '.' ends a statement; a stray ';' vs '.' changes which subject the next line attaches to.",
                '"Mona Lisa" with no datatype defaults to xsd:string; "x"@fr adds a language tag (type rdf:langString).',
            ],
            say_aloud="In Turtle, 'a' means type, semicolon repeats the subject, comma repeats subject and predicate.",
            sources=[_s("W3C RDF 1.1 Primer section 5.1 (Turtle)", "https://www.w3.org/TR/rdf11-primer/", "standard")],
            related_module_ids=["01-tbox-abox-simple"],
            difficulty="easy",
        ),
        FlashCard(
            id="fc-owl-sameas",
            front="owl:sameAs (entity linking)",
            track="foundations",
            tags=["owl", "linked-data", "identity"],
            kind="concept",
            what="Asserts two different IRIs denote the SAME real-world resource.",
            how="dbpedia:Leonardo_da_Vinci owl:sameAs viaf:24604287 - merge/compare their facts.",
            where="Reconciling entities across vendors/datasets (dedup in ingestion).",
            when="When two sources use different IDs for the same thing.",
            who="Linked-data publishers; OWL vocabulary.",
            why="Bridges siloed identifiers so downstream queries see one entity.",
            analogy="Telling the system 'these two customer records are the same person'.",
            code="wd:PumpA owl:sameAs vendorX:pump_00042 .",
            language="turtle",
            pitfalls=[
                "GOTCHA: owl:sameAs is transitive and symmetric - over-asserting it can wrongly merge distinct entities ('sameAs explosion').",
                "TRICK: for weaker links prefer skos:closeMatch / rdfs:seeAlso instead of the hard owl:sameAs.",
            ],
            say_aloud="owl:sameAs says two IRIs are the same thing, so their facts merge.",
            sources=[_s("W3C RDF 1.1 Primer section 7 (RDF Data)", "https://www.w3.org/TR/rdf11-primer/", "standard")],
            related_module_ids=["01-tbox-abox-simple", "03-etl-pipeline"],
        ),
        FlashCard(
            id="fc-shacl-shapes-graph",
            front="SHACL: shapes graph vs data graph",
            track="foundations",
            tags=["shacl", "validation"],
            kind="concept",
            what="SHACL validates a DATA graph against a SHAPES graph (conditions written as RDF).",
            how="Run processor(data_graph, shapes_graph) -> ValidationReport; both graphs stay immutable.",
            where="Quality gates before promoting ingested data (your 09-shacl-gates).",
            when="Every promotion/ingest - block malformed data from reaching the served graph.",
            who="W3C Data Shapes WG (Knublauch & Kontokostas).",
            why="Declarative, reusable data contracts instead of scattered imperative checks.",
            analogy="A JSON-Schema / linter, but the rules are themselves RDF.",
            code="report = validate(data_graph, shacl_graph=shapes)\nassert report.conforms  # bool",
            language="python",
            pitfalls=[
                "TRICK: shapes are shareable modules - pull them in via owl:imports and disable unwanted ones with sh:deactivated true.",
                "GOTCHA: validation is idempotent - the processor must NOT mutate the data or shapes graph.",
                "The data graph must include the rdfs:subClassOf triples for sh:targetClass to walk the hierarchy.",
            ],
            say_aloud="SHACL checks a data graph against a shapes graph and returns a conformance report.",
            sources=[_s("W3C SHACL Recommendation section 1", "https://www.w3.org/TR/shacl/", "standard")],
            related_module_ids=["09-shacl-gates"],
        ),
        FlashCard(
            id="fc-shacl-node-property",
            front="SHACL: node shape, property shape & targets",
            track="foundations",
            tags=["shacl", "shapes", "targets"],
            kind="concept",
            what="Node shape constrains the focus node; property shape (sh:path) constrains its values. Targets pick focus nodes.",
            how="sh:targetClass/targetNode/targetSubjectsOf/targetObjectsOf select focus nodes; sh:property adds property shapes.",
            where="Defining what 'valid' means for each class in the domain.",
            when="Per class/relationship you want to enforce.",
            who="Shape authors.",
            why="Separates 'which nodes' (targets) from 'what must hold' (constraints).",
            analogy="targetClass = the WHERE clause; property shapes = the column checks.",
            code="ex:PersonShape a sh:NodeShape ;\n  sh:targetClass ex:Person ;\n  sh:property [ sh:path ex:ssn ; sh:maxCount 1 ] .",
            language="turtle",
            pitfalls=[
                "GOTCHA: a node shape must NOT have sh:path; a property shape MUST have exactly one - mixing them makes an ill-formed shape.",
                "TRICK: sh:targetObjectsOf ex:knows targets everything on the OBJECT side of that predicate - great for range checks.",
            ],
            say_aloud="Node shapes check the node; property shapes check its values; targets choose which nodes.",
            sources=[_s("W3C SHACL Recommendation section 2", "https://www.w3.org/TR/shacl/", "standard")],
            related_module_ids=["09-shacl-gates"],
            difficulty="hard",
        ),
        FlashCard(
            id="fc-shacl-report",
            front="SHACL: validation report",
            track="foundations",
            tags=["shacl", "report", "conformance"],
            kind="concept",
            what="Output RDF graph with one sh:conforms (bool) + one sh:ValidationResult per violation.",
            how="Each result carries sh:focusNode, sh:resultPath, sh:value, sh:sourceConstraintComponent, sh:resultSeverity.",
            where="CI gate output; surfaced to operators fixing bad data.",
            when="After every validation run.",
            who="SHACL processors (pySHACL, TopBraid).",
            why="Machine-readable, precise pinpointing of WHAT failed and WHY.",
            analogy="A compiler error list: file, line, rule that fired.",
            code="# report.conforms == False\n# result: focusNode=ex:Alice path=ex:ssn\n#   sourceConstraintComponent=sh:PatternConstraintComponent",
            language="turtle",
            pitfalls=[
                "TRICK: read sh:sourceConstraintComponent to know EXACTLY which constraint fired (MaxCount vs Pattern vs Class).",
                "GOTCHA: sh:conforms is true iff there are ZERO results - a single Warning-severity result still makes conforms=false.",
            ],
            say_aloud="A SHACL report says conforms true or false, plus one detailed result per violation.",
            sources=[_s("W3C SHACL Recommendation section 3.6", "https://www.w3.org/TR/shacl/", "standard")],
            related_module_ids=["09-shacl-gates"],
        ),
        FlashCard(
            id="fc-shacl-severity",
            front="SHACL: sh:severity",
            track="foundations",
            tags=["shacl", "severity", "governance"],
            kind="concept",
            what="Per-shape severity label: sh:Info, sh:Warning, or sh:Violation (default).",
            how="Add sh:severity sh:Warning to a shape; it flows into each result's sh:resultSeverity.",
            where="Tiering gate rules: hard-fail vs advisory.",
            when="When some rules should block and others only warn.",
            who="Governance owners tuning strictness.",
            why="Lets one shapes graph express 'must fix' vs 'should fix' without separate pipelines.",
            analogy="Compiler error vs warning vs info/lint note.",
            code="sh:property [ sh:path ex:x ; sh:minCount 1 ; sh:severity sh:Warning ] .",
            language="turtle",
            pitfalls=[
                "GOTCHA: severity does NOT change conformance - even sh:Info results make sh:conforms false; you must filter by severity yourself.",
                "TRICK: default (no sh:severity) = sh:Violation, so advisory rules must set Warning/Info explicitly.",
            ],
            say_aloud="Severity tags a result Info, Warning, or Violation - but any result still fails conformance.",
            sources=[_s("W3C SHACL Recommendation section 2.1.4", "https://www.w3.org/TR/shacl/", "standard")],
            related_module_ids=["09-shacl-gates"],
        ),
        FlashCard(
            id="fc-rag-three-phases",
            front="RAG: retrieve -> augment -> generate",
            track="agent",
            tags=["rag", "llm", "grounding"],
            kind="process",
            what="Retrieve relevant context, augment the prompt with it, generate an answer from ONLY that context.",
            how="Similarity/DB search -> concat context+question+instructions -> LLM answers using provided context.",
            where="The diagnosis chatbot's answer path.",
            when="Whenever answers must be grounded in trusted, current data (not model memory).",
            who="Neo4j/Microsoft GraphRAG guidance; RAG literature.",
            why="Cuts hallucination and lets you cite sources - models optimize for helpfulness over factuality.",
            analogy="Open-book exam: answer only from the page you were handed.",
            code="prompt = f'Answer ONLY from Context.\\nQuestion: {q}\\nContext: {ctx}\\nAnswer:'",
            language="python",
            pitfalls=[
                "TRICK: the grounding instruction matters - 'Only respond with information mentioned in the Context. Do not inject speculation.'",
                "GOTCHA: retrieval quality dominates answer quality - improving the retriever usually beats prompt tweaking.",
            ],
            say_aloud="RAG retrieves context, augments the prompt, and generates an answer only from that context.",
            sources=[_s("Neo4j - What is GraphRAG?", "https://neo4j.com/blog/genai/what-is-graphrag/", "docs")],
            related_module_ids=["07-retrieval-bayes", "08-langgraph-agent"],
        ),
        FlashCard(
            id="fc-vector-rag-limits",
            front="Why vector-only RAG falls short",
            track="agent",
            tags=["rag", "vector", "graphrag"],
            kind="theory",
            what="Vector-only RAG returns isolated text chunks - fragmented, unexplainable, weak on multi-hop.",
            how="Chunk -> embed -> similarity search -> hand top-k chunks to the LLM (no relationships).",
            where="Baseline RAG before adding a knowledge graph.",
            when="Understanding WHY GraphRAG exists.",
            who="Neo4j GraphRAG guide.",
            why="Answers are confined to retrieved fragments and can't explain WHY a chunk was chosen (black box).",
            analogy="Photocopied page scraps with no idea how they connect.",
            code="# vector search -> 5 chunks -> LLM\n# but: no edges, no provenance, no multi-hop join",
            language="text",
            pitfalls=[
                "GOTCHA: a question needing info spread across sections gets INCOMPLETE answers from vector-only retrieval.",
                "TRICK: GraphRAG fixes this - vector/fulltext finds STARTING points, then you TRAVERSE relationships for context.",
                "Explainability matters in healthcare/finance - graph edges give you the 'why', embeddings don't.",
            ],
            say_aloud="Vector-only RAG returns disconnected chunks with no relationships and no explainability.",
            sources=[_s("Neo4j - What is GraphRAG?", "https://neo4j.com/blog/genai/what-is-graphrag/", "docs")],
            related_module_ids=["07-retrieval-bayes"],
        ),
        FlashCard(
            id="fc-graphrag-retrievers",
            front="GraphRAG retriever types",
            track="agent",
            tags=["graphrag", "retrieval", "neo4j"],
            kind="pattern",
            what="Find entry points (vector/fulltext/spatial), then follow relationships to gather connected context.",
            how="Index search -> neighborhood/path traversal, query templates, Text2Cypher, or agentic tool selection.",
            where="graph_rag retrieval in this codebase.",
            when="When answers depend on connected, multi-hop facts.",
            who="Neo4j GraphRAG (VectorCypherRetriever).",
            why="Combines fuzzy entry (embeddings) with precise expansion (graph) for accurate, traceable answers.",
            analogy="Search the index for a page, then follow the cross-references.",
            code="CALL db.index.vector.queryNodes('docs',5,$emb) YIELD node AS doc\nRETURN doc, COLLECT { MATCH p=(doc)-[r]-(nb) RETURN p } AS paths",
            language="cypher",
            pitfalls=[
                "TRICK: neighborhood traversal (1-2 hops) after a vector hit is the highest-ROI GraphRAG pattern.",
                "GOTCHA: Text2Cypher (LLM writes Cypher) is powerful but needs the schema in the prompt + guardrails against bad queries.",
                "In agentic setups, retrievers become TOOLS the LLM selects and chains until it has enough context.",
            ],
            say_aloud="GraphRAG finds entry nodes by vector search, then traverses relationships for connected context.",
            sources=[
                _s("Neo4j - What is GraphRAG?", "https://neo4j.com/blog/genai/what-is-graphrag/", "docs"),
                _s("neo4j-graphrag Python package", "https://neo4j.com/blog/news/graphrag-python-package/", "docs"),
            ],
            related_module_ids=["07-retrieval-bayes", "02-cypher-create-read"],
            difficulty="hard",
        ),
        FlashCard(
            id="fc-sm2",
            front="SM-2 spaced repetition",
            track="foundations",
            tags=["study-method", "sm2", "memory"],
            kind="theory",
            what="SuperMemo's algorithm: schedule reviews at growing intervals based on an ease factor (EF) per item.",
            how="I(1)=1, I(2)=6, I(n)=round(I(n-1)*EF); after grade q(0-5): EF += 0.1-(5-q)(0.08+(5-q)*0.02), floor 1.3; q<3 resets.",
            where="This Study Lab's Today tab (Again/Hard/Good/Easy -> q).",
            when="Reviewing anything you must retain long-term.",
            who="P. A. Wozniak (1990); basis of Anki.",
            why="Reviews items just before you'd forget - Wozniak measured ~92% retention at far less total time.",
            analogy="Watering a plant right before it wilts, not on a fixed calendar.",
            code="if q < 3: reps, interval = 0, 1        # lapse resets\nelse: interval = 1 if reps==1 else 6 if reps==2 else round(interval*ef)",
            language="python",
            pitfalls=[
                "GOTCHA: q=4 leaves EF unchanged; only q<4 (hesitation/harder) lowers it, q=5 raises it slightly.",
                "TRICK: an EF stuck near the 1.3 floor signals a badly written CARD - split it (minimum-information principle).",
                "After a lapse (q<3) restart intervals from 1 but you still relearn fast because EF is retained.",
            ],
            say_aloud="SM-2 grows review intervals by an ease factor and resets when you fail a card.",
            sources=[_s("Wozniak - SuperMemo SM-2 (1990)", "https://super-memory.com/english/ol/sm2.htm", "paper")],
            related_module_ids=[],
        ),
        FlashCard(
            id="fc-cypher-profile",
            front="Cypher: EXPLAIN vs PROFILE (tuning)",
            track="graph",
            tags=["cypher", "performance", "neo4j"],
            kind="code",
            what="EXPLAIN shows the planned query plan (no run); PROFILE runs it and shows real rows/db-hits per operator.",
            how="Prefix a query with EXPLAIN or PROFILE in the browser/driver; read db-hits to find the costly step.",
            where="Optimizing GraphRAG retrieval queries.",
            when="When a diagnose query is slow or scans too much.",
            who="Neo4j Cypher Manual.",
            why="Turns 'it's slow' into 'this NodeByLabelScan should be an index seek'.",
            analogy="SQL EXPLAIN ANALYZE for graphs.",
            code="PROFILE MATCH (p:Product {product_id:$id})-[:CAN_HAVE]->(fm) RETURN fm",
            language="cypher",
            pitfalls=[
                "TRICK: high 'db hits' on a NodeByLabelScan means you're missing an index - add one on the lookup property.",
                "GOTCHA: always bind the most selective anchor first ($product_id) so the planner starts from few nodes.",
                "PROFILE actually executes the query - don't PROFILE destructive writes on real data.",
            ],
            say_aloud="EXPLAIN plans without running; PROFILE runs and shows real db-hits so you can index the hot step.",
            sources=[_s("Neo4j Cypher Manual - Query tuning", "https://neo4j.com/docs/cypher-manual/current/", "docs")],
            related_module_ids=["02-cypher-create-read", "07-retrieval-bayes"],
        ),
    ]

    # Platform / LLMOps / infra / FinOps / security / MLOps expansion
    try:
        from study.flashcards_platform import platform_flashcards

        cards += platform_flashcards()
    except Exception:
        pass

    # de-dupe by id
    seen: set[str] = set()
    unique: list[FlashCard] = []
    for c in cards:
        if c.id in seen:
            continue
        seen.add(c.id)
        unique.append(c)
    return unique


def write_deck() -> Path:
    FLASH_DIR.mkdir(parents=True, exist_ok=True)
    deck = [c.model_dump() for c in build_deck()]
    FLASH_FILE.write_text(json.dumps(deck, indent=2) + "\n", encoding="utf-8")
    return FLASH_FILE


def load_deck() -> list[FlashCard]:
    if not FLASH_FILE.exists():
        write_deck()
    raw = json.loads(FLASH_FILE.read_text(encoding="utf-8"))
    return [FlashCard.model_validate(x) for x in raw]


def list_flashcards(
    *,
    track: str | None = None,
    tag: str | None = None,
    kind: str | None = None,
    q: str | None = None,
) -> list[FlashCard]:
    cards = load_deck()
    out: list[FlashCard] = []
    ql = (q or "").lower().strip()
    for c in cards:
        if track and c.track != track:
            continue
        if kind and c.kind != kind:
            continue
        if tag and tag.lower() not in [t.lower() for t in c.tags]:
            continue
        if ql:
            blob = " ".join(
                [
                    c.front,
                    c.what,
                    c.how,
                    c.why,
                    " ".join(c.tags),
                ]
            ).lower()
            if ql not in blob:
                continue
        out.append(c)
    return out


if __name__ == "__main__":
    p = write_deck()
    print(f"Wrote {len(build_deck())} flashcards → {p}")
