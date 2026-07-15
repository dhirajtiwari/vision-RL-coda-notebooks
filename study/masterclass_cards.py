"""Line-by-line + concept flashcards for the two Masterclasses.

Every meaningful line of code and every concept becomes a MemoryCard you can:
  * READ (front -> reveal code + explanation + mental model + memory hook),
  * FILL-IN-THE-BLANK (blank/answers),
  * WRITE FROM MEMORY (front -> type the code -> self-check against `code`).

Sections group cards by Beat so you can also "write the whole section" from memory.
"""

from __future__ import annotations

from study.models import MemoryCard

_TURTLE = "turtle"
_PY = "python"


class _Builder:
    """Tiny helper so we don't repeat masterclass_id/order for every card."""

    def __init__(self, masterclass_id: str) -> None:
        self.mc = masterclass_id
        self.cards: list[MemoryCard] = []

    def add(
        self,
        cid: str,
        section: str,
        front: str,
        *,
        kind: str = "line",
        code: str = "",
        language: str = "text",
        explain: str = "",
        mental_model: str = "",
        memory_hook: str = "",
        blank: str = "",
        answers: list[str] | None = None,
    ) -> None:
        self.cards.append(
            MemoryCard(
                id=f"{self.mc}::{cid}",
                masterclass_id=self.mc,
                section=section,
                order=len(self.cards),
                kind=kind,  # type: ignore[arg-type]
                front=front,
                code=code,
                language=language,  # type: ignore[arg-type]
                explain=explain,
                mental_model=mental_model,
                memory_hook=memory_hook,
                blank=blank,
                answers=answers or [],
            )
        )


