"""
Grounded Study Lab curriculum — hand-authored, no mock-derived noise.

Every module is built to memorize:
  1) one story  2) say-aloud lines  3) tiny code beats  4) quiz  5) rewrite
"""

from __future__ import annotations

from study.models import (
    BlankSpec,
    CodeBeat,
    ConceptCard,
    FillBlanks,
    LineAnnotation,
    LineQuizItem,
    QuizItem,
    StudyModule,
)
from study.store import MODULES_DIR, save_module


def _ann(lines: list[tuple[int, str]]) -> list[LineAnnotation]:
    return [LineAnnotation(line=n, note=t) for n, t in lines]


def _lq(items: list[tuple[int, str, str, list[str], str]]) -> list[LineQuizItem]:
    out: list[LineQuizItem] = []
    for line, prompt, answer, choices, why in items:
        ch = choices if answer in choices else [answer, *choices]
        out.append(LineQuizItem(line=line, prompt=prompt, answer=answer, choices=ch[:4], why=why))
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 01  TBox / ABox — foundations (simple)
# ═══════════════════════════════════════════════════════════════════════════


def m01_tbox_abox() -> StudyModule:
    return StudyModule(
        id="01-tbox-abox-simple",
        title="1. TBox vs ABox (the only schema rule you need)",
        description="Schema vs data — warehouse rule book vs boxes on shelves.",
        tags=["tbox", "abox", "owl", "rdf"],
        track="foundations",
        order=10,
        estimated_minutes=15,
        story=(
            "The warehouse has ONE rule book on the wall. That book lists allowed shelf labels: "
            "Product, Symptom, FailureMode, Part. That book is the TBox — it almost never changes.\n\n"
            "Trucks deliver boxes: 'washer wm-001 has symptom will-not-drain'. Those boxes are the ABox. "
            "A new product is new boxes, never a new rule book.\n\n"
            "If you remember only one sentence: TBox = kinds of things; ABox = actual things."
        ),
        one_liner="TBox = rule book (classes). ABox = boxes (instances). New SKU = new ABox only.",
        why_it_matters=[
            "Stops you inventing a new ontology file per product.",
            "Lets validation check instances against a shared schema.",
            "Interview trap: people say 'ontology' for both — separate them.",
        ],
        say_aloud=[
            "TBox is the terminological box: shared classes and relationships.",
            "ABox is the assertional box: facts about specific products.",
            "Adding espresso machine esp-001 is ABox under the same TBox.",
            "TBox changes only when we need a new kind of entity, not a new SKU.",
        ],
        cheat_sheet=[
            {"term": "TBox", "meaning": "Schema / vocabulary / classes + properties"},
            {"term": "ABox", "meaning": "Instances / data rows / product packs"},
            {"term": "OWL", "meaning": "Formal language for TBox (+ logic)"},
            {"term": "RDF triple", "meaning": "subject–predicate–object fact"},
            {"term": "Our runtime", "meaning": "Neo4j holds operational ABox; OWL is export/interchange"},
        ],
        beats=[
            CodeBeat(
                id="triple-pattern",
                title="One triple pattern (memorize)",
                language="python",
                goal="Every RDF fact is three parts.",
                narrative="Do not memorize all of rdflib. Memorize: add((subject, predicate, object)).",
                code="""from rdflib import Graph, Namespace, RDF, OWL, Literal, RDFS

WD = Namespace("https://example.org/wd#")
g = Graph()

# TBox: Product is a class
g.add((WD.Product, RDF.type, OWL.Class))
g.add((WD.Product, RDFS.label, Literal("Product")))

# ABox: this washer is a Product
g.add((WD["wm-001"], RDF.type, WD.Product))
g.add((WD["wm-001"], RDFS.label, Literal("Front Load Washer")))""",
                say_after="Class line uses OWL.Class. Instance line uses WD.Product as the type.",
                pro_tips=[
                    "TRICK: in Turtle `a` is exactly rdf:type — 'wm-001 a Product' reads like English (W3C RDF Primer §5.1).",
                    "GOTCHA: literals (strings/numbers) may only sit in the OBJECT position — never subject or predicate.",
                    "TRICK: reuse an existing IRI/vocabulary instead of minting your own — shared IRIs are what let graphs merge.",
                ],
                annotations=_ann(
                    [
                        (6, "TBox: declare a class."),
                        (10, "ABox: individual typed as that class."),
                        (7, "Human label — not required for logic, useful for people."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            6,
                            "Is this TBox or ABox?",
                            "TBox — declaring a class",
                            ["ABox — a real washer", "Cypher MERGE", "Cache key"],
                            "OWL.Class means vocabulary, not a product instance.",
                        ),
                        (
                            10,
                            "Is this TBox or ABox?",
                            "ABox — a product individual",
                            ["TBox class definition", "SPARQL PREFIX", "Redis TTL"],
                            "RDF.type WD.Product means this URI is an instance.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="g.add((WD.Product, RDF.type, {{a}}))\ng.add((WD['wm-001'], RDF.type, {{b}}))",
                    blanks=[
                        BlankSpec(id="a", answer="OWL.Class", hint="class marker"),
                        BlankSpec(id="b", answer="WD.Product", hint="your domain class"),
                    ],
                ),
            ),
            CodeBeat(
                id="turtle-mini",
                title="Same idea in Turtle (read-only)",
                language="turtle",
                goal="Read three lines of Turtle without panic.",
                narrative="Turtle is just a compact way to write triples.",
                code="""@prefix wd:  <https://example.org/wd#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

wd:Product a owl:Class .
wd:wm-001  a wd:Product .""",
                say_after="`a` means rdf:type. First line class, second line instance.",
                annotations=_ann(
                    [
                        (4, "TBox class."),
                        (5, "ABox individual."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            4,
                            "What does `a owl:Class` mean?",
                            "rdf:type owl:Class",
                            ["Creates Neo4j node", "Deletes class", "Runs SPARQL"],
                            "Turtle sugar for type assertion.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="TBox",
                definition="Shared schema: what kinds of nodes/edges are allowed.",
                analogy="CREATE TABLE",
                say_aloud="TBox is the rule book on the wall.",
            ),
            ConceptCard(
                term="ABox",
                definition="Instance data: this product, this symptom, this edge.",
                analogy="INSERT rows",
                say_aloud="ABox is the boxes of facts on the shelves.",
            ),
        ],
        self_quiz=[
            QuizItem(q="New product SKU — TBox or ABox?", a="ABox under existing TBox."),
            QuizItem(q="When does TBox change?", a="Only when you need a new kind of entity/relationship."),
            QuizItem(q="SQL analogy?", a="TBox ≈ schema, ABox ≈ rows."),
        ],
        common_mistakes=[
            "Making one OWL file per product.",
            "Calling Neo4j data 'the ontology' without distinguishing schema vs instances.",
        ],
        final_boss=[
            "45s: warehouse story for TBox vs ABox.",
            "From memory: write 4 rdflib lines — class Product + instance wm-001.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 02  Cypher — create + retrieve (simple)
# ═══════════════════════════════════════════════════════════════════════════


def m02_cypher() -> StudyModule:
    return StudyModule(
        id="02-cypher-create-read",
        title="2. Cypher: write graph, read graph (always $params)",
        description="MERGE to create; MATCH to retrieve; never f-string user input.",
        tags=["cypher", "neo4j", "retrieval"],
        track="graph",
        order=20,
        estimated_minutes=20,
        story=(
            "Cypher is how we talk to Neo4j. Two verbs matter most:\n"
            "• MERGE — put this pattern in the graph if missing (upsert).\n"
            "• MATCH — find this pattern and return it.\n\n"
            "Golden rule: always pass values as $parameters. Never glue user text into the query string. "
            "That is safer and lets Neo4j cache the plan."
        ),
        one_liner="MERGE to write, MATCH to read, $params always, scope by product_id.",
        why_it_matters=[
            "Diagnosis is multi-hop graph lookup, not a document search.",
            "Parameterization = security + speed.",
            "Product scope keeps queries small and accurate.",
        ],
        say_aloud=[
            "MERGE upserts a node or relationship by key.",
            "MATCH finds patterns; RETURN projects columns.",
            "I always bind product_id first so search stays scoped.",
            "User input goes in $params, never in an f-string.",
        ],
        cheat_sheet=[
            {"term": "MERGE", "meaning": "Create if not exists (idempotent write)"},
            {"term": "MATCH", "meaning": "Read / pattern search"},
            {"term": "$param", "meaning": "Bound value — safe + plan cache"},
            {"term": "INDICATES", "meaning": "Symptom → FailureMode edge with confidence"},
            {"term": "Scope", "meaning": "Start from Product {product_id: $id}"},
        ],
        beats=[
            CodeBeat(
                id="merge-path",
                title="Write: MERGE a tiny diagnostic path",
                language="cypher",
                goal="Memorize the MERGEs for product → symptom → failure mode.",
                narrative="Three nodes, two relationships. Confidence lives on INDICATES.",
                code="""MERGE (p:Product {product_id: $product_id})
  ON CREATE SET p.name = $name
MERGE (s:Symptom {symptom_id: $symptom_id})
  ON CREATE SET s.description = $description
MERGE (fm:FailureMode {failure_mode_id: $fm_id})
  ON CREATE SET fm.name = $fm_name
MERGE (p)-[:HAS_SYMPTOM]->(s)
MERGE (s)-[:INDICATES {confidence: $confidence}]->(fm)
RETURN p, s, fm""",
                say_after="Keys are business ids. confidence is a relationship property.",
                pro_tips=[
                    "TRICK: MERGE = get-or-create; it keeps re-ingest idempotent (no duplicate nodes).",
                    "GOTCHA: never f-string user input into Cypher — pass $params (injection-safe + lets Neo4j cache the plan).",
                    "TRICK: bind the most selective anchor first ($product_id); PROFILE the query to confirm db-hits use an index.",
                ],
                annotations=_ann(
                    [
                        (1, "Upsert Product by business key."),
                        (8, "INDICATES edge carries likelihood."),
                        (1, "$product_id is a parameter — not string concat."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            8,
                            "Where is confidence stored?",
                            "On the INDICATES relationship",
                            ["Only on Product node", "In Redis", "In the LLM prompt"],
                            "Edge property = P(symptom|failure)-style weight.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="MERGE (s)-[:{{r}} {{confidence: $confidence}}]->(fm)",
                    blanks=[BlankSpec(id="r", answer="INDICATES", hint="symptom→FM rel type")],
                ),
            ),
            CodeBeat(
                id="match-rank",
                title="Read: MATCH candidates for one product",
                language="cypher",
                goal="Always start at Product; never scan the whole graph first.",
                narrative="This is the spine of GraphRAG retrieval.",
                code="""MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
WHERE s.symptom_id IN $symptom_ids
WITH fm, sum(coalesce(ind.confidence, 0)) AS score
RETURN fm.failure_mode_id AS id, fm.name AS name, score
ORDER BY score DESC""",
                say_after="Product first, then optional symptom links, then order by score.",
                annotations=_ann(
                    [
                        (1, "Scope: one product only."),
                        (3, "Only observed symptoms participate."),
                        (6, "Highest link score first — Python may refine with Bayes later."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            1,
                            "Why product_id in the first MATCH?",
                            "Scope search for speed and accuracy",
                            ["Neo4j forbids global MATCH", "It disables indexes", "Only for SPARQL"],
                            "Partition the problem to one product neighborhood.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Parameterized Cypher",
                definition="Values via $name so the query text is stable.",
                say_aloud="Parameters prevent injection and enable plan cache.",
            ),
        ],
        self_quiz=[
            QuizItem(q="MERGE vs MATCH?", a="MERGE writes/upserts; MATCH reads."),
            QuizItem(q="Why not f-string Cypher?", a="Injection risk + no plan reuse."),
            QuizItem(q="First node in diagnosis MATCH?", a="Product with $product_id."),
        ],
        common_mistakes=[
            "Global MATCH (s:Symptom) on large graphs.",
            "Hardcoding ids into the query string.",
        ],
        final_boss=[
            "Write MERGE Product+Symptom+INDICATES+FailureMode with $params from memory.",
            "Explain product-scoped MATCH in 20 seconds.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 03  ETL pipeline — the control plane (GROUND THIS HEAVILY)
# ═══════════════════════════════════════════════════════════════════════════


def m03_etl() -> StudyModule:
    return StudyModule(
        id="03-etl-pipeline",
        title="3. ETL pipeline — extract, build ABox, validate, promote",
        description="How knowledge gets into Neo4j safely. Memorize the chant and why each gate exists.",
        tags=["etl", "pipeline", "promote", "abox", "control-plane"],
        track="pipeline",
        order=30,
        estimated_minutes=30,
        story=(
            "Knowledge does not appear magically in chat. It is loaded through a pipeline:\n\n"
            "1. EXTRACT sources (PIM catalog, FSM work orders, claims, CRM assets, files).\n"
            "2. TRANSFORM into one catalog shaped like our ABox (OntologyBuilder).\n"
            "3. VALIDATE against TBox shapes (min symptoms, links must point to real ids).\n"
            "4. LOAD into staging Neo4j (:7688) with MERGE.\n"
            "5. SMOKE test a few diagnosis phrases.\n"
            "6. PROMOTE to production Neo4j (:7687) — only then does chat see it.\n"
            "7. INVALIDATE caches so old subgraphs die.\n\n"
            "Operator chant (memorize order):\n"
            "Sources → Fetch → Select → Validate ABox → Materialize → Smoke → Approve → "
            "Promote staging → Promote production."
        ),
        one_liner="Extract → ABox build → validate → staging → smoke → production → drop caches.",
        why_it_matters=[
            "Chat must never read half-baked knowledge (staging exists for that).",
            "Validation before promote = fail-closed quality.",
            "Selection-scoped runs let you onboard one SKU without rewriting the fleet.",
        ],
        say_aloud=[
            "Extract pulls from source systems; transform maps fields into shared TBox classes as ABox.",
            "We validate shapes before materialize and promote.",
            "Staging is bolt 7688; production is bolt 7687; chat reads production only.",
            "After load we invalidate named caches so readers see fresh graph data.",
            "A pipeline run can be dry-run to preview without writing Neo4j.",
        ],
        cheat_sheet=[
            {"term": "Extract", "meaning": "Read sources (connectors / files)"},
            {"term": "Transform", "meaning": "OntologyBuilder → catalog JSON ABox"},
            {"term": "Validate", "meaning": "Shapes: required lists + link integrity"},
            {"term": "Materialize", "meaning": "Write selected products into catalog"},
            {"term": "Promote", "meaning": "MERGE catalog into Neo4j env"},
            {"term": "Staging :7688", "meaning": "Safe write/test graph"},
            {"term": "Production :7687", "meaning": "What diagnose/chat reads"},
            {"term": "Dry-run", "meaning": "Run without side-effect load"},
            {"term": "Selection", "meaning": "product_ids scope for one batch"},
        ],
        change_table=[
            {"stage": "Extract", "input": "PIM/FSM/Claims/CRM/files", "output": "raw records"},
            {"stage": "Transform", "input": "raw records", "output": "catalog ABox JSON"},
            {"stage": "Validate", "input": "catalog slice", "output": "ok / errors"},
            {"stage": "Load staging", "input": "valid ABox", "output": "Neo4j :7688"},
            {"stage": "Promote prod", "input": "approved staging", "output": "Neo4j :7687"},
        ],
        beats=[
            CodeBeat(
                id="chant",
                title="Memorize the operator sequence",
                language="text",
                goal="Recite the 9 steps without looking.",
                narrative="If you can chant this, you understand the control plane.",
                code="""Sources
  → Fetch          (preview delta / dry extract)
  → Select         (which product_ids this batch)
  → Validate ABox  (shapes vs TBox)
  → Materialize    (upsert catalog for selection)
  → Smoke          (run known diagnosis phrases)
  → Approve
  → Promote staging   (:7688)
  → Promote production (:7687)
  → Invalidate caches""",
                say_after="Chat never reads staging. Promote is the door.",
                pro_tips=[
                    "TRICK: keep stages idempotent & replayable — a failed promote can be re-run without double-writing (Kleppmann, DDIA).",
                    "GOTCHA: chat must read only the PROMOTED graph, never staging — promotion is the single gate.",
                    "TRICK: tag facts with a named graph / source so you can promote or roll back a whole source atomically.",
                ],
                annotations=_ann(
                    [
                        (4, "Fail here = no bad data later."),
                        (9, "Production only after smoke."),
                        (11, "Stale cache is a silent bug."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            9,
                            "Which port does chat use?",
                            "Production :7687",
                            ["Staging :7688", "Redis :6379", "Frontend :3000"],
                            "Diagnose path is production-only by design.",
                        ),
                    ]
                ),
            ),
            CodeBeat(
                id="pipeline-ids",
                title="Pipeline registry ids (as-built names)",
                language="text",
                goal="Know the real pipeline names in this repo.",
                narrative="These ids show up in Admin / control plane.",
                code="""structured_extract      # PIM / FSM / Claims / CRM connectors
semi_structured_ingest   # CSV / JSONL
unstructured_extract     # manuals / notes patterns
preprocess_normalize     # clean / provisional notes
knowledge_materialize    # OntologyBuilder → catalog (selection)
smoke_validate           # diagnosis scenarios
promote_graph            # MERGE Neo4j staging | production
bootstrap_all            # chain for first build
incremental_sync         # chain for ongoing updates""",
                say_after="Materialize builds ABox; promote_graph writes Neo4j.",
                annotations=_ann(
                    [
                        (5, "This is where ABox is assembled."),
                        (7, "This is the graph load step."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            5,
                            "Which step builds the ABox catalog?",
                            "knowledge_materialize",
                            ["promote_graph", "smoke_validate", "structured_extract only"],
                            "OntologyBuilder runs in materialize.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="{{a}} builds catalog ABox\n{{b}} MERGEs into Neo4j",
                    blanks=[
                        BlankSpec(id="a", answer="knowledge_materialize"),
                        BlankSpec(id="b", answer="promote_graph"),
                    ],
                ),
            ),
            CodeBeat(
                id="etl-code-spine",
                title="Code spine (tiny mental model)",
                language="python",
                goal="Map words to functions — not every file.",
                narrative="Extract can be parallel (I/O). Transform stays serial (deterministic merges).",
                code="""# conceptual spine (names match the platform idea)
records = extract_sources(product_ids)          # I/O — may use thread pool
catalog = ontology_builder.build(records)       # serial transform → ABox
errors  = validate_shapes(catalog)              # fail-closed
if errors:
    raise ValueError(errors)
if not dry_run:
    populate_graph(catalog, env="staging")      # MERGE :7688
    run_smoke(product_ids)
    populate_graph(catalog, env="production")   # MERGE :7687
    invalidate_all_named_caches()""",
                say_after="Parallel extract is OK. Parallel transform is usually not.",
                annotations=_ann(
                    [
                        (2, "Connectors wait on network — threads help."),
                        (3, "One deterministic builder for ABox."),
                        (4, "Shapes before any graph write."),
                        (10, "Caches must die after graph changes."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            2,
                            "Why may extract use threads?",
                            "I/O bound waits on network",
                            ["CPU ranking needs 100 threads", "Neo4j forbids serial", "Only for CSS"],
                            "Waiting on HTTP/files benefits from concurrency.",
                        ),
                        (
                            10,
                            "Why invalidate caches after promote?",
                            "Readers must not see stale subgraphs",
                            ["Redis license expires daily", "Cypher syntax requires it", "UI theme refresh"],
                            "Otherwise diagnose returns old neighborhoods.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template='catalog = ontology_builder.{{fn}}(records)\nif not dry_run:\n    populate_graph(catalog, env="{{env}}")\n    {{inv}}()',
                    blanks=[
                        BlankSpec(id="fn", answer="build", hint="or build_catalog_payload"),
                        BlankSpec(id="env", answer="staging", hint="first load env"),
                        BlankSpec(id="inv", answer="invalidate_all_named_caches"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Dual graph",
                definition="Staging for safe MERGE; production for diagnose reads.",
                say_aloud="7688 then 7687; chat only sees production.",
            ),
            ConceptCard(
                term="Fail-closed validate",
                definition="Bad ABox never promotes.",
                say_aloud="Shapes run before materialize and promote.",
            ),
            ConceptCard(
                term="Selection scope",
                definition="Run pipeline for chosen product_ids only.",
                say_aloud="One SKU batch without rewriting the fleet.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Order: validate vs promote?", a="Validate before promote."),
            QuizItem(q="Does chat read staging?", a="No — production only."),
            QuizItem(q="What does OntologyBuilder produce?", a="Catalog ABox under shared TBox."),
            QuizItem(q="What happens after promote?", a="Invalidate caches."),
            QuizItem(q="Dry-run means?", a="Preview/extract without writing Neo4j."),
        ],
        common_mistakes=[
            "Calling 'Fetch' an ontology build — Fetch previews sources/delta.",
            "Promoting without smoke.",
            "Forgetting cache invalidation.",
        ],
        final_boss=[
            "Recite the operator chant start to finish.",
            "Draw Extract → Transform → Validate → Stage → Prod on paper.",
            "Name three pipeline registry ids and what they do.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 04  Caching — grounded and simple
# ═══════════════════════════════════════════════════════════════════════════


def m04_cache() -> StudyModule:
    return StudyModule(
        id="04-caching",
        title="4. Caching — remember the answer for a short time",
        description="What to cache, how to key it, when to kill it. Memory vs Redis.",
        tags=["cache", "redis", "ttl", "performance"],
        track="runtime",
        order=40,
        estimated_minutes=25,
        story=(
            "Caching means: if we already computed something expensive and nothing important changed, "
            "return the saved answer instead of hitting Neo4j again.\n\n"
            "Three rules:\n"
            "1. KEY must include every input that changes the answer.\n"
            "2. TTL (time-to-live) limits how old the answer can be.\n"
            "3. INVALIDATE when the graph is reloaded — otherwise users see ghosts.\n\n"
            "One cashier: a notepad (in-process memory) is enough.\n"
            "Ten cashiers (API replicas): they need one shared whiteboard (Redis), "
            "or each has a different notepad and rate limits lie."
        ),
        one_liner="Key correctly, expire with TTL, invalidate on promote; Redis when multi-pod.",
        why_it_matters=[
            "Ontology and product subgraphs are hot reads.",
            "Wrong keys cause silent wrong answers or privacy leaks.",
            "Multi-replica without Redis = divergent limits and caches.",
        ],
        say_aloud=[
            "A cache key must include every input that changes the result.",
            "TTL is how long we trust a cached value.",
            "After promote or graph load I invalidate named caches.",
            "Empty REDIS_URL means in-process memory; multi-pod needs Redis.",
            "I do not blindly cache free-text diagnosis without a strong key.",
        ],
        cheat_sheet=[
            {"term": "Hit", "meaning": "Answer found in cache"},
            {"term": "Miss", "meaning": "Must compute + set"},
            {"term": "TTL", "meaning": "Seconds until entry expires"},
            {"term": "Named cache", "meaning": "e.g. ontology, subgraph, diagnose"},
            {"term": "Invalidate", "meaning": "Delete entries after data change"},
            {"term": "Memory backend", "meaning": "Per process — demo/single node"},
            {"term": "Redis backend", "meaning": "Shared across API pods"},
        ],
        beats=[
            CodeBeat(
                id="get-or-set",
                title="Pattern: get → compute → set",
                language="python",
                goal="Write the 6-line cache pattern from memory.",
                narrative="This is the entire idea.",
                code="""def cached_get(cache, key, compute, ttl_seconds=60):
    hit = cache.get(key)
    if hit is not None:
        return hit                  # HIT
    value = compute()               # MISS — do the real work
    cache.set(key, value, ttl_seconds=ttl_seconds)
    return value

# Good key: every input that changes the answer
key = f"subgraph:{tenant}:{product_id}"

# After ETL / promote
# invalidate_all_named_caches()""",
                say_after="Hit returns early. Miss computes once then stores.",
                pro_tips=[
                    "TRICK: cache-aside = get → miss → compute → set with a TTL; the hard part is invalidation, not lookup.",
                    "GOTCHA: only cache DETERMINISTIC, non-personalized reads — caching per-user results can leak data.",
                    "TRICK: for a pure function in-process, @lru_cache(maxsize=N) is the simplest correct cache (Python docs).",
                ],
                annotations=_ann(
                    [
                        (2, "Look up first."),
                        (5, "Only on miss do we pay Neo4j cost."),
                        (6, "Store with TTL."),
                        (10, "Key composition is the hard part."),
                        (13, "Invalidation is mandatory after graph writes."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            10,
                            "What must a good cache key include?",
                            "Every input that changes the answer",
                            ["Only the current hour", "A random UUID always", "Just the word cache"],
                            "Missing product_id ⇒ wrong product subgraph.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="hit = cache.{{g}}(key)\nif hit is not None:\n    return hit\nvalue = compute()\ncache.{{s}}(key, value, ttl_seconds=60)",
                    blanks=[
                        BlankSpec(id="g", answer="get"),
                        BlankSpec(id="s", answer="set"),
                    ],
                ),
            ),
            CodeBeat(
                id="what-we-cache",
                title="What this platform caches (as-built idea)",
                language="text",
                goal="Know three named hot paths.",
                narrative="Concrete numbers help interviews.",
                code="""ontology schema     TTL ~ 300s   (changes rarely)
product subgraph    TTL ~ 60s    (explorer / neighborhood)
diagnose result     TTL ~ 90s    (optional; key must be strong)

NOT a free lunch:
  - free-text diagnosis without product+symptoms+tenant in the key
  - caching across promote without invalidation""",
                say_after="Stable reads yes; careless personalization no.",
                annotations=_ann([(1, "Schema is hot and stable."), (6, "Danger zone.")]),
                line_quiz=_lq(
                    [
                        (
                            3,
                            "Approx diagnose cache TTL in this platform?",
                            "~90 seconds",
                            ["90 days", "Never expires", "1 millisecond"],
                            "Short TTL limits staleness.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="TTL",
                definition="Max age of a cached value.",
                say_aloud="Time-to-live caps staleness.",
            ),
            ConceptCard(
                term="Shared Redis cache",
                definition="All API pods read/write the same keys.",
                say_aloud="Multi-replica needs Redis for one truth.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Hit vs miss?", a="Hit returns stored value; miss computes and sets."),
            QuizItem(q="When invalidate?", a="After graph load / promote / ETL that changes data."),
            QuizItem(q="Is Redis required for laptop demo?", a="No — memory backend is fine single-node."),
            QuizItem(q="Bad key example?", a="key='diagnose' with no product/symptoms."),
        ],
        common_mistakes=[
            "Caching forever with no invalidation.",
            "Different key formats for rate-limit vs cache (partition module fixes that).",
        ],
        final_boss=[
            "Write get/set cache function from blank page.",
            "Design a diagnose cache key for tenant+product+symptoms.",
            "Explain memory vs Redis in one sentence each.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 05  Multi-threading / concurrency
# ═══════════════════════════════════════════════════════════════════════════


def m05_threads() -> StudyModule:
    return StudyModule(
        id="05-multithreading",
        title="5. Multi-threading — when parallel helps (and when it hurts)",
        description="I/O fan-out with a bound; keep ranking serial; admit only N diagnoses at once.",
        tags=["threading", "concurrency", "parallel", "admission"],
        track="runtime",
        order=50,
        estimated_minutes=25,
        story=(
            "Threads are workers. If four workers each wait on a slow connector, total time is "
            "about the slowest wait — not four times one wait. That is I/O parallelism.\n\n"
            "If four workers all thrash the same CPU-heavy ranking with shared mutable state, "
            "you get bugs and little speedup (Python GIL + race conditions).\n\n"
            "Rules for this platform:\n"
            "• EXTRACT connectors: parallel OK (bound the pool, e.g. max_workers=4).\n"
            "• TRANSFORM / Bayes ranking: serial, deterministic.\n"
            "• ADMISSION: only N diagnoses in flight (semaphore / Redis counter) so Neo4j is not crushed."
        ),
        one_liner="Parallel I/O with a bound; serial transform; limit in-flight diagnoses.",
        why_it_matters=[
            "Connector fan-out is mostly waiting on network.",
            "Unbounded threads open too many DB sessions under load.",
            "Admission control protects p99 latency.",
        ],
        say_aloud=[
            "I parallelize independent I/O, not the core ranking math.",
            "ThreadPoolExecutor needs max_workers — never unbounded.",
            "Admission control caps concurrent expensive diagnose calls.",
            "Shared mutable state across threads needs locks or immutability.",
        ],
        cheat_sheet=[
            {"term": "I/O bound", "meaning": "Time spent waiting (network/disk) — threads help"},
            {"term": "CPU bound", "meaning": "Heavy compute — threads help less in CPython"},
            {"term": "max_workers", "meaning": "Ceiling on parallel tasks"},
            {"term": "Admission control", "meaning": "Max in-flight expensive requests"},
            {"term": "Semaphore", "meaning": "Counter that blocks when full"},
            {"term": "GIL", "meaning": "CPython lock — pure-Python CPU parallelism limited"},
        ],
        beats=[
            CodeBeat(
                id="thread-pool",
                title="Parallel extract with a bound",
                language="python",
                goal="Write ThreadPoolExecutor map with max_workers.",
                narrative="Four connectors fetch at once; results collected; then serial build.",
                code="""from concurrent.futures import ThreadPoolExecutor

def fetch_all(fetch_fns: list, max_workers: int = 4) -> list:
    # Bound the pool — protects sockets and the source systems
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(lambda fn: fn(), fetch_fns))

records = fetch_all([fetch_pim, fetch_fsm, fetch_claims, fetch_crm])
catalog = build_abox_serial(records)   # serial on purpose""",
                say_after="map runs functions concurrently; build stays single-threaded.",
                pro_tips=[
                    "GOTCHA: CPython's GIL means threads help I/O-bound waits, NOT CPU-bound work — use processes for CPU parallelism (Python docs).",
                    "TRICK: parallel EXTRACT (I/O) is safe; parallel TRANSFORM often isn't — shared mutable state races.",
                    "TRICK: prefer concurrent.futures ThreadPoolExecutor.map over manual threads; always cap max_workers.",
                ],
                annotations=_ann(
                    [
                        (5, "Context manager shuts workers down cleanly."),
                        (6, "max_workers is the safety rail."),
                        (9, "Deterministic merge after all I/O returns."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            6,
                            "Why set max_workers?",
                            "Bound concurrency — avoid storms",
                            ["Python requires exactly 4", "Disables the GIL", "Only for Cypher"],
                            "Unbounded pools exhaust FDs and backends.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="with ThreadPoolExecutor(max_workers={{n}}) as pool:\n    return list(pool.{{m}}(lambda fn: fn(), fetch_fns))",
                    blanks=[
                        BlankSpec(id="n", answer="4", hint="small integer bound"),
                        BlankSpec(id="m", answer="map"),
                    ],
                ),
            ),
            CodeBeat(
                id="admission",
                title="Admission: only N diagnoses at once",
                language="python",
                goal="Explain acquire/release around expensive work.",
                narrative="Like a nightclub bouncer: capacity 32.",
                code="""# conceptual — matches ConcurrencyLimiter idea
class Admission:
    def __init__(self, max_in_flight=32):
        self.max_in_flight = max_in_flight
        self._in_flight = 0

    def run(self, fn):
        if self._in_flight >= self.max_in_flight:
            raise RuntimeError("busy — retry later")  # HTTP 429/503
        self._in_flight += 1
        try:
            return fn()
        finally:
            self._in_flight -= 1  # always release""",
                say_after="Always release in finally so a crash does not leak a slot.",
                annotations=_ann(
                    [
                        (7, "Reject when full — backpressure."),
                        (11, "finally releases even on exception."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            11,
                            "Why finally?",
                            "Release slot even if fn raises",
                            ["Faster CPU", "Required by Neo4j", "Disables cache"],
                            "Otherwise in_flight leaks and system stays 'full'.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Parallel extract",
                definition="Fetch independent sources concurrently.",
                say_aloud="I/O fan-out with a worker ceiling.",
            ),
            ConceptCard(
                term="Serial transform",
                definition="Build ABox and rank deterministically in one flow.",
                say_aloud="No race conditions in confidence merges.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Parallelize extract or Bayes?", a="Extract (I/O). Keep Bayes/transform serial."),
            QuizItem(q="What is admission control?", a="Cap in-flight expensive requests."),
            QuizItem(q="Why max_workers?", a="Bound resource use."),
        ],
        common_mistakes=[
            "Spawning a thread per HTTP request without a pool.",
            "Sharing a non-thread-safe dict across workers without locks.",
        ],
        final_boss=[
            "Write ThreadPoolExecutor fetch_all from memory.",
            "Explain GIL in one honest sentence.",
            "Describe diagnose admission in 15 seconds.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 06  Partitioning
# ═══════════════════════════════════════════════════════════════════════════


def m06_partition() -> StudyModule:
    return StudyModule(
        id="06-partitioning",
        title="6. Partitioning — split work and keys on purpose",
        description="Logical keys today; physical shards later. Same key shape everywhere.",
        tags=["partition", "tenant", "scale", "sharding"],
        track="runtime",
        order=60,
        estimated_minutes=20,
        story=(
            "Partitioning means: do not treat the whole world as one pile.\n\n"
            "• Data partition: only this tenant / product line's knowledge.\n"
            "• Work partition: ETL one product_ids slice at a time.\n"
            "• Key partition: cache and rate-limit keys include tenant|product so "
            "customers never share a bucket.\n\n"
            "Today this repo mostly uses LOGICAL keys (strings). Physical Neo4j Fabric "
            "shards are a later scale step — same keys, different storage."
        ),
        one_liner="Same key language for cache, rate limit, and future shards: tenant|product|…",
        why_it_matters=[
            "Prevents one noisy tenant from exhausting everyone's rate limit.",
            "Keeps ETL batches small and reviewable.",
            "Prepares for multi-region without renaming everything later.",
        ],
        say_aloud=[
            "A partition key names the slice of the world we are working on.",
            "Rate limits and caches must use the same key dimensions.",
            "Selection-scoped promote is work partitioning by product_id.",
            "Logical keys now; physical Fabric or multi-DB later if needed.",
        ],
        cheat_sheet=[
            {"term": "Logical partition", "meaning": "Key design only — one DB still"},
            {"term": "Physical partition", "meaning": "Data lives on different servers/shards"},
            {"term": "tenant_id", "meaning": "Who owns the data (customer org)"},
            {"term": "product_id slice", "meaning": "ETL/query limited to listed products"},
            {"term": "Key agreement", "meaning": "Cache + rate-limit + logs share shape"},
        ],
        beats=[
            CodeBeat(
                id="key-shape",
                title="Canonical key shape",
                language="python",
                goal="Build partition strings from memory.",
                narrative="Boring strings prevent subtle multi-tenant bugs.",
                code="""def partition_key(tenant_id: str, product_id: str | None = None) -> str:
    parts = [f"tenant={tenant_id or 'default'}"]
    if product_id:
        parts.append(f"product={product_id}")
    return "|".join(parts)

# Uses
rate_key  = partition_key("acme", None) + "|route=/diagnose"
cache_key = partition_key("acme", "wm-001") + "|res=subgraph"

# Work partition (ETL)
product_ids = ["wm-001", "esp-001"]   # only these this run""",
                say_after="tenant always; product when the data is product-scoped.",
                pro_tips=[
                    "TRICK: partition by a key (tenant/product) to spread load; always scope queries by that key (Kleppmann, DDIA Ch.6).",
                    "GOTCHA: watch for hot keys/skew — one huge tenant can unbalance an otherwise even partition scheme.",
                ],
                annotations=_ann(
                    [
                        (2, "Stable prefix."),
                        (6, "Rate limit per tenant (and route)."),
                        (7, "Cache per tenant+product resource."),
                        (10, "ETL selection list = work partition."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            7,
                            "Why product in subgraph cache key?",
                            "Different products have different neighborhoods",
                            ["Redis requires product", "Cypher ignores product", "UI color theme"],
                            "Otherwise wm data could be served for esp.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template='parts = [f"tenant={{t}}"]\nif product_id:\n    parts.append(f"product={{p}}")\nreturn "|".join(parts)',
                    blanks=[
                        BlankSpec(id="t", answer="{tenant_id}"),
                        BlankSpec(id="p", answer="{product_id}"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Work partition",
                definition="Process a subset (product_ids) per pipeline run.",
                say_aloud="Selection-scoped materialize is work partitioning.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Logical vs physical partition?", a="Logical=keys; physical=separate storage."),
            QuizItem(q="Why same key shape for cache and rate limit?", a="One vocabulary; no cross-tenant bleed."),
            QuizItem(q="Example work partition?", a="Promote only product_ids=['esp-001']."),
        ],
        common_mistakes=[
            "Global rate limit key for all tenants.",
            "Cache key missing tenant in multi-tenant SaaS.",
        ],
        final_boss=[
            "Write partition_key() from memory.",
            "Give one logical and one physical partition example.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 07  Accurate retrieval + Bayes (short)
# ═══════════════════════════════════════════════════════════════════════════


def m07_retrieval() -> StudyModule:
    return StudyModule(
        id="07-retrieval-bayes",
        title="7. Accurate retrieval — scope, match, rank, escalate",
        description="Four steps only. Miss likelihood for sparse edges. No magic.",
        tags=["graphrag", "bayes", "accuracy"],
        track="graph",
        order=70,
        estimated_minutes=20,
        story=(
            "Fast is useless if wrong. Accurate diagnosis retrieval is four steps:\n"
            "1. SCOPE — know the product/asset.\n"
            "2. MATCH — map customer words to symptom ids (lexical/TF-IDF hybrid).\n"
            "3. RANK — walk INDICATES; Bayes: posterior ∝ prior × ∏ likelihoods.\n"
            "4. GATE — if evidence is weak, escalate; do not fake confidence.\n\n"
            "Sparse data: missing edge uses a small miss likelihood — we do not invent edges."
        ),
        one_liner="Scope → match → Bayes on INDICATES → escalate if weak.",
        why_it_matters=[
            "Wrong part costs money and trust.",
            "Sparse warranty graphs are normal — gates matter.",
        ],
        say_aloud=[
            "I resolve product before ranking failure modes.",
            "Likelihoods come from INDICATES.confidence.",
            "Posterior is proportional to prior times product of likelihoods.",
            "If the top posterior is weak I escalate.",
        ],
        cheat_sheet=[
            {"term": "Prior P(fm)", "meaning": "How common is this failure (e.g. from occurrence)"},
            {"term": "Likelihood P(s|fm)", "meaning": "INDICATES.confidence"},
            {"term": "Posterior", "meaning": "Belief in fm after seeing symptoms"},
            {"term": "Miss likelihood", "meaning": "Default when edge absent (soft, not zero panic)"},
        ],
        beats=[
            CodeBeat(
                id="bayes-loop",
                title="Naive Bayes in 12 lines",
                language="python",
                goal="Write the multiply-and-normalize loop.",
                narrative="This is the math interview whiteboard.",
                code="""def bayesian_posteriors(priors, likelihoods, observed, candidates, miss=0.05):
    scores = {}
    for fm in candidates:
        score = max(priors.get(fm, 0.0), 0.0)
        for s in observed:
            score *= likelihoods.get((s, fm), miss)
        scores[fm] = score
    total = sum(scores.values()) or 1.0
    return {fm: v / total for fm, v in scores.items()}

# then: if max(posteriors.values()) < THRESHOLD: escalate()""",
                say_after="Multiply likelihoods; normalize so they sum to one.",
                pro_tips=[
                    "TRICK: multiply prior × likelihoods, then normalize so posteriors sum to 1.",
                    "GOTCHA: use a small 'miss' default for unseen (symptom, failure) pairs so one gap doesn't zero the whole score.",
                    "TRICK: GraphRAG = vector/fulltext to find entry nodes, then traverse 1–2 hops for connected, explainable context (Neo4j GraphRAG).",
                ],
                annotations=_ann(
                    [
                        (4, "Start from prior."),
                        (6, "Missing edge → miss, not crash."),
                        (9, "Normalize to a probability distribution."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            6,
                            "What is miss for?",
                            "Default likelihood when INDICATES edge is absent",
                            ["Delete the failure mode", "Redis TTL", "HTTP status"],
                            "Sparse graphs need a soft default.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="score *= likelihoods.get((s, fm), {{m}})\ntotal = sum(scores.values()) or 1.0\nreturn {fm: v / total for fm, v in scores.items()}",
                    blanks=[BlankSpec(id="m", answer="miss")],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="GraphRAG (here)",
                definition="Retrieve typed graph evidence, then format the answer.",
                say_aloud="Evidence from Neo4j first; LLM wording optional.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Four retrieval steps?", a="Scope, match, rank, gate/escalate."),
            QuizItem(q="Where is P(s|fm)?", a="INDICATES.confidence."),
        ],
        common_mistakes=[
            "Ranking without product scope.",
            "Treating RPN as a probability.",
        ],
        final_boss=[
            "Write bayesian_posteriors from memory.",
            "Trace 'won't drain E21 on wm-001' through four steps aloud.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 08  LangGraph agent (simple contrast)
# ═══════════════════════════════════════════════════════════════════════════


def m08_langgraph() -> StudyModule:
    return StudyModule(
        id="08-langgraph-agent",
        title="8. LangGraph agent — fixed belt vs smart Cypher tool",
        description="Memorize the production four-node belt; know the interview alternate.",
        tags=["langgraph", "agent", "tools"],
        track="agent",
        order=80,
        estimated_minutes=20,
        story=(
            "LangGraph is a flowchart that holds state.\n\n"
            "THIS PRODUCT (deterministic):\n"
            "detect_product → run_diagnosis → format_response → handle_escalation\n"
            "Diagnosis guts = fixed Cypher + Bayes. LLM is optional wording only.\n\n"
            "INTERVIEW ALTERNATE (smart Cypher tool):\n"
            "Outer model decides to call a tool; inside the tool a second model writes Cypher; "
            "try/except runs it. Flexible, less deterministic.\n\n"
            "Same skeleton idea: State → nodes → edges → compile. Different guts."
        ),
        one_liner="Production: four fixed nodes + GraphRAG. Interview alt: tool that generates Cypher.",
        why_it_matters=[
            "Warranty needs auditability — fixed queries help.",
            "Interviewers often teach LLM-written Cypher — you must contrast.",
        ],
        say_aloud=[
            "Our diagnose path is detect, diagnose, format, escalate.",
            "tool_diagnose calls GraphRAG with parameterized Cypher.",
            "Smart Cypher agents use two LLM jobs: route and write query.",
            "I always try/except untrusted generated Cypher.",
        ],
        cheat_sheet=[
            {"term": "StateGraph", "meaning": "Blueprint of nodes and edges"},
            {"term": "compile()", "meaning": "Runnable app"},
            {"term": "Tool", "meaning": "Function the agent may call"},
            {"term": "Deterministic path", "meaning": "Fixed Cypher + scores"},
        ],
        beats=[
            CodeBeat(
                id="four-nodes",
                title="Production four-node belt",
                language="python",
                goal="Write build_diagnosis_graph wiring from memory.",
                narrative="Thin nodes; intelligence in graph_rag.",
                code="""from langgraph.graph import StateGraph, END

def build_diagnosis_graph():
    g = StateGraph(AgentState)
    g.add_node("detect_product", node_detect_product)
    g.add_node("run_diagnosis", node_run_graph_diagnosis)
    g.add_node("format_response", node_format_response)
    g.add_node("handle_escalation", node_handle_escalation)
    g.set_entry_point("detect_product")
    g.add_edge("detect_product", "run_diagnosis")
    g.add_edge("run_diagnosis", "format_response")
    g.add_edge("format_response", "handle_escalation")
    g.add_edge("handle_escalation", END)
    return g.compile()""",
                say_after="Entry detect_product; end after escalation handler.",
                pro_tips=[
                    "TRICK: model the agent as a state graph — nodes mutate a typed state, conditional edges route control (LangGraph).",
                    "GOTCHA: give the graph a clear END after the escalation handler so it can't loop forever.",
                    "TRICK: ReAct pattern = thought → action(tool) → observation, repeated until there's enough context (Yao et al., 2022).",
                ],
                annotations=_ann(
                    [
                        (5, "Resolve product/asset first."),
                        (6, "GraphRAG + Bayes here."),
                        (10, "Linear happy path."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            6,
                            "Where does ranking run?",
                            "Inside run_diagnosis / GraphRAG",
                            ["Only in CSS", "Inside Redis", "In the browser only"],
                            "Node calls tool_diagnose → graph_rag.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template='g.set_entry_point("{{e}}")\ng.add_edge("run_diagnosis", "{{n}}")',
                    blanks=[
                        BlankSpec(id="e", answer="detect_product"),
                        BlankSpec(id="n", answer="format_response"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Two-LLM smart tool",
                definition="Router LLM + Cypher-writer LLM inside the tool.",
                say_aloud="Flexible; must sandbox and try/except.",
            ),
        ],
        self_quiz=[
            QuizItem(
                q="Four production nodes?", a="detect_product, run_diagnosis, format_response, handle_escalation."
            ),
            QuizItem(q="Is LLM required for diagnosis here?", a="No — GraphRAG primary."),
        ],
        common_mistakes=[
            "Describing this product as LLM-written Cypher.",
        ],
        final_boss=[
            "Draw both agent styles side by side.",
            "Write the four add_edge lines from memory.",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 09  SHACL lite
# ═══════════════════════════════════════════════════════════════════════════


def m09_shacl() -> StudyModule:
    return StudyModule(
        id="09-shacl-gates",
        title="9. SHACL-style gates — clipboard before promote",
        description="Closed-world checks vs open-world OWL. Min evidence rules.",
        tags=["shacl", "validation", "quality"],
        track="pipeline",
        order=90,
        estimated_minutes=15,
        story=(
            "OWL can describe meaning in an open world (missing fact ≠ false). "
            "SHACL is the clipboard at the dock: before promote, required fields and links must exist.\n\n"
            "This app uses a Python lite validator with the same job: min symptoms, min failure modes, "
            "min INDICATES links, every link id must exist in the pack."
        ),
        one_liner="Shapes fail-closed before promote; reasoner is optional offline, not diagnose-path.",
        why_it_matters=["Bad ABox in production = wrong diagnosis at scale."],
        say_aloud=[
            "We shape-check ABox before materialize and promote.",
            "Minimum evidence: at least one symptom, failure mode, and INDICATES link.",
            "OWL open world is not the same as SHACL closed world.",
        ],
        cheat_sheet=[
            {"term": "SHACL", "meaning": "Shapes Constraint Language — data quality"},
            {"term": "Open world", "meaning": "OWL: unknown ≠ false"},
            {"term": "Closed world", "meaning": "Shapes: missing required = invalid"},
        ],
        beats=[
            CodeBeat(
                id="min-evidence",
                title="Min evidence rules",
                language="python",
                goal="Recite the three mins.",
                narrative="If you ship empty products, ranking has nothing to stand on.",
                code="""MIN_SYMPTOMS = 1
MIN_FAILURE_MODES = 1
MIN_INDICATES_LINKS = 1

def validate_bundle(bundle: dict) -> list[str]:
    errors = []
    if len(bundle.get("symptoms") or []) < MIN_SYMPTOMS:
        errors.append("need ≥1 symptom")
    if len(bundle.get("failure_modes") or []) < MIN_FAILURE_MODES:
        errors.append("need ≥1 failure mode")
    if len(bundle.get("symptom_failure_links") or []) < MIN_INDICATES_LINKS:
        errors.append("need ≥1 INDICATES link")
    return errors  # empty list => ok""",
                say_after="Three mins; non-empty errors means block promote.",
                pro_tips=[
                    "GOTCHA: sh:conforms is true ONLY if there are zero results — even a Warning-severity result fails conformance (W3C SHACL §3.6).",
                    "TRICK: non-empty results = block promote; read sh:sourceConstraintComponent to see exactly which rule fired.",
                    "TRICK: tier rules with sh:severity (Info/Warning/Violation); the default is Violation.",
                ],
                annotations=_ann([(8, "Block empty evidence packs.")]),
                line_quiz=_lq(
                    [
                        (
                            11,
                            "Why require INDICATES links?",
                            "Ranking needs symptom→FM evidence edges",
                            ["Neo4j license", "Redis cluster", "CSS grid"],
                            "Without links GraphRAG cannot score.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="MIN_SYMPTOMS = {{a}}\nMIN_INDICATES_LINKS = {{b}}",
                    blanks=[
                        BlankSpec(id="a", answer="1"),
                        BlankSpec(id="b", answer="1"),
                    ],
                ),
            ),
        ],
        concepts=[],
        self_quiz=[
            QuizItem(q="OWL vs SHACL one-liner?", a="OWL meaning; SHACL instance quality."),
            QuizItem(q="When validate?", a="Before materialize/promote."),
        ],
        common_mistakes=["Validating only after production load."],
        final_boss=["Write validate_bundle mins from memory."],
    )


def all_seed_modules() -> list[StudyModule]:
    from study.seed_platform_modules import platform_modules

    return [
        m01_tbox_abox(),
        m02_cypher(),
        m03_etl(),
        m04_cache(),
        m05_threads(),
        m06_partition(),
        m07_retrieval(),
        m08_langgraph(),
        m09_shacl(),
        *platform_modules(),
    ]


def write_all_seeds(*, wipe_old: bool = True) -> list[str]:
    """Write grounded seeds + authoritative flashcard deck."""
    MODULES_DIR.mkdir(parents=True, exist_ok=True)
    if wipe_old:
        for path in MODULES_DIR.glob("*.json"):
            # keep user uploads prefixed u-
            if path.name.startswith("u-"):
                continue
            path.unlink(missing_ok=True)
    ids: list[str] = []
    for m in all_seed_modules():
        save_module(m)
        ids.append(m.id)
    try:
        from study.flashcards_deck import write_deck

        write_deck()
    except Exception:
        pass
    return ids


if __name__ == "__main__":
    ids = write_all_seeds()
    from study.flashcards_deck import load_deck

    print("Wrote grounded seeds:", ids)
    print("Flashcards:", len(load_deck()))
