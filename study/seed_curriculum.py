"""Hand-authored high-quality seed modules for interview Study Lab."""

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
from study.store import save_module


def _ann(lines: list[tuple[int, str]]) -> list[LineAnnotation]:
    return [LineAnnotation(line=n, note=t) for n, t in lines]


def _lq(items: list[tuple[int, str, str, list[str]]]) -> list[LineQuizItem]:
    out = []
    for line, prompt, answer, choices in items:
        ch = choices if answer in choices else [answer, *choices]
        out.append(LineQuizItem(line=line, prompt=prompt, answer=answer, choices=ch[:4]))
    return out


def module_rdf_owl() -> StudyModule:
    code_classes = """from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef

WD = Namespace("https://example.org/warranty-diagnosis#")
g = Graph()
g.bind("wd", WD)
g.bind("owl", OWL)
g.bind("rdfs", RDFS)

# Every class is three triples: type, label, comment
g.add((WD.Product, RDF.type, OWL.Class))
g.add((WD.Product, RDFS.label, Literal("Product")))
g.add((WD.Product, RDFS.comment, Literal("Appliance product family")))

g.add((WD.Symptom, RDF.type, OWL.Class))
g.add((WD.FailureMode, RDF.type, OWL.Class))
g.add((WD.Part, RDF.type, OWL.Class))"""

    code_props = """# ObjectProperty = edge between two resources (URI → URI)
g.add((WD.indicates, RDF.type, OWL.ObjectProperty))
g.add((WD.indicates, RDFS.domain, WD.Symptom))
g.add((WD.indicates, RDFS.range, WD.FailureMode))
g.add((WD.indicates, RDFS.label, Literal("indicates")))

# DatatypeProperty = attribute with a literal
g.add((WD.confidence, RDF.type, OWL.DatatypeProperty))
g.add((WD.confidence, RDFS.domain, WD.indicates))  # often on reified axiom
g.add((WD.confidence, RDFS.range, XSD.decimal))"""

    code_abox = """# ABox: individuals under TBox classes
wm = WD["product_wm_001"]
g.add((wm, RDF.type, WD.Product))
g.add((wm, RDFS.label, Literal("Front Load Washer 8kg")))

s = WD["sym_wm_s01"]
g.add((s, RDF.type, WD.Symptom))
g.add((s, RDFS.label, Literal("Will not drain")))

fm = WD["fm_wm_fm01"]
g.add((fm, RDF.type, WD.FailureMode))
g.add((s, WD.indicates, fm))  # plain triple
# confidence often stored via owl:Axiom reification in richer models"""

    ttl = """@prefix wd:   <https://example.org/warranty-diagnosis#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

wd:Product a owl:Class ;
    rdfs:label "Product" .

wd:Symptom a owl:Class .
wd:FailureMode a owl:Class .

wd:indicates a owl:ObjectProperty ;
    rdfs:domain wd:Symptom ;
    rdfs:range wd:FailureMode .

wd:product_wm_001 a wd:Product ;
    rdfs:label "Front Load Washer 8kg" .

wd:sym_wm_s01 a wd:Symptom ;
    wd:indicates wd:fm_wm_fm01 ."""

    return StudyModule(
        id="01-rdf-owl-tbox-abox",
        title="RDF / OWL — TBox then ABox",
        description="Build a warranty ontology: classes, properties, individuals, Turtle serialization.",
        tags=["rdf", "owl", "tbox", "abox", "turtle", "rdflib"],
        story=(
            "Imagine a warehouse with one rule book on the wall (TBox): shelves may only be labeled "
            "Product, Symptom, FailureMode, Part. Trucks deliver boxes of facts about specific machines "
            "(ABox). You never print a new rule book for each SKU — you shelve new boxes under existing labels. "
            "RDF is the triple language for both; OWL adds logical rules."
        ),
        one_liner="TBox = rule book (classes/properties); ABox = shelves (instances); RDF triples for both.",
        change_table=[
            {"from": "Ad-hoc JSON", "to": "Typed triples", "why": "Interchange + formal meaning"},
            {"from": "Per-product schema", "to": "Shared TBox", "why": "Scale to thousands of SKUs"},
            {"from": "Only Neo4j", "to": "OWL export + Neo4j runtime", "why": "Audit + operational speed"},
        ],
        beats=[
            CodeBeat(
                id="tbox-classes",
                title="TBox Part A — Classes with rdflib",
                language="python",
                narrative="Three triples per class: type, label, comment. This is the pattern — memorize it.",
                code=code_classes,
                annotations=_ann(
                    [
                        (1, "rdflib Graph is an in-memory triple store."),
                        (3, "Namespace keeps IRIs short and consistent (wd:Product)."),
                        (4, "Empty Graph(); bind prefixes for readable Turtle later."),
                        (9, "OWL.Class declares a TBox class — not an instance."),
                        (10, "Human label for UI / tooling."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            9,
                            "What does this triple assert?",
                            "WD.Product is an OWL Class",
                            [
                                "WD.Product is an instance of a washing machine",
                                "Deletes the Product class",
                                "Opens a Neo4j session",
                            ],
                        ),
                        (1, "Which library provides Graph/Namespace?", "rdflib", ["neo4j", "langchain", "fastapi"]),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template='g.add((WD.Product, RDF.type, {{c1}}))\ng.add((WD.Product, RDFS.label, {{c2}}("Product")))',
                    blanks=[
                        BlankSpec(id="c1", answer="OWL.Class", hint="OWL class type"),
                        BlankSpec(id="c2", answer="Literal", hint="rdflib literal wrapper"),
                    ],
                ),
            ),
            CodeBeat(
                id="tbox-props",
                title="TBox Part B — Object & Datatype properties",
                language="python",
                narrative="ObjectProperty = edge between resources. DatatypeProperty = literal attributes.",
                code=code_props,
                annotations=_ann(
                    [
                        (2, "ObjectProperty: both ends are resources (URIs)."),
                        (3, "domain = allowed subject class."),
                        (4, "range = allowed object class."),
                        (8, "DatatypeProperty points to XSD literals (numbers, strings)."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            2,
                            "indicates is which kind of property?",
                            "OWL.ObjectProperty",
                            ["OWL.DatatypeProperty", "OWL.Class", "RDF.Bag"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="g.add((WD.indicates, RDF.type, {{p1}}))\ng.add((WD.indicates, RDFS.domain, {{p2}}))\ng.add((WD.indicates, RDFS.range, {{p3}}))",
                    blanks=[
                        BlankSpec(id="p1", answer="OWL.ObjectProperty"),
                        BlankSpec(id="p2", answer="WD.Symptom"),
                        BlankSpec(id="p3", answer="WD.FailureMode"),
                    ],
                ),
            ),
            CodeBeat(
                id="abox-instances",
                title="ABox — individuals and INDICATES",
                language="python",
                narrative="Same Graph API; RDF.type points at your TBox class, not owl:Class.",
                code=code_abox,
                annotations=_ann(
                    [
                        (2, "Individual IRI under the product namespace."),
                        (3, "Type is WD.Product — ABox fact under TBox class."),
                        (12, "Predicate WD.indicates is the TBox ObjectProperty."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            3,
                            "Is this TBox or ABox?",
                            "ABox individual typed as Product",
                            ["TBox class definition", "SPARQL query", "Cypher MERGE"],
                        ),
                    ]
                ),
            ),
            CodeBeat(
                id="turtle-read",
                title="Turtle serialization — read what you built",
                language="turtle",
                narrative="If you can hand-write this Turtle from memory, you understand TBox+ABox.",
                code=ttl,
                annotations=_ann(
                    [
                        (1, "Prefix maps short names to IRIs."),
                        (5, "a owl:Class is Turtle sugar for rdf:type."),
                        (14, "ABox individual with indicates edge."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            5,
                            "What does `a owl:Class` mean?",
                            "rdf:type owl:Class",
                            ["Creates a Neo4j node", "Deletes a class", "Runs SPARQL"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="wd:indicates a owl:{{t1}} ;\n    rdfs:domain wd:{{t2}} ;\n    rdfs:range wd:{{t3}} .",
                    blanks=[
                        BlankSpec(id="t1", answer="ObjectProperty"),
                        BlankSpec(id="t2", answer="Symptom"),
                        BlankSpec(id="t3", answer="FailureMode"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="RDF triple", definition="subject–predicate–object statement", analogy="One edge fact"),
            ConceptCard(term="TBox", definition="Terminological box: classes & properties", analogy="CREATE TABLE"),
            ConceptCard(term="ABox", definition="Assertional box: individuals & facts", analogy="INSERT rows"),
            ConceptCard(
                term="OWL", definition="Ontology language on Description Logic", analogy="Schema + logic rules"
            ),
        ],
        self_quiz=[
            QuizItem(
                q="Why not create a new OWL file per product SKU?",
                a="New product is ABox under shared TBox; per-SKU schema does not scale.",
            ),
            QuizItem(
                q="ObjectProperty vs DatatypeProperty?", a="Object links resources; Datatype links to literals (XSD)."
            ),
            QuizItem(
                q="Where does runtime diagnosis usually run?",
                a="Neo4j property graph (operational ABox); RDF/OWL for formal interchange.",
            ),
        ],
        common_mistakes=[
            "Typing an instance as owl:Class instead of your domain class.",
            "Inventing property names not in the TBox.",
            "Thinking Turtle file is what the chat queries at runtime.",
        ],
        final_boss=[
            "From blank page: create Product, Symptom, FailureMode, indicates in rdflib.",
            "Write equivalent Turtle by hand.",
            "Explain TBox vs ABox with the warehouse story in 45 seconds.",
        ],
        source="seed",
        order=10,
        estimated_minutes=40,
    )


def module_sparql_cypher() -> StudyModule:
    sparql = """PREFIX wd: <https://example.org/warranty-diagnosis#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?symLabel ?fmLabel WHERE {
  ?sym a wd:Symptom ;
       rdfs:label ?symLabel ;
       wd:indicates ?fm .
  ?fm rdfs:label ?fmLabel .
}
ORDER BY ?symLabel"""

    cypher_create = """// Create path (parameterize ids in real apps)
MERGE (p:Product {product_id: $product_id})
  ON CREATE SET p.name = $name
MERGE (s:Symptom {symptom_id: $symptom_id})
  ON CREATE SET s.description = $description
MERGE (fm:FailureMode {failure_mode_id: $fm_id})
  ON CREATE SET fm.name = $fm_name
MERGE (p)-[:HAS_SYMPTOM]->(s)
MERGE (s)-[:INDICATES {confidence: $confidence}]->(fm)
RETURN p, s, fm"""

    cypher_read = """MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
WHERE s.symptom_id IN $symptom_ids
WITH fm, collect({symptom_id: s.symptom_id, confidence: ind.confidence}) AS indications,
     sum(coalesce(ind.confidence, 0)) AS total_confidence
RETURN fm.failure_mode_id AS failure_mode_id,
       fm.name AS name,
       indications,
       total_confidence
ORDER BY total_confidence DESC"""

    shortest = """// Shortest diagnostic path: symptom → FM → step → part
MATCH (s:Symptom {symptom_id: $sid})-[:INDICATES]->(fm:FailureMode)
MATCH path = shortestPath(
  (fm)-[:CONFIRMS|REQUIRES_PART*1..4]-(part:Part)
)
RETURN path
LIMIT 5"""

    return StudyModule(
        id="02-sparql-and-cypher",
        title="SPARQL + Cypher — query & create graphs",
        description="Query RDF with SPARQL; create/read Neo4j with parameterized Cypher; shortestPath for retrieval.",
        tags=["sparql", "cypher", "neo4j", "shortest-path", "retrieval"],
        story=(
            "SPARQL is SQL-for-triples on RDF. Cypher is pattern-matching on property graphs. "
            "Same diagnosis idea: find Symptom → FailureMode → Part. In production we parameterize "
            "every id ($product_id) so plans cache and injection fails closed."
        ),
        one_liner="SPARQL for RDF; Cypher for Neo4j; always parameterize; prefer typed short paths over full scans.",
        beats=[
            CodeBeat(
                id="sparql-indicates",
                title="SPARQL — symptoms indicating failure modes",
                language="sparql",
                narrative="Graph pattern in WHERE mirrors the triples you asserted.",
                code=sparql,
                annotations=_ann(
                    [
                        (1, "PREFIX shortens IRIs."),
                        (4, "SELECT projects variables."),
                        (6, "Triple patterns share variables to join."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            8,
                            "What does wd:indicates connect?",
                            "Symptom to FailureMode",
                            ["Product to Part only", "Two literals", "Nothing"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="?sym a wd:{{x1}} ;\n     wd:indicates ?fm .",
                    blanks=[BlankSpec(id="x1", answer="Symptom")],
                ),
            ),
            CodeBeat(
                id="cypher-merge",
                title="Cypher CREATE/MERGE path",
                language="cypher",
                narrative="MERGE is upsert. Properties on INDICATES store likelihood.",
                code=cypher_create,
                annotations=_ann(
                    [
                        (2, "MERGE Product by business key product_id."),
                        (11, "Relationship property confidence = P(s|fm)-style weight."),
                        (1, "$params — never f-string user text into Cypher."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            2,
                            "Why MERGE not bare CREATE?",
                            "Idempotent upsert by key",
                            ["Always faster than MATCH", "Deletes old nodes", "Only for RDF"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="MERGE (s)-[:{{r1}} {{confidence: $confidence}}]->(fm)",
                    blanks=[BlankSpec(id="r1", answer="INDICATES")],
                ),
            ),
            CodeBeat(
                id="cypher-rank",
                title="Cypher retrieval for ranking (GraphRAG style)",
                language="cypher",
                narrative="Product-scoped candidates only — never global symptom scan first.",
                code=cypher_read,
                annotations=_ann(
                    [
                        (1, "Start at Product — partitions the search space."),
                        (3, "Filter observed symptoms with IN $symptom_ids."),
                        (8, "ORDER BY total_confidence — pre-rank before Bayes in Python."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            1,
                            "Why bind product_id first?",
                            "Scope search; accuracy + speed",
                            ["Neo4j requires it always", "Disables indexes", "Only for SPARQL"],
                        ),
                    ]
                ),
            ),
            CodeBeat(
                id="shortest-path",
                title="shortestPath for compact diagnostic trails",
                language="cypher",
                narrative="Bounded variable-length paths keep retrieval fast and explainable.",
                code=shortest,
                annotations=_ann(
                    [
                        (3, "shortestPath finds minimal hop trail."),
                        (4, "Relationship type union + max depth 4 bounds cost."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            3,
                            "What does shortestPath optimize?",
                            "Fewest hops between nodes",
                            ["Cheapest part cost only", "Highest Bayes posterior", "Longest trail"],
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="SPARQL", definition="Query language for RDF graphs"),
            ConceptCard(term="Cypher", definition="Neo4j pattern query language"),
            ConceptCard(term="Parameterization", definition="Pass $vars — plan cache + safety"),
            ConceptCard(term="shortestPath", definition="Minimal hop path in property graph"),
        ],
        self_quiz=[
            QuizItem(q="SQL SELECT equivalent in SPARQL?", a="SELECT variables; WHERE holds graph patterns."),
            QuizItem(q="Why avoid f-string Cypher?", a="Injection risk + plan never caches."),
            QuizItem(
                q="Fast accurate retrieval pattern?",
                a="Product scope → typed edges → rank → optional shortestPath explain.",
            ),
        ],
        common_mistakes=[
            "Global MATCH (s:Symptom) without product filter on large graphs.",
            "Unbounded [*]-paths exploding the DB.",
            "Putting ranking math in Cypher when Python Bayes is clearer/testable.",
        ],
        final_boss=[
            "Write MERGE for Product-Symptom-INDICATES-FailureMode with $params.",
            "Write SPARQL that returns symptom labels for a failure mode.",
            "Explain shortestPath bounds for production safety.",
        ],
        source="seed",
        order=20,
        estimated_minutes=35,
    )


def module_langgraph_cypher_agent() -> StudyModule:
    code = '''from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# In THIS repo's production app we use FIXED Cypher + Bayes.
# This tutorial beat teaches the "smart Cypher" pattern for interviews:
# outer LLM decides tools; inner LLM (or mock) writes Cypher; tool runs it safely.

class DiagnosticQueryInput(BaseModel):
    user_input: str = Field(..., description="Symptom or error description")

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]

@tool(args_schema=DiagnosticQueryInput)
def query_graph(user_input: str) -> str:
    """Generate Cypher from schema + user text, then run it."""
    # --- second "brain": Cypher writer (LLM or mock) ---
    schema = "Nodes: Product,Symptom,FailureMode,Part Rels: HAS_SYMPTOM,INDICATES,REQUIRES_PART"
    cypher = mock_or_llm_cypher(schema, user_input)  # must list labels so model doesn't invent
    cypher = cypher.strip().removeprefix("```cypher").removesuffix("```").strip()
    try:
        rows = neo4j_graph.query(cypher)  # or session.run
        return str(rows) if rows else "No results found."
    except Exception as e:
        return f"Error running query: {e} | cypher={cypher}"

tools = [query_graph]

def diagnostic_agent_node(state: AgentState):
    # --- first brain: tool-calling agent ---
    llm = chat_model.bind_tools(tools)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("agent", diagnostic_agent_node)
    g.add_node("tools", tool_node)
    g.set_entry_point("agent")
    def should_continue(state):
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END
    g.add_conditional_edges("agent", should_continue)
    g.add_edge("tools", "agent")
    return g.compile()'''

    prod = """# WarrantyGraph production skeleton (deterministic) — agents/diagnosis_graph.py
from langgraph.graph import StateGraph, END

class AgentState(TypedDict, total=False):
    user_message: str
    product_id: str | None
    diagnosis: dict | None
    response: str
    escalated: bool

def build_diagnosis_graph():
    graph = StateGraph(AgentState)
    graph.add_node("detect_product", node_detect_product)
    graph.add_node("run_diagnosis", node_run_graph_diagnosis)  # tool_diagnose → fixed Cypher + Bayes
    graph.add_node("format_response", node_format_response)
    graph.add_node("handle_escalation", node_handle_escalation)
    graph.set_entry_point("detect_product")
    graph.add_edge("detect_product", "run_diagnosis")
    graph.add_edge("run_diagnosis", "format_response")
    graph.add_edge("format_response", "handle_escalation")
    graph.add_edge("handle_escalation", END)
    return graph.compile()"""

    return StudyModule(
        id="03-langgraph-cypher-agent",
        title="LangGraph agents — tools, Cypher generation, vs deterministic GraphRAG",
        description="Interview-ready smart-Cypher tool pattern AND this repo's fixed-node production agent.",
        tags=["langgraph", "tools", "cypher", "agent", "llm"],
        story=(
            "Version A: one worker with fixed Cypher. Version B: a second assistant at the door writes "
            "Cypher on the spot; the worker only runs it inside try/except. Version C (this product): "
            "the conveyor belt is fixed (detect→diagnose→format→escalate) and diagnosis guts are "
            "parameterized Cypher + Bayes — high determinism for warranty audit."
        ),
        one_liner="Two LLM jobs (route vs write query) OR zero LLM on core path — know both for interviews.",
        change_table=[
            {"version": "Smart Cypher", "domain_logic": "LLM prompt + schema", "determinism": "Medium"},
            {"version": "WarrantyGraph", "domain_logic": "Fixed Cypher + reliability.py", "determinism": "High"},
            {"version": "Stable shell", "domain_logic": "StateGraph nodes/edges", "determinism": "Skeleton unchanged"},
        ],
        beats=[
            CodeBeat(
                id="smart-tool",
                title="Smart tool — generate then run Cypher",
                language="python",
                narrative="Memorize: schema in prompt, strip fences, try/except, return error string not crash.",
                code=code,
                annotations=_ann(
                    [
                        (8, "Interview pattern note — production repo differs on purpose."),
                        (18, "Tool input schema for structured args."),
                        (24, "Schema list prevents invented labels."),
                        (26, "Strip markdown fences LLMs love to add."),
                        (27, "try/except — generated Cypher is untrusted."),
                        (36, "First brain: bind_tools decides whether to call query_graph."),
                        (45, "Conditional edge: tool_calls → tools else END."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            27,
                            "Why try/except around query?",
                            "Generated Cypher may be invalid",
                            ["Neo4j always succeeds", "Python forbids bare calls", "Only for SPARQL"],
                        ),
                        (
                            36,
                            "What does bind_tools do?",
                            "Lets the model emit tool calls",
                            ["Writes Cypher itself inside Neo4j", "Starts Redis", "Creates TBox"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template='@tool(args_schema={{a1}})\ndef query_graph(user_input: str) -> str:\n    try:\n        rows = neo4j_graph.{{a2}}(cypher)\n    except Exception as e:\n        return f"Error: {{e}}"',
                    blanks=[
                        BlankSpec(id="a1", answer="DiagnosticQueryInput"),
                        BlankSpec(id="a2", answer="query"),
                    ],
                ),
            ),
            CodeBeat(
                id="prod-graph",
                title="Production deterministic LangGraph",
                language="python",
                narrative="Same LangGraph skill, different trade-off: fixed edges, tool_diagnose uses GraphRAG.",
                code=prod,
                annotations=_ann(
                    [
                        (7, "Explicit state fields — not only messages."),
                        (12, "run_diagnosis calls GraphRAG tools with fixed Cypher."),
                        (16, "Linear pipeline — no ReAct loop required."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            12,
                            "Where does ranking live?",
                            "graph_rag + reliability (not LLM Cypher)",
                            ["Inside Neo4j only", "Random choice", "CSS styles"],
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="ToolNode", definition="Executes tool calls emitted by the model"),
            ConceptCard(term="bind_tools", definition="Attaches tool schemas to the chat model"),
            ConceptCard(term="Two-LLM pattern", definition="Router LLM + Cypher-writer LLM"),
            ConceptCard(term="Deterministic GraphRAG", definition="Fixed queries + probabilistic ranking"),
        ],
        self_quiz=[
            QuizItem(
                q="Name the two LLM jobs in smart Cypher agents.", a="(1) Decide to call tool (2) Write Cypher text."
            ),
            QuizItem(q="What stays stable across agent versions?", a="State → nodes → edges → compile skeleton."),
            QuizItem(
                q="Why does WarrantyGraph avoid LLM Cypher on the diagnose path?",
                a="Auditability, determinism, no invented labels.",
            ),
        ],
        common_mistakes=[
            "Forgetting schema labels in the Cypher prompt.",
            "No try/except around graph.query.",
            "Confusing this product with the smart-Cypher tutorial.",
            "Name collision: `graph` as Neo4jGraph and compiled LangGraph.",
        ],
        final_boss=[
            "Whiteboard both agent topologies in 2 minutes.",
            "Write query_graph tool from memory with try/except + strip.",
            "Write build_diagnosis_graph four nodes from memory.",
        ],
        source="seed",
        order=30,
        estimated_minutes=45,
    )


def module_runtime_scale() -> StudyModule:
    code = """from functools import lru_cache
from runtime.cache import get_named_cache
from runtime.partitioning import partition_key
import concurrent.futures

# Tier 1 — application cache (memory or Redis)
cache = get_named_cache("diagnose", ttl_seconds=90)

def cached_diagnose(product_id: str, symptom_key: str, compute):
    key = f"diag:{product_id}:{symptom_key}"  # include all inputs that change the answer
    hit = cache.get(key)
    if hit is not None:
        return hit
    value = compute()
    cache.set(key, value)
    return value

# Tier 2 — parameterized Cypher so Neo4j caches query plans
GOOD = "MATCH (p:Product {product_id: $id}) RETURN p"
# BAD  = f"MATCH (p:Product {{product_id: '{id}'}}) RETURN p"

# Concurrency — bound worker pool for I/O fan-out (connectors)
def fetch_sources_parallel(fns: list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(lambda f: f(), fns))

# Partitioning — logical keys today; physical shards later
def rate_limit_key(tenant: str, client: str, route: str) -> str:
    return partition_key(tenant, client, route)  # e.g. tenant|client|route

# Invalidation — after promote/ETL
def on_graph_loaded():
    cache.clear()  # or invalidate_all_named_caches()"""

    return StudyModule(
        id="04-cache-threads-partition",
        title="Caching, multi-threading, partitioning",
        description="Three-tier cache thinking, thread pools for I/O, logical partitions, invalidation.",
        tags=["cache", "redis", "threading", "partitioning", "performance"],
        story=(
            "One cashier: a notepad of recent answers is enough. Ten cashiers: they need a shared whiteboard "
            "(Redis) or they contradict each other. Writes still go through a careful manager (primary Neo4j); "
            "reads can scale out. Threads help when waiting on many connectors — not when holding the GIL on pure CPU."
        ),
        one_liner="Cache hot diagnose keys; parameterize Cypher; bound thread pools; partition by tenant|product.",
        beats=[
            CodeBeat(
                id="runtime-patterns",
                title="Cache + threads + partitions (patterns)",
                language="python",
                narrative="Memorize key composition, TTL, invalidation after promote.",
                code=code,
                annotations=_ann(
                    [
                        (6, "Named cache with TTL — memory or Redis backend."),
                        (9, "Key must include every input that changes the result."),
                        (18, "Parameterized Cypher = plan reuse + safety."),
                        (23, "ThreadPool for I/O-bound connector fan-out."),
                        (29, "Logical partition key for multi-tenant limits."),
                        (33, "Invalidate on graph load or users see stale truth."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            9,
                            "What belongs in a diagnose cache key?",
                            "product_id + symptoms (+ tenant)",
                            ["Only the wall clock time", "Random UUID always", "Just the word diagnose"],
                        ),
                        (
                            33,
                            "When clear cache?",
                            "After ETL/promote graph load",
                            ["Never", "Only on Fridays", "Before every Cypher keyword"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template='key = f"diag:{{k1}}:{{k2}}"\nhit = cache.{{k3}}(key)',
                    blanks=[
                        BlankSpec(id="k1", answer="{product_id}"),
                        BlankSpec(id="k2", answer="{symptom_key}"),
                        BlankSpec(id="k3", answer="get"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="TTL cache", definition="Entries expire after seconds — freshness vs speed"),
            ConceptCard(term="Redis shared state", definition="Multi-pod cache/rate/admission"),
            ConceptCard(term="Logical partition", definition="Key design before physical shards"),
            ConceptCard(term="CAP for diagnosis", definition="Prefer consistency of knowledge over availability"),
        ],
        self_quiz=[
            QuizItem(
                q="Is Redis required for a single-node demo?", a="No — memory backends work; Redis for multi-replica."
            ),
            QuizItem(q="Why not unbounded threads?", a="Connection storms and tail latency; bound max_workers."),
            QuizItem(
                q="Product-based sharding idea?", a="Partition graph data by product line when scale forces Fabric."
            ),
        ],
        common_mistakes=[
            "Caching without invalidation after promote.",
            "String-built Cypher killing the plan cache.",
            "Claiming Fabric/replicas are as-built when only logical keys exist.",
        ],
        final_boss=[
            "Design diagnose cache keys for multi-tenant API.",
            "Explain memory vs Redis for rate limits.",
            "Draw CAP choice for warranty knowledge updates.",
        ],
        source="seed",
        order=40,
        estimated_minutes=30,
    )


def module_retrieval_accuracy() -> StudyModule:
    code = """# Accurate retrieval pipeline (as-built GraphRAG idea)
def diagnose_pipeline(message: str, product_id: str | None):
    product = resolve_product(message, product_id)          # 1 scope
    symptoms = hybrid_match(message, product.symptom_ids) # 2 lexical + TF-IDF
    ranked = cypher_indicates(product.id, symptoms)       # 3 typed graph
    posteriors = bayesian_posteriors(priors, likelihoods, symptoms, fm_ids)
    if max(posteriors.values(), default=0) < THRESHOLD:
        return escalate("insufficient evidence")          # 4 accuracy gate
    steps = confirms_steps(top_fm)
    parts = requires_parts(top_fm)
    return rank_and_format(posteriors, steps, parts)

def bayesian_posteriors(priors, likelihoods, observed, candidates, miss=0.05):
    # posterior ∝ prior(fm) * Π P(s|fm); missing edge → miss likelihood
    scores = {}
    for fm in candidates:
        score = max(priors.get(fm, 0.0), 0.0)
        for s in observed:
            score *= likelihoods.get((s, fm), miss)
        scores[fm] = score
    total = sum(scores.values()) or 1.0
    return {fm: v / total for fm, v in scores.items()}"""

    return StudyModule(
        id="05-fast-accurate-retrieval",
        title="Fast & accurate retrieval — hybrid match, Bayes, gates",
        description="Product-scoped hybrid retrieval, INDICATES likelihoods, naive Bayes, escalate when sparse.",
        tags=["graphrag", "bayes", "retrieval", "accuracy", "fmea"],
        story=(
            "Speed without scope is a full-graph scan. Accuracy without gates is a confident wrong answer. "
            "We pin the product, match language softly, walk typed edges, multiply likelihoods, and escalate "
            "when the posterior is mush."
        ),
        one_liner="Scope → hybrid match → typed Cypher → Bayes → escalate if weak.",
        beats=[
            CodeBeat(
                id="retrieval-bayes",
                title="Retrieval + Bayes ranking",
                language="python",
                narrative="miss_likelihood is the sparse-data soft landing — not inventing edges with KGE.",
                code=code,
                annotations=_ann(
                    [
                        (3, "Resolve product first — partitions search."),
                        (4, "Hybrid lexical/TF-IDF for customer language."),
                        (6, "Naive Bayes over INDICATES confidences."),
                        (7, "Accuracy gate — refuse overconfident garbage."),
                        (14, "Missing edge uses miss likelihood instead of zeroing wrongly."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            7,
                            "Why escalate on low posterior?",
                            "Protect accuracy when evidence is thin",
                            ["To crash the API", "Redis requires it", "Cypher forbids high scores"],
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="score *= likelihoods.get((s, fm), {{m1}})\n# normalize so posteriors sum to 1",
                    blanks=[BlankSpec(id="m1", answer="miss")],
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="Hybrid match", definition="Lexical + TF-IDF (vectors optional later)"),
            ConceptCard(term="Naive Bayes", definition="Posterior ∝ prior × ∏ likelihoods"),
            ConceptCard(term="Miss likelihood", definition="Default P(s|fm) when edge absent"),
        ],
        self_quiz=[
            QuizItem(q="Where does P(s|fm) come from?", a="INDICATES.confidence on the graph edge."),
            QuizItem(
                q="KGE vs our sparse strategy?",
                a="We soft-score + escalate + grow ABox; no silent edge invention in v1.",
            ),
        ],
        common_mistakes=[
            "Ranking globally without product scope.",
            "Treating RPN as a probability.",
            "Skipping insufficient-data escalation.",
        ],
        final_boss=[
            "Write bayesian_posteriors from memory.",
            "Trace 'washer won't drain E21' through the pipeline aloud.",
        ],
        source="seed",
        order=50,
        estimated_minutes=30,
    )


def module_shacl() -> StudyModule:
    code = """# SHACL-style closed-world checks (lite) — ontology_validate.py idea
ALLOWED_LIST_KEYS = {
    "symptoms": "Symptom",
    "failure_modes": "FailureMode",
    "diagnostic_steps": "DiagnosticStep",
    "parts": "Part",
}

MIN_SYMPTOMS = 1
MIN_FAILURE_MODES = 1
MIN_INDICATES_LINKS = 1

def validate_product_bundle(bundle: dict) -> dict:
    errors = []
    for key, class_name in ALLOWED_LIST_KEYS.items():
        if key in bundle and not isinstance(bundle[key], list):
            errors.append(f"{key} must be a list of {class_name} instances")
    if len(bundle.get("symptoms") or []) < MIN_SYMPTOMS:
        errors.append("need ≥1 symptom")
    if len(bundle.get("symptom_failure_links") or []) < MIN_INDICATES_LINKS:
        errors.append("need ≥1 INDICATES link")
    # LINK_SPECS: foreign-key style — every link id must exist in pools
    return {"ok": not errors, "errors": errors}

# Full W3C SHACL (target) uses pyshacl.validate(data_graph, shacl_graph=shapes)
# OWL reasoners (HermiT) are open-world inference — different job than shapes."""

    shapes_ttl = """@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix wd:   <https://example.org/warranty-diagnosis#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

wd:ProductShape a sh:NodeShape ;
  sh:targetClass wd:Product ;
  sh:property [
    sh:path wd:productId ;
    sh:minCount 1 ;
    sh:datatype xsd:string ;
  ] ."""

    return StudyModule(
        id="06-shacl-and-quality-gates",
        title="SHACL & quality gates — validate ABox before promote",
        description="Closed-world shapes vs OWL open-world; lite validator as-built; SHACL Turtle target.",
        tags=["shacl", "validation", "tbox", "quality"],
        story=(
            "OWL tells you what could be true in an open world. SHACL is the clipboard at the loading dock: "
            "before boxes enter production, every required label and link must be present. Our app uses a "
            "Python SHACL-inspired validator; full pyshacl is the enterprise upgrade."
        ),
        one_liner="Shapes fail-closed before promote; reasoners are optional offline enrichment.",
        beats=[
            CodeBeat(
                id="shapes-lite",
                title="Lite shapes in Python",
                language="python",
                narrative="Memorize min evidence: symptoms, FMs, INDICATES links.",
                code=code,
                annotations=_ann(
                    [
                        (2, "Catalog list keys map to TBox classes."),
                        (10, "Minimum evidence keeps junk products out of GraphRAG."),
                        (15, "Bundle validation returns structured errors for Admin UI."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            12,
                            "Why MIN_INDICATES_LINKS?",
                            "Need evidence edges for diagnosis",
                            ["Neo4j license requires it", "CSS styling", "Redis key length"],
                        ),
                    ]
                ),
            ),
            CodeBeat(
                id="shacl-ttl",
                title="SHACL NodeShape (target form)",
                language="turtle",
                narrative="Know the vocabulary even if runtime is Python lite.",
                code=shapes_ttl,
                annotations=_ann(
                    [
                        (5, "NodeShape targets a class."),
                        (7, "property constraints on a path."),
                        (8, "minCount enforces required fields."),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="wd:ProductShape a sh:{{s1}} ;\n  sh:targetClass wd:{{s2}} .",
                    blanks=[
                        BlankSpec(id="s1", answer="NodeShape"),
                        BlankSpec(id="s2", answer="Product"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="SHACL", definition="Shapes Constraint Language — closed-world data quality"),
            ConceptCard(term="Open world", definition="OWL: missing fact ≠ false"),
            ConceptCard(term="Fail-closed promote", definition="Invalid ABox never reaches production chat"),
        ],
        self_quiz=[
            QuizItem(q="OWL vs SHACL one-liner?", a="OWL meaning/inference; SHACL instance quality checks."),
            QuizItem(q="When do we validate?", a="Before materialize/promote — not only after Neo4j load."),
        ],
        common_mistakes=[
            "Validating only after production load.",
            "Calling lite shapes a full HermiT reasoner.",
        ],
        final_boss=[
            "Write validate_product_bundle checks from memory.",
            "Sketch a SHACL NodeShape for Symptom with minCount 1 on description.",
        ],
        source="seed",
        order=60,
        estimated_minutes=25,
    )


def module_master_lineage() -> StudyModule:
    return StudyModule(
        id="07-master-platform-lineage",
        title="Platform lineage — warehouse story end-to-end",
        description="Glue module: dual graph, multi-source ABox, GraphRAG, LLMOps defaults.",
        tags=["platform", "tbox", "pipeline", "interview"],
        story=(
            "Sources arrive → OntologyBuilder restickers to shared TBox language → shapes clipboard → "
            "staging back room → smoke test → production floor. Shoppers (chat) never enter staging. "
            "Specialist walks INDICATES, multiplies likelihoods, returns parts with a paper trail. "
            "LLM is optional translator at the door — accountant still does the math."
        ),
        one_liner="Shared TBox; multi-source ABox; shape-check; stage→prod; deterministic GraphRAG+Bayes.",
        beats=[
            CodeBeat(
                id="wizard-chant",
                title="Operator chant (memorize order)",
                language="text",
                narrative="If you can recite this, you understand the control plane.",
                code=(
                    "Sources → Fetch → Select → Validate ABox → Materialize → Smoke → Approve\n"
                    "→ Promote staging (:7688) → Promote production (:7687)\n"
                    "→ Chat / GraphRAG reads production only\n"
                    "→ invalidate caches"
                ),
                annotations=_ann(
                    [
                        (1, "Selection-scoped work — don't rewrite whole fleet."),
                        (2, "Dual graph blast-radius control."),
                        (3, "Read path isolation."),
                    ]
                ),
                line_quiz=_lq(
                    [
                        (
                            2,
                            "Which port does chat use?",
                            "Production 7687",
                            ["Staging 7688 only", "Redis 6379", "Frontend 3000"],
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(term="Dual graph", definition="Staging write-first; production diagnose-read"),
            ConceptCard(term="OntologyBuilder", definition="Maps SoR payloads into catalog ABox"),
            ConceptCard(term="LLMOps ready", definition="Guardrails/evals active; LLM gateway inactive by default"),
        ],
        self_quiz=[
            QuizItem(q="New product = ?", a="New ABox under shared TBox."),
            QuizItem(q="llm_enabled default?", a="false — GraphRAG primary."),
        ],
        common_mistakes=[
            "Saying chat reads staging.",
            "Calling sources 'the ontology'.",
        ],
        final_boss=[
            "90-second warehouse pitch.",
            "Draw dual graph + wizard steps from blank page.",
        ],
        source="seed",
        order=5,
        estimated_minutes=20,
    )


def all_seed_modules() -> list[StudyModule]:
    return [
        module_master_lineage(),
        module_rdf_owl(),
        module_sparql_cypher(),
        module_langgraph_cypher_agent(),
        module_runtime_scale(),
        module_retrieval_accuracy(),
        module_shacl(),
    ]


def write_all_seeds() -> list[str]:
    ids = []
    for m in all_seed_modules():
        save_module(m)
        ids.append(m.id)
    # Also seed from notebook if present
    try:
        from pathlib import Path

        from study.generator import generate_from_bytes

        nb = Path(__file__).resolve().parent.parent / "notebooks" / "rdf_owl_langgraph_tutorial.ipynb"
        if nb.exists():
            mod = generate_from_bytes(
                nb.name,
                nb.read_bytes(),
                title="Notebook: RDF/OWL + LangGraph tutorial (auto)",
                tags=["notebook", "rdf", "langgraph"],
            )
            mod.id = "08-notebook-auto"
            mod.order = 15
            save_module(mod)
            ids.append(mod.id)
    except Exception:
        pass
    return ids


if __name__ == "__main__":
    print("Wrote seeds:", write_all_seeds())