# ══════════════════════════════════════════════════════════════════════════
# GUIDE 1 — RDF/OWL Ontology in Turtle
# ══════════════════════════════════════════════════════════════════════════
def _build_ontology() -> list[MemoryCard]:
    b = _Builder("mc-01-rdf-owl-ontology-turtle")

    # ---- Mental models / the story ----
    S0 = "Mental models & memory hooks"
    b.add(
        "chant",
        S0,
        "Recite the 7-beat build order of the ontology.",
        kind="concept",
        explain="Prefixes → Ontology header → Classes → Disjointness → Object properties → Restrictions → Individuals.",
        mental_model="You build the rulebook before writing a single real fact about a real car.",
        memory_hook='"Dictionary, title, nouns, no-overlap law, verbs, minimum-requirement laws, then real facts."',
    )
    b.add(
        "tbox-abox",
        S0,
        "What is the TBox vs the ABox here?",
        kind="concept",
        explain="TBox = the schema (classes, properties, axioms). ABox = the real instance facts (Beat 7).",
        mental_model="TBox is the rulebook on the wall; ABox is the boxes of facts on the shelves.",
        memory_hook="T = Terminology (types). A = Assertions (actual things).",
    )
    b.add(
        "a-is-type",
        S0,
        "What does the Turtle keyword `a` mean?",
        kind="concept",
        code="wd:wm-001 a :Product .   # a == rdf:type",
        language=_TURTLE,
        explain="`a` is pure syntactic sugar for rdf:type.",
        mental_model="Read it as plain English: 'wm-001 IS A Product'.",
        memory_hook="`a` = 'is a'.",
    )
    b.add(
        "punctuation",
        S0,
        "What do `;`, `,`, and `.` mean in Turtle?",
        kind="concept",
        explain="`;` = same subject, new predicate. `,` = same subject+predicate, another object. `.` = statement finished.",
        mental_model="Semicolon keeps talking about the same thing; period ends the sentence.",
        memory_hook="; = 'and it also…'  |  , = 'and also this value'  |  . = 'full stop'.",
    )
    b.add(
        "domain-range",
        S0,
        "How do you read rdfs:domain and rdfs:range?",
        kind="concept",
        explain="domain = the class the property starts FROM; range = the class it points TO.",
        mental_model="An arrow: (domain) --property--> (range).",
        memory_hook="DoMain = D for 'departs'; Range = the 'receiving' end.",
    )
    b.add(
        "neo4j-gotcha",
        S0,
        "Does Neo4j enforce the OWL restrictions (Beat 6)?",
        kind="concept",
        explain="No. minCardinality only means something with an OWL reasoner / SHACL validator, or your own app-code check.",
        mental_model="The ontology is the design contract; Neo4j is just the storage engine — they don't police each other.",
        memory_hook="Paper rules ≠ database rules unless you wire the check.",
    )

    # ---- Beat 1: Prefixes ----
    S1 = "Beat 1: Prefixes"
    b.add(
        "prefix-empty",
        S1,
        "Write the line declaring OUR namespace (the empty prefix).",
        code="@prefix :     <http://example.org/car-diagnostics#> .",
        language=_TURTLE,
        explain="The empty prefix `:` is OUR namespace; :Product expands to http://example.org/car-diagnostics#Product.",
        mental_model="Home base — everything you invent lives here.",
        memory_hook="Empty colon = 'ours'.",
        blank="@prefix : <____> .",
        answers=["http://example.org/car-diagnostics#"],
    )
    b.add(
        "prefix-rdf",
        S1,
        "Write the rdf prefix line.",
        code="@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        language=_TURTLE,
        explain="The W3C RDF core vocabulary (rdf:type, rdf:Property, ...).",
        memory_hook="rdf = 1999/02/22 — the odd date that never changes.",
        blank="@prefix rdf: <http://www.w3.org/1999/02/22-____-ns#> .",
        answers=["rdf-syntax"],
    )
    b.add(
        "prefix-rdfs",
        S1,
        "Write the rdfs prefix line.",
        code="@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        language=_TURTLE,
        explain="RDF Schema vocabulary (rdfs:label, rdfs:comment, rdfs:subClassOf, domain/range).",
        memory_hook="rdfs = rdf + Schema = 2000/01/rdf-schema.",
        blank="@prefix rdfs: <http://www.w3.org/2000/01/____#> .",
        answers=["rdf-schema"],
    )
    b.add(
        "prefix-owl",
        S1,
        "Write the owl prefix line.",
        code="@prefix owl:  <http://www.w3.org/2002/07/owl#> .",
        language=_TURTLE,
        explain="The OWL vocabulary (owl:Class, owl:ObjectProperty, owl:Restriction, owl:AllDisjointClasses).",
        memory_hook="owl = 2002/07/owl.",
        blank="@prefix owl: <http://www.w3.org/2002/07/____#> .",
        answers=["owl"],
    )
    b.add(
        "prefix-xsd",
        S1,
        "Write the xsd prefix line.",
        code="@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .",
        language=_TURTLE,
        explain="XML Schema datatypes (xsd:string, xsd:nonNegativeInteger) used for typed literals.",
        memory_hook="xsd = XML Schema Datatypes = 2001/XMLSchema.",
        blank="@prefix xsd: <http://www.w3.org/2001/____#> .",
        answers=["XMLSchema"],
    )
    b.add(
        "prefix-why",
        S1,
        "Why define our own `:` prefix instead of only using rdf:/rdfs:/owl:?",
        kind="concept",
        explain="rdf/rdfs/owl/xsd are W3C's vocabularies you build ON; you invent your OWN terms under your own prefix.",
        mental_model="You speak their grammar (owl/rdfs) but your own nouns (:Product) live under your namespace.",
        memory_hook="Their words = borrowed; your words = your prefix.",
    )

    # ---- Beat 2: Ontology header ----
    S2 = "Beat 2: Ontology header"
    b.add(
        "header",
        S2,
        "Write the ontology header (declares the document itself).",
        kind="block",
        code=(
            "<http://example.org/car-diagnostics> rdf:type owl:Ontology ;\n"
            '    rdfs:label "Car Diagnostics Ontology" ;\n'
            '    rdfs:comment "Governs Product, Symptom, ErrorCode, DiagnosticStep, and Resolution facts for a car-diagnostics knowledge graph." .'
        ),
        language=_TURTLE,
        explain="Uses the FULL URI (not `:`) because it describes the ontology document itself, not a term inside it.",
        mental_model="The title page of the rulebook.",
        memory_hook="Full URI = we're talking ABOUT the book, not a word in it.",
        blank='<http://example.org/car-diagnostics> rdf:type owl:____ ;\n    rdfs:____ "Car Diagnostics Ontology" .',
        answers=["Ontology", "label"],
    )

    # ---- Beat 3: Classes ----
    S3 = "Beat 3: Classes"
    b.add(
        "class-pattern",
        S3,
        "What 3-line shape declares every class?",
        kind="pattern",
        code=':X rdf:type owl:Class ;\n    rdfs:label "..." ;\n    rdfs:comment "..." .',
        language=_TURTLE,
        explain="rdf:type owl:Class = WHAT it is; rdfs:label = short name; rdfs:comment = longer explanation.",
        mental_model="type/label/comment = identity card, nickname, bio.",
        memory_hook="Type, Label, Comment — 'TLC' for every class.",
    )
    for cid, cls, label, comment in [
        ("class-product", "Product", "Product", "A car model/product line, e.g. Toyota Camry 2022."),
        ("class-errorcode", "ErrorCode", "Error Code", "A specific, catalogued fault code, e.g. P0300."),
        (
            "class-symptom",
            "Symptom",
            "Symptom",
            "An observation reported by a customer or technician, e.g. rough idle.",
        ),
        (
            "class-step",
            "DiagnosticStep",
            "Diagnostic Step",
            "A specific check that confirms an ErrorCode is really present.",
        ),
        ("class-resolution", "Resolution", "Resolution", "The repair action that fixes a confirmed ErrorCode."),
    ]:
        b.add(
            cid,
            S3,
            f"Declare the {cls} class.",
            code=f':{cls} rdf:type owl:Class ;\n    rdfs:label "{label}" ;\n    rdfs:comment "{comment}" .',
            language=_TURTLE,
            explain=f"{cls} is one of the five allowed nouns → becomes a Neo4j node label :{cls}.",
            blank=f':{cls} rdf:type owl:____ ;\n    rdfs:label "{label}" .',
            answers=["Class"],
        )
    b.add(
        "classes-five",
        S3,
        "Name the five classes in order.",
        kind="concept",
        explain="Product, ErrorCode, Symptom, DiagnosticStep, Resolution.",
        memory_hook="P-E-S-D-R: 'Please Escalate Serious Diagnostic Reports.'",
    )

    # ---- Beat 4: Disjointness ----
    S4 = "Beat 4: Disjointness"
    b.add(
        "disjoint",
        S4,
        "Write the no-overlap (disjointness) axiom.",
        kind="block",
        code="[] rdf:type owl:AllDisjointClasses ;\n   owl:members ( :Product :ErrorCode :Symptom :DiagnosticStep :Resolution ) .",
        language=_TURTLE,
        explain="Nothing can be two classes at once. `[]` = anonymous blank node; `( ... )` (spaces!) = an RDF list.",
        mental_model="A law that says a box can't be labelled two unrelated things at the same time.",
        memory_hook="AllDisjoint = 'all separate'; spaces not commas inside ( ).",
        blank="[] rdf:type owl:____ ;\n   owl:____ ( :Product :ErrorCode :Symptom :DiagnosticStep :Resolution ) .",
        answers=["AllDisjointClasses", "members"],
    )
    b.add(
        "blank-node",
        S4,
        "What is `[]` and why doesn't the axiom name it?",
        kind="concept",
        explain="`[]` is a blank node — an anonymous thing that only holds this one statement; nothing else refers back to it.",
        mental_model="A sticky note with no name because no one needs to find it later.",
        memory_hook="Empty brackets = nobody needs its name.",
    )
    b.add(
        "rdf-list",
        S4,
        "How do you write an ordered list in Turtle, and where is one used?",
        kind="concept",
        code="( :Product :ErrorCode :Symptom :DiagnosticStep :Resolution )",
        language=_TURTLE,
        explain="Parentheses with SPACE-separated members = an RDF list. Used in owl:members of the disjointness axiom.",
        memory_hook="( ) with spaces = list; commas would be wrong here.",
    )

    # ---- Beat 5: Object properties ----
    S5 = "Beat 5: Object properties"
    b.add(
        "prop-pattern",
        S5,
        "What shape declares an object property (a verb)?",
        kind="pattern",
        code=':verb rdf:type owl:ObjectProperty ;\n    rdfs:domain :FromClass ;\n    rdfs:range :ToClass ;\n    rdfs:label "..." .',
        language=_TURTLE,
        explain="ObjectProperty = a directed connection; domain = FROM, range = TO.",
        mental_model="Every property is a labelled arrow between two class-boxes.",
        memory_hook="Type, Domain, Range, Label — 'TDRL'.",
    )
    for cid, verb, dom, rng, label in [
        ("prop-canexhibit", "canExhibit", "Product", "ErrorCode", "can exhibit"),
        ("prop-mayindicate", "mayIndicate", "Symptom", "ErrorCode", "may indicate"),
        ("prop-confirmedby", "confirmedBy", "ErrorCode", "DiagnosticStep", "confirmed by"),
        ("prop-leadsto", "leadsTo", "DiagnosticStep", "Resolution", "leads to"),
    ]:
        b.add(
            cid,
            S5,
            f"Declare :{verb} — say the arrow out loud.",
            code=f':{verb} rdf:type owl:ObjectProperty ;\n    rdfs:domain :{dom} ;\n    rdfs:range :{rng} ;\n    rdfs:label "{label}" .',
            language=_TURTLE,
            explain=f"Arrow: (:{dom}) --{verb}--> (:{rng}). Becomes Neo4j relationship type.",
            memory_hook=f"{dom} → {rng}",
            blank=f":{verb} rdf:type owl:____ ;\n    rdfs:domain :{dom} ;\n    rdfs:range :{rng} .",
            answers=["ObjectProperty"],
        )
    b.add(
        "prop-chain",
        S5,
        "Recite the four-arrow chain from Product to Resolution.",
        kind="concept",
        explain="Product -canExhibit-> ErrorCode; Symptom -mayIndicate-> ErrorCode; ErrorCode -confirmedBy-> DiagnosticStep; DiagnosticStep -leadsTo-> Resolution.",
        mental_model="A diagnostic pipeline: car shows a code, symptom hints at it, a step confirms it, the step leads to the fix.",
        memory_hook="exhibit → indicate → confirm → lead.",
    )

    # ---- Beat 6: Restrictions ----
    S6 = "Beat 6: Restrictions"
    b.add(
        "restr-pattern",
        S6,
        "What shape attaches a minimum-cardinality restriction to a class?",
        kind="pattern",
        code=':Class rdfs:subClassOf [\n    rdf:type owl:Restriction ;\n    owl:onProperty :prop ;\n    owl:minCardinality "1"^^xsd:nonNegativeInteger\n] .',
        language=_TURTLE,
        explain="Restriction is attached via rdfs:subClassOf (NOT rdf:type), onto a blank-node Restriction.",
        mental_model="'Being this class MEANS being a subclass of things that have at least one such link.'",
        memory_hook="subClassOf [ Restriction · onProperty · minCardinality ].",
    )
    b.add(
        "restr-errorcode",
        S6,
        "Require every ErrorCode to have ≥1 confirming step.",
        kind="block",
        code=':ErrorCode rdfs:subClassOf [\n    rdf:type owl:Restriction ;\n    owl:onProperty :confirmedBy ;\n    owl:minCardinality "1"^^xsd:nonNegativeInteger\n] .',
        language=_TURTLE,
        explain="An ErrorCode with zero confirming DiagnosticSteps is not allowed to exist — a diagnostic dead end caught at design time.",
        memory_hook="No code without a way to confirm it.",
        blank=':ErrorCode rdfs:____ [\n    rdf:type owl:____ ;\n    owl:onProperty :confirmedBy ;\n    owl:____ "1"^^xsd:nonNegativeInteger\n] .',
        answers=["subClassOf", "Restriction", "minCardinality"],
    )
    b.add(
        "restr-step",
        S6,
        "Require every DiagnosticStep to lead to ≥1 resolution.",
        kind="block",
        code=':DiagnosticStep rdfs:subClassOf [\n    rdf:type owl:Restriction ;\n    owl:onProperty :leadsTo ;\n    owl:minCardinality "1"^^xsd:nonNegativeInteger\n] .',
        language=_TURTLE,
        explain="A step that leads nowhere is invalid — every step must reach a Resolution.",
        memory_hook="No step without a fix.",
        blank=':DiagnosticStep rdfs:subClassOf [\n    rdf:type owl:Restriction ;\n    owl:onProperty :____ ;\n    owl:minCardinality "1"^^xsd:nonNegativeInteger\n] .',
        answers=["leadsTo"],
    )
    b.add(
        "typed-literal",
        S6,
        'What is a "typed literal" and where does one appear in Beat 6?',
        kind="concept",
        code='"1"^^xsd:nonNegativeInteger',
        language=_TURTLE,
        explain='A value plus an explicit datatype tag (^^). Untyped "1" is just a string; minCardinality needs a real integer.',
        memory_hook="^^ = 'this is really a…'; without it, \"1\" is a word not a number.",
    )

    # ---- Beat 7: Individuals ----
    S7 = "Beat 7: Individuals"
    b.add(
        "ind-camry",
        S7,
        "Write the Toyota Camry individual (a real Product).",
        kind="block",
        code=':Toyota_Camry_2022 rdf:type :Product ;\n    rdfs:label "Toyota Camry 2022" ;\n    :canExhibit :P0300 .',
        language=_TURTLE,
        explain="A real instance typed as :Product, linked to error code P0300 via :canExhibit.",
        memory_hook="Instance = rdf:type YOUR class (not owl:Class).",
        blank=':Toyota_Camry_2022 rdf:type :____ ;\n    rdfs:label "Toyota Camry 2022" ;\n    :____ :P0300 .',
        answers=["Product", "canExhibit"],
    )
    b.add(
        "ind-p0300",
        S7,
        "Write the P0300 ErrorCode individual.",
        kind="block",
        code=':P0300 rdf:type :ErrorCode ;\n    rdfs:label "P0300" ;\n    rdfs:comment "Random/multiple cylinder misfire detected" ;\n    :confirmedBy :CheckSparkPlugs .',
        language=_TURTLE,
        explain="A real ErrorCode; obeys Beat 6 because it has a :confirmedBy step.",
        memory_hook="P0300 → confirmedBy → CheckSparkPlugs.",
        blank=':P0300 rdf:type :ErrorCode ;\n    rdfs:label "P0300" ;\n    :____ :CheckSparkPlugs .',
        answers=["confirmedBy"],
    )
    b.add(
        "ind-roughidle",
        S7,
        "Write the RoughIdle Symptom individual.",
        kind="block",
        code=':RoughIdle rdf:type :Symptom ;\n    rdfs:label "Rough idle" ;\n    :mayIndicate :P0300 .',
        language=_TURTLE,
        explain="A symptom that points at the error code via :mayIndicate.",
        memory_hook="Symptom → mayIndicate → ErrorCode.",
        blank=':RoughIdle rdf:type :Symptom ;\n    rdfs:label "Rough idle" ;\n    :____ :P0300 .',
        answers=["mayIndicate"],
    )
    b.add(
        "ind-checkplugs",
        S7,
        "Write the CheckSparkPlugs DiagnosticStep individual.",
        kind="block",
        code=':CheckSparkPlugs rdf:type :DiagnosticStep ;\n    rdfs:label "Check spark plugs and ignition coils" ;\n    :leadsTo :ReplaceSparkPlugs .',
        language=_TURTLE,
        explain="Obeys Beat 6 because it has a :leadsTo resolution.",
        memory_hook="Step → leadsTo → Resolution.",
        blank=':CheckSparkPlugs rdf:type :DiagnosticStep ;\n    rdfs:label "Check spark plugs and ignition coils" ;\n    :____ :ReplaceSparkPlugs .',
        answers=["leadsTo"],
    )
    b.add(
        "ind-replaceplugs",
        S7,
        "Write the ReplaceSparkPlugs Resolution individual.",
        kind="block",
        code=':ReplaceSparkPlugs rdf:type :Resolution ;\n    rdfs:label "Replace worn spark plugs" .',
        language=_TURTLE,
        explain="The terminal fix; a Resolution has no outgoing required property.",
        memory_hook="Resolution = end of the chain.",
        blank=':ReplaceSparkPlugs rdf:type :____ ;\n    rdfs:label "Replace worn spark plugs" .',
        answers=["Resolution"],
    )
    b.add(
        "neo4j-map",
        S7,
        "How does Beat 7 become Neo4j?",
        kind="concept",
        explain="Each `rdf:type :Class` → a node with that label; each :canExhibit/:mayIndicate/:confirmedBy/:leadsTo → a relationship.",
        mental_model="Nouns become nodes; verbs become relationships.",
        memory_hook="type → node label; property → relationship type.",
    )

    return b.cards


# ══════════════════════════════════════════════════════════════════════════
# GUIDE 2 — Smart Cypher-Generation Agent (Python)
# ══════════════════════════════════════════════════════════════════════════
def _build_agent() -> list[MemoryCard]:
    b = _Builder("mc-02-smart-cypher-agent")

    # ---- Mental models ----
    S0 = "Mental models & memory hooks"
    b.add(
        "one-liner",
        S0,
        "One-sentence summary of this agent.",
        kind="concept",
        explain="One smart tool — it asks a second LLM to write the Cypher, then runs whatever Cypher comes back.",
        mental_model="A worker with an assistant at the door who writes the search instructions on the spot.",
        memory_hook="Write-then-run: LLM writes Cypher, try/except runs it.",
    )
    b.add(
        "two-llms",
        S0,
        "Name the TWO different LLM calls and their jobs.",
        kind="concept",
        explain="llm in diagnostic_agent_node = decides WHETHER to call the tool. cypher_llm inside the tool = writes the Cypher.",
        mental_model="Manager (should I search?) vs specialist (what exactly to search).",
        memory_hook="Decider vs Writer.",
    )
    b.add(
        "skeleton",
        S0,
        "What has stayed identical across all three versions?",
        kind="concept",
        explain="The outer skeleton: State → Nodes → Graph → Run. Only the tool's insides evolve.",
        mental_model="Same chassis, different engine each version.",
        memory_hook="S-N-G-R never changes.",
    )
    b.add(
        "name-collision",
        S0,
        "What variable name is reused for two different things?",
        kind="concept",
        explain="`graph` = the Neo4jGraph in Beat 1, then REASSIGNED to the compiled LangGraph app in Beat 5.",
        mental_model="Same label on two different boxes — an unlucky collision.",
        memory_hook="graph #1 = Neo4j; graph #2 = LangGraph app.",
    )
    b.add(
        "prompt-two-jobs",
        S0,
        "What two jobs does the Cypher-generation prompt do at once?",
        kind="concept",
        explain="(1) Teaches the schema (node/rel names) so the LLM can't invent labels; (2) constrains output format ('only return the Cypher').",
        memory_hook="Schema + format.",
    )
    b.add(
        "lineage",
        S0,
        "The three-version trade-off in one line.",
        kind="concept",
        explain="Original: 2 general tools (Python if). Graph-only: 1 hardcoded Cypher. Smart: 1 LLM-generated Cypher (schema-constrained).",
        mental_model="Flexibility ↑ as determinism ↓ across the three versions.",
        memory_hook="if-statements → fixed Cypher → generated Cypher.",
    )

    # ---- Beat 1: imports + setup ----
    S1 = "Beat 1: Imports + Neo4jGraph setup"
    b.add(
        "imp-typing",
        S1,
        "Import the typing helpers for the state.",
        code="from typing import TypedDict, Annotated, List",
        language=_PY,
        explain="TypedDict for the state schema; Annotated + List for the reducer-annotated messages field.",
        memory_hook="TypedDict/Annotated/List = the state's ingredients.",
        blank="from typing import ____, Annotated, List",
        answers=["TypedDict"],
    )
    b.add(
        "imp-langgraph",
        S1,
        "Import StateGraph and END.",
        code="from langgraph.graph import StateGraph, END",
        language=_PY,
        explain="StateGraph builds the workflow; END is the terminal sentinel.",
        memory_hook="Graph + END from langgraph.graph.",
        blank="from langgraph.graph import ____, END",
        answers=["StateGraph"],
    )
    b.add(
        "imp-toolnode",
        S1,
        "Import ToolNode.",
        code="from langgraph.prebuilt import ToolNode",
        language=_PY,
        explain="A prebuilt node that actually executes tool calls.",
        memory_hook="ToolNode = prebuilt tool-runner.",
        blank="from langgraph.____ import ToolNode",
        answers=["prebuilt"],
    )
    b.add(
        "imp-chatopenai",
        S1,
        "Import ChatOpenAI.",
        code="from langchain_openai import ChatOpenAI",
        language=_PY,
        explain="The LLM used for both the decider and the cypher-writer.",
        blank="from langchain_openai import ____",
        answers=["ChatOpenAI"],
    )
    b.add(
        "imp-tool",
        S1,
        "Import the @tool decorator.",
        code="from langchain_core.tools import tool",
        language=_PY,
        explain="Turns a plain function into a callable tool the LLM can invoke.",
        blank="from langchain_core.tools import ____",
        answers=["tool"],
    )
    b.add(
        "imp-pydantic",
        S1,
        "Import BaseModel and Field.",
        code="from pydantic import BaseModel, Field",
        language=_PY,
        explain="Defines the tool's typed input schema.",
        blank="from pydantic import BaseModel, ____",
        answers=["Field"],
    )
    b.add(
        "imp-operator",
        S1,
        "Import operator.",
        code="import operator",
        language=_PY,
        explain="operator.add is the reducer that APPENDS to the messages list in state.",
        memory_hook="operator.add = 'append messages'.",
        blank="import ____",
        answers=["operator"],
    )
    b.add(
        "imp-neo4jgraph",
        S1,
        "Import Neo4jGraph (the NEW import this version).",
        code="from langchain_neo4j import Neo4jGraph",
        language=_PY,
        explain="LangChain-native wrapper replacing the raw neo4j.GraphDatabase driver; gives graph.query() directly.",
        mental_model="A friendlier Neo4j handle — no manual session boilerplate.",
        memory_hook="langchain_neo4j → Neo4jGraph.",
        blank="from ____ import Neo4jGraph",
        answers=["langchain_neo4j"],
    )
    b.add(
        "setup-graph",
        S1,
        "Construct the Neo4jGraph object.",
        kind="block",
        code="graph = Neo4jGraph(\n    url=NEO4J_URI,\n    username=NEO4J_USER,\n    password=NEO4J_PASSWORD\n)",
        language=_PY,
        explain="Exposes graph.query(cypher_string) directly — no `with driver.session()` needed.",
        memory_hook="url / username / password → graph.query().",
        blank="graph = ____(\n    url=NEO4J_URI,\n    username=NEO4J_USER,\n    password=NEO4J_PASSWORD\n)",
        answers=["Neo4jGraph"],
    )

    # ---- Beat 2: model + tool ----
    S2 = "Beat 2: One model + one self-writing tool"
    b.add(
        "model",
        S2,
        "Define the tool's input schema.",
        kind="block",
        code='class DiagnosticQueryInput(BaseModel):\n    user_input: str = Field(..., description="User\'s car problem (error code or symptoms)")',
        language=_PY,
        explain="A pydantic model; Field(...) marks user_input as required with a description the LLM reads.",
        memory_hook="BaseModel + Field(...) = required, described input.",
        blank='class DiagnosticQueryInput(____):\n    user_input: str = ____(..., description="...")',
        answers=["BaseModel", "Field"],
    )
    b.add(
        "tool-decorator",
        S2,
        "Decorate and define the tool signature.",
        kind="block",
        code="@tool(args_schema=DiagnosticQueryInput)\ndef query_graph(user_input: str) -> str:",
        language=_PY,
        explain="@tool with args_schema binds the pydantic input; the function returns a string result.",
        memory_hook="@tool(args_schema=...) → the one tool.",
        blank="@____(args_schema=DiagnosticQueryInput)\ndef query_graph(user_input: str) -> str:",
        answers=["tool"],
    )
    b.add(
        "cypher-llm",
        S2,
        "Create the SECOND LLM (the Cypher writer).",
        code='cypher_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)',
        language=_PY,
        explain="A separate LLM instance inside the tool whose only job is writing Cypher. temperature=0 = deterministic.",
        memory_hook="cypher_llm = the writer; temperature 0 = no creativity.",
        blank='cypher_llm = ChatOpenAI(model="gpt-4o-mini", temperature=____)',
        answers=["0"],
    )
    b.add(
        "prompt",
        S2,
        "Write the Cypher-generation prompt (schema + format).",
        kind="block",
        code=(
            'prompt = f"""\n'
            "    You are an expert at writing Cypher queries for a car diagnostics knowledge graph.\n"
            "    The graph has nodes: CarModel, ErrorCode, Symptom, Cause, Fix\n"
            "    Relationships: HAS_ERROR, CAUSED_BY, FIXED_BY, LEADS_TO\n"
            '    User query: "{user_input}"\n'
            "    Generate a single, safe Cypher query that answers this.\n"
            "    Only return the Cypher query, nothing else.\n"
            '    """'
        ),
        language=_PY,
        explain="Lists the schema so the LLM can't invent labels, and constrains output to only the query.",
        memory_hook="Nodes + Relationships + 'only return the Cypher'.",
        blank='prompt = f"""\n    ... The graph has nodes: ____\n    Relationships: ____\n    User query: "{user_input}"\n    Only return the Cypher query, nothing else.\n    """',
        answers=["CarModel, ErrorCode, Symptom, Cause, Fix", "HAS_ERROR, CAUSED_BY, FIXED_BY, LEADS_TO"],
    )
    b.add(
        "invoke-strip",
        S2,
        "Invoke the writer LLM and clean its output.",
        kind="block",
        code="cypher_response = cypher_llm.invoke(prompt)\ncypher_query = cypher_response.content.strip()",
        language=_PY,
        explain=".strip() removes stray whitespace/newlines (or a code-fence wrapper) the LLM might add.",
        memory_hook=".strip() guards against ```cypher wrappers and whitespace.",
        blank="cypher_response = cypher_llm.____(prompt)\ncypher_query = cypher_response.content.____()",
        answers=["invoke", "strip"],
    )
    b.add(
        "try-except",
        S2,
        "Run the generated Cypher defensively.",
        kind="block",
        code=(
            "try:\n"
            "    results = graph.query(cypher_query)\n"
            "    if results:\n"
            "        return str(results)\n"
            "    else:\n"
            '        return "No results found in the diagnostic graph."\n'
            "except Exception as e:\n"
            '    return f"Error running query: {str(e)}"'
        ),
        language=_PY,
        explain="Generated Cypher is untrusted input; try/except returns a clean error string instead of crashing.",
        mental_model="Treat LLM-written code like any dynamic, untrusted input.",
        memory_hook="try graph.query → else 'no results' → except → error string.",
        blank='try:\n    results = graph.query(cypher_query)\n    if results:\n        return ____(results)\n    else:\n        return "No results found in the diagnostic graph."\nexcept ____ as e:\n    return f"Error running query: {str(e)}"',
        answers=["str", "Exception"],
    )
    b.add(
        "tools-list",
        S2,
        "Register the tool.",
        code="tools = [query_graph]",
        language=_PY,
        explain="A one-element list of tools bound to the agent.",
        memory_hook="tools = [ the one tool ].",
        blank="tools = [____]",
        answers=["query_graph"],
    )

    # ---- Beat 3: State ----
    S3 = "Beat 3: State (unchanged)"
    b.add(
        "state",
        S3,
        "Define the agent state.",
        kind="block",
        code="class AgentState(TypedDict):\n    messages: Annotated[List, operator.add]",
        language=_PY,
        explain="messages accumulates; Annotated[..., operator.add] tells LangGraph to APPEND, not overwrite.",
        mental_model="A running transcript that only ever grows.",
        memory_hook="Annotated[List, operator.add] = 'append messages'.",
        blank="class AgentState(TypedDict):\n    messages: Annotated[List, operator.____]",
        answers=["add"],
    )

    # ---- Beat 4: nodes + graph ----
    S4 = "Beat 4: Nodes + Graph (unchanged structure)"
    b.add(
        "agent-node",
        S4,
        "Write the diagnostic agent node (the FIRST llm).",
        kind="block",
        code='def diagnostic_agent_node(state: AgentState):\n    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)\n    response = llm.invoke(state["messages"])\n    return {"messages": [response]}',
        language=_PY,
        explain="bind_tools lets this LLM decide whether to call query_graph; returns the response appended to messages.",
        memory_hook="bind_tools = the decider LLM.",
        blank='def diagnostic_agent_node(state: AgentState):\n    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).____(tools)\n    response = llm.invoke(state["messages"])\n    return {"messages": [response]}',
        answers=["bind_tools"],
    )
    b.add(
        "tool-node",
        S4,
        "Create the tool-executing node.",
        code="tool_node = ToolNode(tools)",
        language=_PY,
        explain="Prebuilt node that runs whichever tool the LLM asked for.",
        blank="tool_node = ____(tools)",
        answers=["ToolNode"],
    )
    b.add(
        "build-nodes",
        S4,
        "Create the workflow and add nodes + entry point.",
        kind="block",
        code='workflow = StateGraph(AgentState)\nworkflow.add_node("diagnostic_agent", diagnostic_agent_node)\nworkflow.add_node("tools", tool_node)\nworkflow.set_entry_point("diagnostic_agent")',
        language=_PY,
        explain="Two nodes: the agent and the tools; entry point is the agent.",
        memory_hook="add_node ×2, set_entry_point = agent.",
        blank='workflow = StateGraph(AgentState)\nworkflow.add_node("diagnostic_agent", diagnostic_agent_node)\nworkflow.add_node("tools", tool_node)\nworkflow.____("diagnostic_agent")',
        answers=["set_entry_point"],
    )
    b.add(
        "should-continue",
        S4,
        "Write the routing function + edges.",
        kind="block",
        code='def should_continue(state):\n    last = state["messages"][-1]\n    return "tools" if getattr(last, "tool_calls", None) else END\n\nworkflow.add_conditional_edges("diagnostic_agent", should_continue)\nworkflow.add_edge("tools", "diagnostic_agent")',
        language=_PY,
        explain="If the last message has tool_calls → go to tools, else END. Tools loop back to the agent.",
        mental_model="Keep looping agent↔tools until the agent stops asking for tools.",
        memory_hook="tool_calls? → tools, else END; tools → back to agent.",
        blank='def should_continue(state):\n    last = state["messages"][-1]\n    return "tools" if getattr(last, "____", None) else END\n\nworkflow.add_____("diagnostic_agent", should_continue)\nworkflow.add_edge("tools", "diagnostic_agent")',
        answers=["tool_calls", "conditional_edges"],
    )
    b.add(
        "compile",
        S4,
        "Return the compiled graph.",
        code="return workflow.compile()",
        language=_PY,
        explain="compile() turns the workflow definition into a runnable app.",
        memory_hook="compile() = make it runnable.",
        blank="return workflow.____()",
        answers=["compile"],
    )

    # ---- Beat 5: run ----
    S5 = "Beat 5: Run (name collision noted)"
    b.add(
        "run",
        S5,
        "Write the run block (mind the `graph` reassignment).",
        kind="block",
        code='if __name__ == "__main__":\n    graph = build_graph()\n    state = {"messages": [("human", "My Honda Civic has P0420 error and check engine light")]}\n    result = graph.invoke(state)\n    print(result["messages"][-1].content)',
        language=_PY,
        explain="Here `graph` is reassigned to the compiled LangGraph app (not the Neo4jGraph from Beat 1).",
        memory_hook='graph = build_graph() → now it\'s the app; invoke with a "human" message.',
        blank='if __name__ == "__main__":\n    graph = build_graph()\n    state = {"messages": [("____", "My Honda Civic has P0420 ...")]}\n    result = graph.____(state)\n    print(result["messages"][-1].content)',
        answers=["human", "invoke"],
    )

    return b.cards


MASTERCLASS_CARDS: dict[str, list[MemoryCard]] = {
    "mc-01-rdf-owl-ontology-turtle": _build_ontology(),
    "mc-02-smart-cypher-agent": _build_agent(),
}


def cards_for(masterclass_id: str) -> list[MemoryCard]:
    return MASTERCLASS_CARDS.get(masterclass_id, [])


def sections_for(masterclass_id: str) -> list[str]:
    """Ordered unique section names (for 'write the whole section' drills)."""
    seen: list[str] = []
    for c in cards_for(masterclass_id):
        if c.section not in seen:
            seen.append(c.section)
    return seen
