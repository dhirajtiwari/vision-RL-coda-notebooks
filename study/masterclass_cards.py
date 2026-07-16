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
        python: str = "",
        cypher: str = "",
        shacl: str = "",
        what: str = "",
        how: str = "",
        where: str = "",
        when: str = "",
        who: str = "",
        why: str = "",
        pitfalls: list[str] | None = None,
        sources: list | None = None,
        run_hint: str = "",
    ) -> None:
        from study.models import SourceRef

        srcs = []
        for s in sources or []:
            if isinstance(s, SourceRef):
                srcs.append(s)
            elif isinstance(s, dict):
                srcs.append(SourceRef(**s))
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
                python=python,
                cypher=cypher,
                shacl=shacl,
                what=what,
                how=how,
                where=where,
                when=when,
                who=who,
                why=why,
                pitfalls=pitfalls or [],
                sources=srcs,
                run_hint=run_hint,
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
        python=(
            "# rdflib (as in the notebook's TBox cell)\n"
            "g.add((WD.Product, RDF.type, OWL.Class))\n"
            'g.add((WD.Product, RDFS.label, Literal("Product")))\n'
            'g.add((WD.Product, RDFS.comment, Literal("...")))'
        ),
        cypher=(
            "// A class is a node LABEL in Neo4j (no DDL needed).\n"
            "// Optionally guard identity with a constraint:\n"
            "CREATE CONSTRAINT product_id IF NOT EXISTS\n"
            "FOR (p:Product) REQUIRE p.product_id IS UNIQUE;"
        ),
        shacl=":ProductShape a sh:NodeShape ;\n    sh:targetClass :Product .",
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
            python=f'g.add((WD.{cls}, RDF.type, OWL.Class))\ng.add((WD.{cls}, RDFS.label, Literal("{label}")))',
            cypher=f"// :{cls} is a node label; e.g. an instance:\nMERGE (n:{cls} {{id: $id}});",
            shacl=f":{cls}Shape a sh:NodeShape ; sh:targetClass :{cls} .",
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
        python=(
            "# rdflib: AllDisjointClasses via an RDF list, OR the notebook's simpler pairwise form\n"
            "from rdflib.collection import Collection\n"
            "node, members = BNode(), BNode()\n"
            "g.add((node, RDF.type, OWL.AllDisjointClasses))\n"
            "Collection(g, members, [WD.Product, WD.ErrorCode, WD.Symptom, WD.DiagnosticStep, WD.Resolution])\n"
            "g.add((node, OWL.members, members))\n"
            "# notebook style (pairwise):\n"
            "g.add((WD.Product, OWL.disjointWith, WD.ErrorCode))"
        ),
        cypher=(
            "// Neo4j has no disjointness. Find a node wrongly given two labels:\n"
            "MATCH (n) WHERE size(labels(n)) > 1 RETURN n;"
        ),
        shacl=(
            "# No direct 'disjoint'; forbid the other class per shape:\n"
            ":ProductShape a sh:NodeShape ; sh:targetClass :Product ;\n"
            "    sh:not [ sh:class :ErrorCode ] ."
        ),
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
        python=(
            "# rdflib (notebook OBJECT_PROPS loop)\n"
            "g.add((WD.canExhibit, RDF.type, OWL.ObjectProperty))\n"
            "g.add((WD.canExhibit, RDFS.domain, WD.Product))\n"
            "g.add((WD.canExhibit, RDFS.range, WD.ErrorCode))"
        ),
        cypher=(
            "// object property = relationship TYPE\n"
            "MATCH (p:Product {id:$p}), (e:ErrorCode {id:$e})\n"
            "MERGE (p)-[:CAN_EXHIBIT]->(e);"
        ),
        shacl=(
            ":ProductShape sh:property [\n" "    sh:path :canExhibit ; sh:class :ErrorCode ; sh:nodeKind sh:IRI ] ."
        ),
    )
    for cid, verb, dom, rng, label, rel in [
        ("prop-canexhibit", "canExhibit", "Product", "ErrorCode", "can exhibit", "CAN_EXHIBIT"),
        ("prop-mayindicate", "mayIndicate", "Symptom", "ErrorCode", "may indicate", "MAY_INDICATE"),
        ("prop-confirmedby", "confirmedBy", "ErrorCode", "DiagnosticStep", "confirmed by", "CONFIRMED_BY"),
        ("prop-leadsto", "leadsTo", "DiagnosticStep", "Resolution", "leads to", "LEADS_TO"),
    ]:
        b.add(
            cid,
            S5,
            f"Declare :{verb} — say the arrow out loud.",
            code=f':{verb} rdf:type owl:ObjectProperty ;\n    rdfs:domain :{dom} ;\n    rdfs:range :{rng} ;\n    rdfs:label "{label}" .',
            language=_TURTLE,
            explain=f"Arrow: (:{dom}) --{verb}--> (:{rng}). Becomes Neo4j relationship :{rel}.",
            memory_hook=f"{dom} → {rng}",
            blank=f":{verb} rdf:type owl:____ ;\n    rdfs:domain :{dom} ;\n    rdfs:range :{rng} .",
            answers=["ObjectProperty"],
            python=(
                f"g.add((WD.{verb}, RDF.type, OWL.ObjectProperty))\n"
                f"g.add((WD.{verb}, RDFS.domain, WD.{dom}))\n"
                f"g.add((WD.{verb}, RDFS.range, WD.{rng}))"
            ),
            cypher=f"MATCH (a:{dom} {{id:$a}}), (b:{rng} {{id:$b}})\nMERGE (a)-[:{rel}]->(b);",
            shacl=f":{dom}Shape sh:property [ sh:path :{verb} ; sh:class :{rng} ] .",
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
        python=(
            "# rdflib (notebook: BNode restriction)\n"
            "r = BNode()\n"
            "g.add((r, RDF.type, OWL.Restriction))\n"
            "g.add((r, OWL.onProperty, WD.confirmedBy))\n"
            "g.add((r, OWL.minCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))\n"
            "g.add((WD.ErrorCode, RDFS.subClassOf, r))"
        ),
        cypher=(
            "// Neo4j does NOT enforce cardinality. Find violators instead:\n"
            "MATCH (e:ErrorCode) WHERE NOT (e)-[:CONFIRMED_BY]->()\n"
            "RETURN e;"
        ),
        shacl=(
            "# SHACL is where this rule is actually ENFORCED at runtime:\n"
            ":ErrorCodeShape a sh:NodeShape ; sh:targetClass :ErrorCode ;\n"
            "    sh:property [ sh:path :confirmedBy ; sh:minCount 1 ] ."
        ),
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
        python=(
            "r = BNode()\n"
            "g.add((r, RDF.type, OWL.Restriction))\n"
            "g.add((r, OWL.onProperty, WD.confirmedBy))\n"
            "g.add((r, OWL.minCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))\n"
            "g.add((WD.ErrorCode, RDFS.subClassOf, r))"
        ),
        cypher="MATCH (e:ErrorCode) WHERE NOT (e)-[:CONFIRMED_BY]->()\nRETURN e;  // violators",
        shacl=":ErrorCodeShape a sh:NodeShape ; sh:targetClass :ErrorCode ;\n    sh:property [ sh:path :confirmedBy ; sh:minCount 1 ] .",
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
        python=(
            "g.add((WD.Toyota_Camry_2022, RDF.type, WD.Product))\n"
            'g.add((WD.Toyota_Camry_2022, RDFS.label, Literal("Toyota Camry 2022")))\n'
            "g.add((WD.Toyota_Camry_2022, WD.canExhibit, WD.P0300))"
        ),
        cypher=(
            'MERGE (p:Product {name: "Toyota Camry 2022"})\n'
            'MERGE (e:ErrorCode {code: "P0300"})\n'
            "MERGE (p)-[:CAN_EXHIBIT]->(e);"
        ),
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
        python=(
            "g.add((WD.P0300, RDF.type, WD.ErrorCode))\n"
            'g.add((WD.P0300, RDFS.label, Literal("P0300")))\n'
            'g.add((WD.P0300, RDFS.comment, Literal("Random/multiple cylinder misfire detected")))\n'
            "g.add((WD.P0300, WD.confirmedBy, WD.CheckSparkPlugs))"
        ),
        cypher=(
            'MERGE (e:ErrorCode {code: "P0300", description: "Random/multiple cylinder misfire detected"})\n'
            'MERGE (s:DiagnosticStep {id: "CheckSparkPlugs"})\n'
            "MERGE (e)-[:CONFIRMED_BY]->(s);"
        ),
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
        python=(
            "# The notebook's Part 6: same triples, swap the store\n"
            "from langchain_neo4j import Neo4jGraph\n"
            "graph = Neo4jGraph(url=..., username=..., password=...)\n"
            'graph.query("MERGE (p:Product {name:$n})", {"n": "Toyota Camry 2022"})'
        ),
        cypher=(
            "// Rosetta: Turtle triple -> Cypher\n"
            "// :X a :Product           -> MERGE (:Product {id:...})\n"
            "// :X :canExhibit :Y       -> MERGE (x)-[:CAN_EXHIBIT]->(y)\n"
            "// owl:minCardinality 1    -> (not enforced; use SHACL)"
        ),
        shacl=(
            "# SHACL is the runtime enforcer Neo4j lacks:\n"
            ":ErrorCodeShape a sh:NodeShape ; sh:targetClass :ErrorCode ;\n"
            "    sh:property [ sh:path :confirmedBy ; sh:minCount 1 ] ."
        ),
    )

    # Non-destructive 5W+H enrichment (does NOT change front/code/blank/answers)
    enrich = {
        "chant": {
            "what": "The ordered recipe for writing the car-diagnostics OWL file in Turtle.",
            "how": "Write prefixes, then ontology header, classes, disjointness, object properties, restrictions, then individuals.",
            "where": "Design-time ontology file (Masterclass body); exports under docs/ontology/ in the product.",
            "when": "Before any Neo4j CREATE/MERGE of product knowledge.",
            "who": "Ontology author / knowledge engineer.",
            "why": "The rulebook must exist before instance facts, so every fact is typed and linkable.",
            "sources": [
                {
                    "title": "W3C OWL 2 Primer",
                    "url": "https://www.w3.org/TR/owl2-primer/",
                    "kind": "standard",
                }
            ],
            "run_hint": "Open Masters → this guide → Flashcards → section 'Mental models'.",
        },
        "tbox-abox": {
            "what": "TBox = schema (classes/properties/axioms). ABox = instance facts about real cars.",
            "how": "Declare classes/properties first (Beats 3–6); assert individuals last (Beat 7).",
            "where": "Turtle ontology file; runtime product uses Neo4j ABox under a shared TBox.",
            "when": "Every knowledge model: design schema once, load many instances.",
            "who": "Knowledge steward (TBox) vs data pipeline (ABox).",
            "why": "Separating schema from data scales and keeps validation honest.",
            "sources": [
                {
                    "title": "W3C OWL 2 Primer (TBox vs ABox)",
                    "url": "https://www.w3.org/TR/owl2-primer/",
                    "kind": "standard",
                }
            ],
        },
        "a-is-type": {
            "what": "Turtle keyword `a` means rdf:type.",
            "how": "Write `wd:wm-001 a :Product .` instead of `rdf:type`.",
            "where": "Any Turtle class or individual typing triple.",
            "when": "Whenever you assert 'this resource is a member of that class'.",
            "who": "Ontology authors (W3C RDF 1.1 Primer).",
            "why": "Readable English-like typing without repeating rdf:type.",
            "sources": [
                {
                    "title": "W3C RDF 1.1 Primer §5.1 Turtle",
                    "url": "https://www.w3.org/TR/rdf11-primer/",
                    "kind": "standard",
                }
            ],
        },
        "punctuation": {
            "what": "Turtle statement punctuation: `;` `,` `.`",
            "how": "`;` same subject new predicate; `,` same subject+predicate new object; `.` end statement.",
            "where": "Every multi-line Turtle block in Beats 3–7.",
            "when": "Authoring readable grouped triples.",
            "who": "Turtle authors (Prud'hommeaux & Carothers).",
            "why": "Wrong punctuation is the #1 silent parse break.",
            "sources": [
                {
                    "title": "W3C RDF 1.1 Turtle",
                    "url": "https://www.w3.org/TR/turtle/",
                    "kind": "standard",
                }
            ],
        },
        "domain-range": {
            "what": "rdfs:domain / rdfs:range constrain property ends.",
            "how": "domain = subject class; range = object class of the property.",
            "where": "Beat 5 object property declarations.",
            "when": "Defining allowed edges in the TBox.",
            "who": "RDFS/OWL modelers.",
            "why": "Documents intended link direction for humans and reasoners.",
            "sources": [
                {
                    "title": "W3C RDF Schema 1.1",
                    "url": "https://www.w3.org/TR/rdf-schema/",
                    "kind": "standard",
                }
            ],
            "cypher": "(:Symptom)-[:INDICATES]->(:ErrorCode)  // domain→range as node labels",
        },
        "neo4j-gotcha": {
            "what": "OWL minCardinality is not enforced by Neo4j storage alone.",
            "how": "Enforce with SHACL/pyshacl, app shapes (ontology_validate), or a reasoner — not bare Bolt.",
            "where": "After Turtle design; before/while loading ABox into Neo4j.",
            "when": "Promote gates and CI validation.",
            "who": "Platform + knowledge ops.",
            "why": "Paper ontology ≠ database police unless you wire checks.",
            "sources": [
                {"title": "W3C SHACL", "url": "https://www.w3.org/TR/shacl/", "kind": "standard"},
                {
                    "title": "Neo4j Cypher Manual — constraints",
                    "url": "https://neo4j.com/docs/cypher-manual/current/constraints/",
                    "kind": "docs",
                },
            ],
            "run_hint": "In this product: graph/enterprise_pipeline/ontology_validate.py before promote.",
        },
        "neo4j-map": {
            "what": "Rosetta map: Turtle individuals/properties → Neo4j nodes/relationships.",
            "how": "rdf:type Class → node label; object properties → relationship types; MERGE on business keys.",
            "where": "populate_graph.py after ontology design; dual Neo4j prod/staging.",
            "when": "Materialize/promote ABox loads.",
            "who": "ETL loaders + GraphRAG consumers.",
            "why": "Same meaning, operational store optimized for multi-hop diagnosis.",
            "sources": [
                {
                    "title": "Neo4j Cypher Manual — MERGE",
                    "url": "https://neo4j.com/docs/cypher-manual/current/clauses/merge/",
                    "kind": "docs",
                }
            ],
            "run_hint": "After load: SHOW CONSTRAINTS; then MATCH a known Product by product_id.",
        },
    }
    return _apply_enrich(b.cards, enrich)


def _apply_enrich(cards: list[MemoryCard], enrich: dict) -> list[MemoryCard]:
    """Merge optional 5W+H fields without touching front/code/blank/answers unless listed."""
    from study.models import SourceRef

    out: list[MemoryCard] = []
    for c in cards:
        short = c.id.split("::", 1)[-1]
        extra = enrich.get(short)
        if not extra:
            out.append(c)
            continue
        e = dict(extra)
        if "sources" in e:
            srcs = []
            for s in e["sources"] or []:
                if isinstance(s, SourceRef):
                    srcs.append(s)
                elif isinstance(s, dict):
                    srcs.append(SourceRef(**s))
            e["sources"] = srcs
        out.append(c.model_copy(update=e))
    return out


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

    # Light 5W+H on agent mental models only (does not change front/code/blank)
    enrich = {
        "one-liner": {
            "what": "LangGraph agent that generates Cypher via a second LLM, then executes it.",
            "how": "Tool node: prompt LLM for Cypher → parse → graph.query → return rows or error.",
            "where": "Study masterclass body; product core path prefers fixed GraphRAG Cypher (see OVERRIDES).",
            "when": "Flexible exploration demos; not the production deterministic diagnose core.",
            "who": "Agent authors studying Text2Cypher patterns.",
            "why": "Teaches flexibility vs determinism trade-off vs hardcoded Cypher.",
            "sources": [
                {
                    "title": "LangGraph docs",
                    "url": "https://langchain-ai.github.io/langgraph/",
                    "kind": "docs",
                }
            ],
        },
    }
    return _apply_enrich(b.cards, enrich)


def _build_graph_ops() -> list[MemoryCard]:
    """Masterclass cards: indexing, delta, partition, concurrency, sharding (repo-grounded)."""
    b = _Builder("mc-03-graph-ops-index-delta-scale")
    S0 = "Mental models"
    b.add(
        "index-vs-edge",
        S0,
        "What does a Neo4j index buy you vs walking relationships?",
        kind="concept",
        explain="Indexes speed property lookups (find node by product_id). Multi-hop meaning still comes from relationship expansion, not a 'path index'.",
        mental_model="Index = phone book to the house; edges = the roads between houses.",
        memory_hook="Seek identity, expand meaning.",
        what="A side structure mapping property values → nodes (unique constraints create unique indexes).",
        how="CREATE CONSTRAINT … REQUIRE prop IS UNIQUE (Neo4j 5) then MATCH/MERGE on that prop.",
        where="graph/populate_graph.py create_constraints; SHOW INDEXES in Browser.",
        when="On every populate/promote load (IF NOT EXISTS); used on every diagnose seek.",
        who="ETL loader creates; GraphRAG queries use.",
        why="Without it: label scans + possible duplicate business ids.",
        code="CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        language="cypher",
        pitfalls=[
            "Indexing every property wastes writes.",
            "Full-text/vector are different tools — not a substitute for unique keys.",
        ],
        sources=[
            {
                "title": "Neo4j Cypher Manual — Constraints",
                "url": "https://neo4j.com/docs/cypher-manual/current/constraints/",
                "kind": "docs",
            }
        ],
        run_hint="Neo4j Browser :7474 → SHOW CONSTRAINTS; SHOW INDEXES;",
    )
    b.add(
        "delta-vs-algorithm",
        S0,
        "Delta stepping in this product vs the Delta-stepping algorithm?",
        kind="concept",
        explain="Here delta = incremental ABox change application (entity_delta + selection promote). Not the parallel SSSP 'delta-stepping' algorithm.",
        mental_model="Warehouse restock of changed boxes, not a shortest-path paper.",
        memory_hook="Delta = changed knowledge packs.",
        what="Apply only NEW/UPDATE product ABox into staging→production via MERGE.",
        how="change_preview → entity_delta → select product_ids → validate → materialize → promote.",
        where="change_preview.py, entity_delta.py, populate_graph.py, Admin wizard.",
        when="Onboard/bulletin updates — not on every chat message.",
        who="Knowledge operator / control plane.",
        why="Avoid full fleet rewrite; fail-closed promote.",
        sources=[{"title": "docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md", "kind": "docs"}],
        run_hint="Admin → Fetch → entity delta → select → promote staging then production.",
    )
    b.add(
        "logical-vs-fabric",
        S0,
        "Logical partition vs Neo4j Fabric sharding?",
        kind="concept",
        explain="Logical: same DB, keys (tenant|product) isolate work/cache/limits. Fabric/composite: separate databases; edges typically don't cross shards.",
        mental_model="Logical = labeled shelves in one warehouse; Fabric = separate warehouses.",
        memory_hook="Keys now; shards later if one DB can't scale.",
        what="Partitioning strategy for multi-tenant/product scale.",
        how="runtime/partitioning.py today; composite DBs only when needed.",
        where="API rate limits, caches, selection product_ids.",
        when="Always for keys; physical shards only after SLOs break.",
        who="Platform engineers.",
        why="Product-scoped diagnose maps cleanly to product shards later.",
        sources=[
            {
                "title": "Neo4j composite databases concepts",
                "url": "https://neo4j.com/docs/operations-manual/current/scalability/composite-databases/concepts/",
                "kind": "docs",
            }
        ],
    )

    S1 = "Beat 1: Unique constraints (indexing)"
    b.add(
        "create-constraints-fn",
        S1,
        "Write create_constraints(tx) for Product and Symptom uniqueness.",
        kind="block",
        code=(
            "def create_constraints(tx) -> None:\n"
            "    for query in [\n"
            '        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",\n'
            '        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",\n'
            "        # … FailureMode, Part, Asset, Claim, …\n"
            "    ]:\n"
            "        tx.run(query)"
        ),
        language="python",
        explain="Idempotent constraint creation; Neo4j 5 builds a unique index per constraint.",
        mental_model="Phone books for every business key before any MERGE.",
        memory_hook="CONSTRAINT IF NOT EXISTS → UNIQUE → index.",
        blank=(
            "def create_constraints(tx) -> None:\n"
            "    for query in [\n"
            '        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.____ IS UNIQUE",\n'
            "    ]:\n"
            "        tx.____(query)"
        ),
        answers=["product_id", "run"],
        what="Ensure unique business keys exist as constraints/indexes.",
        how="session.execute_write(create_constraints) before MERGEs.",
        where="graph/populate_graph.py",
        when="Every populate_graph / promote load — not every diagnose.",
        who="ETL loader.",
        why="Fast seeks + no duplicate products.",
        sources=[
            {
                "title": "Neo4j Cypher constraints",
                "url": "https://neo4j.com/docs/cypher-manual/current/constraints/",
                "kind": "docs",
            }
        ],
        run_hint="python -m graph.populate_graph then SHOW CONSTRAINTS;",
        cypher="CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
    )
    b.add(
        "populate-order",
        S1,
        "In populate_graph, what runs first: MERGE data or create_constraints?",
        kind="concept",
        code="with driver.session() as session:\n    session.execute_write(create_constraints)\n    # then MERGE products, symptoms, …",
        language="python",
        explain="Constraints first so subsequent MERGE/MATCH use unique indexes.",
        memory_hook="Index phone book, then put people in the book.",
        blank="session.execute_write(____)\n# then MERGE …",
        answers=["create_constraints"],
        what="Load order inside populate_graph.",
        how="execute_write(create_constraints) then entity MERGEs.",
        where="populate_graph()",
        when="Bootstrap and promote.",
        who="Pipeline.",
        why="Planner can seek on first write and later reads.",
    )
    b.add(
        "merge-product",
        S1,
        "Write MERGE for a Product by product_id with a parameter.",
        code="MERGE (p:Product {product_id: $product_id})\nSET p.name = $name",
        language="cypher",
        explain="MERGE upserts using the unique key; pairs with the constraint.",
        blank="MERGE (p:Product {product_id: $____})\nSET p.name = $name",
        answers=["product_id"],
        what="Idempotent product upsert.",
        how="MERGE on constrained property + SET other props.",
        where="populate_graph product loop.",
        when="Each product in catalog.",
        who="Loader.",
        why="Re-runs safe; index seek on key.",
        sources=[
            {
                "title": "Neo4j MERGE",
                "url": "https://neo4j.com/docs/cypher-manual/current/clauses/merge/",
                "kind": "docs",
            }
        ],
    )
    b.add(
        "profile-seek",
        S1,
        "How do you verify the planner uses the unique index?",
        kind="pattern",
        code=(
            "PROFILE\n"
            "MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)\n"
            "RETURN fm LIMIT 5"
        ),
        language="cypher",
        explain="PROFILE shows operators; look for NodeUniqueIndexSeek (or similar) on Product, not NodeByLabelScan.",
        memory_hook="PROFILE = truth about db hits.",
        what="Query plan inspection for index use.",
        how="Prefix PROFILE/EXPLAIN in Browser or driver.",
        where="Neo4j Browser on prod/staging.",
        when="When diagnose feels slow or after schema change.",
        who="Engineers.",
        why="Prove indexes are used on the hot path.",
        run_hint="http://localhost:7474 — paste PROFILE query with a real product_id.",
        sources=[
            {
                "title": "Neo4j query tuning",
                "url": "https://neo4j.com/docs/cypher-manual/current/query-tuning/",
                "kind": "docs",
            }
        ],
    )

    S2 = "Beat 2: Delta stepping (ABox)"
    b.add(
        "entity-delta",
        S2,
        "What does entity_delta compute?",
        kind="concept",
        explain="Per-product comparison of catalog ABox entities vs Neo4j (symptoms, FMs, steps, parts, …) → NEW/needs work/in_sync.",
        code="# graph/enterprise_pipeline/entity_delta.py\ndelta = compute_product_entity_delta('esp-001', compare_env='production')",
        language="python",
        mental_model="Diff two shelves: JSON catalog vs live graph.",
        memory_hook="entity_delta = what is actually NEW for this product.",
        blank="delta = compute_product_entity_delta('esp-001', compare_env='____')",
        answers=["production"],
        what="Entity-level ABox diff catalog ↔ Neo4j.",
        how="build_selection_entity_deltas(product_ids, compare_env=…).",
        where="entity_delta.py; Admin entity-delta API.",
        when="After Fetch / before promote selection.",
        who="Operator + control plane.",
        why="Selection-scoped promote without reloading the fleet.",
        run_hint="Admin UI or GET /admin/pipeline/entity-delta",
    )
    b.add(
        "delta-chant",
        S2,
        "Recite the delta promote chant.",
        kind="concept",
        explain="Fetch → Select → Validate ABox → Materialize → Smoke → Approve → Promote staging → Promote production → Invalidate caches.",
        memory_hook="FSVM SAP SP I — Fetch Select Validate Materialize Smoke Approve Stage Prod Invalidate.",
        what="Operator sequence for safe knowledge delta.",
        how="Admin wizard / control-plane pipelines.",
        where="UI Admin; docs/25 and docs/22.",
        when="Every NEW/UPDATE pack.",
        who="Knowledge operator.",
        why="Fail-closed path; chat never reads staging.",
        blank="Fetch → Select → ____ ABox → Materialize → Smoke → Promote staging → Promote production",
        answers=["Validate"],
    )

    S3 = "Beat 3: Partitioning & concurrency"
    b.add(
        "partition-key",
        S3,
        "Write a partition key helper for tenant + optional product.",
        kind="block",
        code=(
            "def partition_key(tenant_id: str, product_id: str | None = None) -> str:\n"
            "    parts = [f'tenant={tenant_id or \"default\"}']\n"
            "    if product_id:\n"
            "        parts.append(f'product={product_id}')\n"
            "    return '|'.join(parts)"
        ),
        language="python",
        explain="Same key language for rate limits and caches; work partition uses product_ids lists.",
        blank="return '____'.join(parts)",
        answers=["|"],
        what="Logical multi-tenant/product key.",
        how="runtime/partitioning.py",
        where="Rate limit middleware, cache namespaces.",
        when="Every multi-tenant request.",
        who="API runtime.",
        why="Prevent cross-tenant bleed in limits/cache.",
    )
    b.add(
        "parallel-map",
        S3,
        "Write bounded parallel_map for connector fetch.",
        kind="block",
        code=(
            "from concurrent.futures import ThreadPoolExecutor\n\n"
            "def parallel_map(items, fn, max_workers=4):\n"
            "    with ThreadPoolExecutor(max_workers=max_workers) as pool:\n"
            "        return list(pool.map(fn, items))"
        ),
        language="python",
        explain="I/O fan-out only; ranking stays serial. See runtime/concurrency.py.",
        blank="with ThreadPoolExecutor(max_workers=____) as pool:\n    return list(pool.map(fn, items))",
        answers=["4"],
        what="Bounded thread pool for independent I/O.",
        how="ThreadPoolExecutor + max_workers.",
        where="Connector extract paths.",
        when="Multiple PIM/FSM/Claims/CRM fetches.",
        who="ETL.",
        why="Faster waits without connection storms.",
        sources=[
            {
                "title": "Python concurrent.futures",
                "url": "https://docs.python.org/3/library/concurrent.futures.html",
                "kind": "docs",
            }
        ],
    )
    b.add(
        "admission",
        S3,
        "What is diagnose admission control?",
        kind="concept",
        explain="Cap in-flight expensive /diagnose calls (default 32); reject when full; always release in finally. concurrency_limit.py.",
        mental_model="Nightclub bouncer for Neo4j.",
        memory_hook="Acquire → work → finally release.",
        what="Bulkhead for diagnose concurrency.",
        how="ConcurrencyLimiter.from_settings; Redis optional for multi-pod.",
        where="api/main.py middleware/diagnose path.",
        when="Every diagnose under load.",
        who="API platform.",
        why="Protect p99 and Bolt pool.",
        sources=[
            {
                "title": "Google SRE — handling overload",
                "url": "https://sre.google/sre-book/handling-overload/",
                "kind": "docs",
            }
        ],
    )
    b.add(
        "sharding-status",
        S3,
        "Is Neo4j Fabric multi-shard deployed in this demo?",
        kind="concept",
        explain="No. AS_BUILT non-claim. Logical product_id scope prepares for product-line shards later.",
        memory_hook="Fabric = later; product scope = now.",
        what="Physical graph sharding status.",
        how="Would use composite DBs + route by product map.",
        where="Not in compose; see docs/25 §10.",
        when="Only if single DB cannot meet storage/CPU SLOs.",
        who="Platform architects.",
        why="Sharding graphs is hard; wrong key destroys multi-hop queries.",
        sources=[
            {
                "title": "Neo4j composite databases",
                "url": "https://neo4j.com/docs/operations-manual/current/scalability/composite-databases/concepts/",
                "kind": "docs",
            }
        ],
    )

    S4 = "Beat 4: Retrieval path"
    b.add(
        "retrieve-with-index",
        S4,
        "Write product-scoped MATCH that should use the unique index.",
        kind="block",
        code=(
            "MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)\n"
            "OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\n"
            "WHERE s.symptom_id IN $symptom_ids\n"
            "RETURN fm.failure_mode_id AS id, sum(coalesce(ind.confidence, 0)) AS score\n"
            "ORDER BY score DESC"
        ),
        language="cypher",
        explain="Index seek on Product, then expand; symptom filter uses ids (also unique).",
        blank="MATCH (p:Product {product_id: $____})-[:CAN_HAVE]->(fm:FailureMode)",
        answers=["product_id"],
        what="Hot GraphRAG retrieval skeleton — product-scoped multi-hop ranking seed.",
        how="Parameterized Cypher; unique index seek on product_id then relationship expand.",
        where="graph_rag / diagnose path after product resolve.",
        when="Every diagnosis with a known product.",
        who="GraphRAG runtime.",
        why="Scope + index = speed and product-local accuracy (no fleet-wide scan).",
        pitfalls=[
            "Leaving out product_id forces wider scans.",
            "f-stringing product_id into Cypher (injection + plan cache miss).",
        ],
        sources=[
            {
                "title": "Neo4j query tuning",
                "url": "https://neo4j.com/docs/cypher-manual/current/query-tuning/",
                "kind": "docs",
            }
        ],
        run_hint="PROFILE the query in Browser with a real product_id from the catalog.",
    )
    b.add(
        "show-indexes",
        S4,
        "Write the two Cypher commands that list constraints and indexes.",
        kind="line",
        code="SHOW CONSTRAINTS;\nSHOW INDEXES;",
        language="cypher",
        explain="Operational proof that create_constraints ran and unique indexes exist.",
        blank="SHOW ____;\nSHOW ____;",
        answers=["CONSTRAINTS", "INDEXES"],
        what="Catalog introspection for uniqueness and index objects.",
        how="Run in Neo4j Browser or via driver session.run.",
        where="Prod :7474 / staging :7475 after populate or promote.",
        when="After every bootstrap or schema change.",
        who="Operators and engineers verifying load.",
        why="Without unique indexes, MERGE and MATCH degrade and duplicates slip in.",
        sources=[
            {
                "title": "Neo4j Cypher Manual — SHOW CONSTRAINTS",
                "url": "https://neo4j.com/docs/cypher-manual/current/listing/constraints/",
                "kind": "docs",
            }
        ],
        run_hint="http://localhost:7474 → paste both commands.",
    )
    b.add(
        "full-constraint-list",
        S1,
        "Name the main entity keys that get UNIQUE constraints in create_constraints.",
        kind="concept",
        explain=(
            "product_id, symptom_id, failure_mode_id, step_id, part_id, resolution_id, "
            "model_id, sku_id, component_id, error_code_id, asset_id, policy_id, claim_id."
        ),
        mental_model="Every business noun that can be MERGEd needs a unique name tag.",
        memory_hook="Products, symptoms, FMs, steps, parts, resolutions, models, SKUs, components, codes, assets, policies, claims.",
        blank="CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.____ IS UNIQUE",
        answers=["product_id"],
        what="Complete set of unique business keys created by populate_graph.create_constraints.",
        how="One CREATE CONSTRAINT IF NOT EXISTS … REQUIRE … IS UNIQUE per label/key.",
        where="graph/populate_graph.py lines in create_constraints(tx).",
        when="Every populate_graph / promote load before entity MERGEs.",
        who="ETL loader.",
        why="Index-backed seeks + no duplicate fleet entities on re-load.",
        code=(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE\n"
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE\n"
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fm:FailureMode) REQUIRE fm.failure_mode_id IS UNIQUE\n"
            "# … Part, Asset, Claim, ErrorCode, …"
        ),
        language="cypher",
        pitfalls=["Creating constraints after bad duplicate data already exists (constraint create fails)"],
        sources=[
            {
                "title": "docs/19-Indexes-Constraints-and-Lookup-Performance.md",
                "kind": "docs",
            },
            {
                "title": "docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md",
                "kind": "docs",
            },
        ],
        run_hint="python -m graph.populate_graph && SHOW CONSTRAINTS;",
    )
    b.add(
        "end-to-end-chant",
        "Mental models",
        "Recite the scale path: index → delta → partition → concurrency → (optional) shard.",
        kind="concept",
        explain=(
            "1) Unique indexes for identity seeks. 2) Selection-scoped ABox delta promote. "
            "3) Logical tenant|product keys. 4) Bounded threads + admission. "
            "5) Fabric shards only if one DB cannot scale."
        ),
        mental_model="Phone book → restock changed boxes → labeled shelves → nightclub bouncer → extra warehouses only if needed.",
        memory_hook="Seek → Delta → Key → Cap → Shard-later.",
        what="Ordered adoption of scale capabilities in this product.",
        how="Operate docs/25 §14 order; never invent Fabric claims in demos.",
        where="AS_BUILT + docs/25 + Study Lab Masters mc-03.",
        when="Interviews, demos, and production hardening roadmap.",
        who="Platform + knowledge ops.",
        why="Wrong order (shard first) destroys multi-hop queries and ops simplicity.",
        blank="Seek → ____ → Key → Cap → Shard-later",
        answers=["Delta"],
        sources=[
            {"title": "docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md", "kind": "docs"},
            {"title": "docs/sdd/AS_BUILT.md", "kind": "docs"},
        ],
        run_hint="Study Lab → Masters → Graph Ops → Flashcards → Mental models.",
    )

    return b.cards


# ══════════════════════════════════════════════════════════════════════════
# GUIDE 4 — Scaling & Populating the KG (traversal, scale, pipeline, infra)
# ══════════════════════════════════════════════════════════════════════════
def _build_scaling_populate() -> list[MemoryCard]:
    b = _Builder("mc-04-scaling-populating-kg")

    # ---- Mental models / the story ----
    S0 = "Mental models & memory hooks"
    b.add(
        "chant",
        S0,
        "Recite the 4-part chant for scaling & populating the KG.",
        kind="concept",
        explain="Part 1 traversal → Part 2 scale → Part 3 pipeline → Part 4 infra.",
        mental_model="Choose the right path, scale the boring way first, feed with strong+weak+validate, then package/gate/run.",
        memory_hook='"Weighted-path → Scale-boring-first → Strong+Weak+Validate → Docker-gate-run."',
    )
    b.add(
        "two-tiers",
        S0,
        "The two tiers of shortest path in Neo4j?",
        kind="concept",
        explain="Native Cypher shortestPath()/allShortestPaths() ship built in (unweighted, BFS, fewest hops). GDS library (installed separately) has the weighted algorithms (Dijkstra, Delta-Stepping, A*, Yen's).",
        mental_model="Built-in = 'is there any path?'. GDS = 'what's the cheapest route?'.",
        memory_hook="Native = hops. GDS = cost.",
    )
    b.add(
        "projection-gotcha",
        S0,
        "The #1 GDS trip-up?",
        kind="concept",
        explain="GDS algorithms run on an in-memory graph PROJECTION, not the live store. You must gds.graph.project(...) before any algorithm call.",
        mental_model="GDS works on a photocopy of the shape, not the original filing cabinet.",
        memory_hook="Project → run → drop. Forget project = 'my GDS query doesn't work'.",
    )
    b.add(
        "scale-order",
        S0,
        "The order you reach for scaling levers?",
        kind="concept",
        explain="Vertical (page cache) → read replicas → three caching layers → property sharding/composite DB LAST.",
        mental_model="Bigger machine before more machines; shard only when nothing else is left.",
        memory_hook="Page → Replica → Cache → Shard-last.",
    )
    b.add(
        "strong-weak",
        S0,
        "Strong node vs weak node?",
        kind="concept",
        explain="Strong = verified, from a system of record (structured data). Weak = plausible, schema-constrained, from LLM/unstructured text — unverified until a resolution pass merges it into a strong node.",
        mental_model="Strong = official catalog entry; weak = a technician's scribbled note until confirmed.",
        memory_hook="Strong = system of record. Weak = needs confirming.",
    )
    b.add(
        "three-tools",
        S0,
        "Docker vs GitHub Actions vs Kubernetes — one job each?",
        kind="concept",
        explain="Docker PACKAGES (Neo4j + pipeline code). GitHub Actions GATES (merge-blocking ontology/eval/build). Kubernetes RUNS (StatefulSet core + read replicas + ingestion CronJob).",
        mental_model="Package → Gate → Run.",
        memory_hook="Docker packs, Actions gates, K8s runs.",
    )

    # ---- PART 1: Traversal ----
    S1 = "Part 1 — Traversal & shortest path"
    b.add(
        "native-shortestpath",
        S1,
        "Write a native Cypher reachability check (fewest hops).",
        kind="block",
        code=(
            "MATCH (s:Symptom {symptom_id: $symptom_id}), (r:Resolution)\n"
            "MATCH path = shortestPath((s)-[*..6]-(r))\n"
            "RETURN path\n"
            "LIMIT 1"
        ),
        language="cypher",
        explain="shortestPath() is built in, unweighted (BFS) — answers 'is there ANY path at all?', not the cheapest one.",
        mental_model="A maze solver that counts doors, not effort.",
        memory_hook="shortestPath = fewest hops, no install.",
        what="Native, unweighted reachability between two nodes.",
        how="shortestPath((a)-[*..N]-(b)) with a bounded var-length pattern.",
        where="Any Neo4j install — no plugin.",
        when="You only need 'connected or not', not a ranked/cheapest route.",
        who="Query author.",
        why="Cheapest to run; no GDS/projection needed.",
        blank="MATCH path = ____((s)-[*..6]-(r)) RETURN path LIMIT 1",
        answers=["shortestPath"],
        pitfalls=[
            "Unbounded var-length (no ..N cap) can explode.",
            "It is fewest hops, NOT lowest cost — don't use it for cheapest-route questions.",
        ],
        sources=[
            {
                "title": "Neo4j Cypher Manual — Shortest Paths",
                "url": "https://neo4j.com/docs/cypher-manual/current/patterns/shortest-paths/",
                "kind": "docs",
            },
        ],
        run_hint="[REFERENCE] not on the diagnose hot path in this repo.",
    )
    b.add(
        "gds-project",
        S1,
        "Write the GDS graph projection (step that MUST come first).",
        kind="block",
        code=(
            "CALL gds.graph.project(\n"
            "  'diag',\n"
            "  ['Symptom','FailureMode','DiagnosticStep','Resolution'],\n"
            "  {\n"
            "    INDICATES: { properties: 'cost' },\n"
            "    CONFIRMS:  { properties: 'cost' },\n"
            "    LEADS_TO:  { properties: 'cost' }\n"
            "  }\n"
            ");"
        ),
        language="cypher",
        explain="GDS runs on an in-memory projection, not the live store. Name it, list node labels + weighted rel types, then run algorithms against the name.",
        mental_model="Load the sub-shape into a workbench before machining it.",
        memory_hook="Project first, or GDS 'doesn't work'.",
        what="In-memory GDS graph projection with a weight property.",
        how="gds.graph.project(name, labels, relConfig-with-properties).",
        where="Requires GDS library installed (not bundled).",
        when="Before ANY gds.* algorithm call.",
        who="Graph analyst / platform.",
        why="Algorithms operate on projections, not stored graphs.",
        blank="CALL gds.graph.____('diag', [...], {...});",
        answers=["project"],
        pitfalls=[
            "Forgetting to drop the projection leaks memory.",
            "Projecting the whole graph when you only need a sub-shape.",
        ],
        sources=[
            {
                "title": "Neo4j GDS — Graph Catalog / project",
                "url": "https://neo4j.com/docs/graph-data-science/current/management-ops/graph-creation/",
                "kind": "docs",
            },
        ],
        run_hint="[REFERENCE] GDS not installed in this repo (APOC only).",
    )
    b.add(
        "gds-dijkstra",
        S1,
        "Write weighted Dijkstra source→target (cheapest diagnostic route).",
        kind="block",
        code=(
            "MATCH (src:Symptom {symptom_id: $symptom_id}),\n"
            "      (dst:Resolution {resolution_id: $resolution_id})\n"
            "CALL gds.shortestPath.dijkstra.stream('diag', {\n"
            "  sourceNode: src, targetNode: dst,\n"
            "  relationshipWeightProperty: 'cost'\n"
            "})\n"
            "YIELD totalCost, nodeIds\n"
            "RETURN totalCost,\n"
            "  [id IN nodeIds | gds.util.asNode(id).name] AS route;"
        ),
        language="cypher",
        explain="Weighted shortest path: 'cost' = technician time / part cost / difficulty. The cheapest route and the fewest-hops route are frequently DIFFERENT paths.",
        mental_model="A sat-nav optimizing for fuel, not distance.",
        memory_hook="Dijkstra = cheapest, single-threaded.",
        what="Source-target weighted shortest path over a projection.",
        how="gds.shortestPath.dijkstra.stream(graph, {source,target,weightProp}).",
        where="On a projection created by gds.graph.project.",
        when="You care about lowest total cost, not hop count.",
        who="Analyst / diagnostics optimizer.",
        why="Fastest (fewest-hop) ≠ cheapest (least time/cost) route.",
        pitfalls=[
            "GDS Dijkstra is single-threaded regardless of concurrency config.",
            "Needs the projection + a weight property on the relationships.",
        ],
        sources=[
            {
                "title": "Neo4j GDS — Dijkstra Source-Target",
                "url": "https://neo4j.com/docs/graph-data-science/current/algorithms/dijkstra-source-target/",
                "kind": "docs",
            },
        ],
        run_hint="[REFERENCE] correct pattern to add if a cheapest-route feature is prioritised.",
    )
    b.add(
        "delta-stepping-parallel",
        S1,
        "Which algorithm gives PARALLEL single-source shortest paths (not Dijkstra)?",
        kind="concept",
        explain="Delta-Stepping SSSP. GDS's Dijkstra runs single-threaded no matter how much concurrency you configure; Delta-Stepping is the parallel answer for single-source shortest paths at scale.",
        mental_model="Same destination map, many workers filling it in at once.",
        memory_hook="Need parallel SSSP? Switch algorithm (Delta-Stepping), not a flag.",
        what="Parallel single-source shortest paths.",
        how="gds.allShortestPaths.deltaStepping over a projection.",
        where="GDS library.",
        when="Large graph, need single-source shortest paths FAST.",
        who="Analyst.",
        why="Dijkstra is single-threaded; concurrency config won't parallelize it.",
        blank="Parallel SSSP = ____-Stepping, not a config flag on Dijkstra.",
        answers=["Delta"],
        sources=[
            {
                "title": "Neo4j GDS — Delta-Stepping",
                "url": "https://neo4j.com/docs/graph-data-science/current/algorithms/delta-single-source/",
                "kind": "docs",
            },
        ],
        run_hint="Contrast with the ABox 'delta stepping' in mc-03 (different meaning).",
    )
    b.add(
        "repo-hot-path",
        S1,
        "How does THIS repo actually traverse for a diagnosis?",
        kind="block",
        code=(
            "MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)\n"
            "OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\n"
            "WHERE s.symptom_id IN $symptom_ids\n"
            "RETURN fm.failure_mode_id AS id,\n"
            "       sum(coalesce(ind.confidence, 0)) AS score\n"
            "ORDER BY score DESC"
        ),
        language="cypher",
        explain="Bounded, parameterized, product-scoped multi-hop MATCH — unique index seek on Product, expand product-local edges, score in Python. No shortestPath()/GDS.",
        mental_model="Start at a known house and walk its street — not search the whole city for a path.",
        memory_hook="Seek product → expand edges → rank in Python.",
        what="The as-built diagnosis retrieval pattern.",
        how="Index-seek the product, expand INDICATES, sum confidence.",
        where="graph/graph_rag.py.",
        when="Every /diagnose request.",
        who="GraphRAG runtime.",
        why="The question is 'rank failure modes', not 'find a path'.",
        pitfalls=["Don't claim GDS/Delta-stepping shortest-path is on this path — it isn't."],
        sources=[
            {"title": "docs/17-Enterprise-Landscape-Pipeline-and-Topology.md", "kind": "docs"},
            {"title": "docs/sdd/AS_BUILT.md", "kind": "docs"},
        ],
        run_hint="[AS-BUILT] POST /diagnose in this repo.",
    )

    # ---- PART 2: Scaling ----
    S2 = "Part 2 — Scaling for high volume"
    b.add(
        "page-cache",
        S2,
        "The single most important Neo4j scaling lever, and its config?",
        kind="block",
        code=(
            "# neo4j.conf (reference tuning)\n"
            "server.memory.pagecache.size=8g\n"
            "server.memory.heap.initial_size=4g\n"
            "server.memory.heap.max_size=4g"
        ),
        language="bash",
        explain="The page cache is Neo4j's in-memory cache of the store files — it decides whether a query reads from RAM (fast) or disk (slow). Size it to the working set BEFORE clustering or sharding.",
        mental_model="Keep the whole active dataset in RAM; a well-tuned single node beats a badly-tuned cluster.",
        memory_hook="RAM first. Page cache = working set in memory.",
        what="Vertical scaling via page-cache sizing.",
        how="server.memory.pagecache.size in neo4j.conf.",
        where="neo4j.conf (REFERENCE — untuned in the demo container).",
        when="Before any clustering/sharding decision.",
        who="Operator.",
        why="RAM vs disk is the dominant latency factor.",
        blank="server.memory.____.size=8g",
        answers=["pagecache"],
        sources=[
            {
                "title": "Neo4j Operations Manual — Memory configuration",
                "url": "https://neo4j.com/docs/operations-manual/current/performance/memory-configuration/",
                "kind": "docs",
            },
        ],
        run_hint="[REFERENCE] demo runs a single untuned container.",
    )
    b.add(
        "core-replica",
        S2,
        "Describe the Core-Replica cluster (read scaling).",
        kind="concept",
        explain="Core servers hold authoritative data with Raft consensus for writes — deploy an ODD number (3 min) for quorum. Read replicas hold async copies, serve reads, take no part in write consensus → near-infinite horizontal read scale.",
        mental_model="A few trusted signatories (cores) + many photocopiers (replicas) for reading.",
        memory_hook="Odd cores for quorum; replicas for reads.",
        what="Neo4j HA topology for read scaling + fault tolerance.",
        how="3+ cores (Raft) for writes; N replicas for reads behind a load balancer.",
        where="REFERENCE — this repo is single prod + separate staging (env partition, not HA).",
        when="One machine's read capacity is the bottleneck.",
        who="Platform/ops.",
        why="Reads scale horizontally without risking write consistency.",
        blank="Always deploy an ____ number of core servers (3 minimum) for quorum.",
        answers=["odd"],
        pitfalls=["Even core count can't maintain a clean quorum.", "[NON-CLAIM] this repo has no causal cluster HA."],
        sources=[
            {
                "title": "Neo4j Ops Manual — Clustering introduction",
                "url": "https://neo4j.com/docs/operations-manual/current/clustering/introduction/",
                "kind": "docs",
            },
        ],
        run_hint="Say: single prod :7687 + staging :7688 = environment partition, not HA.",
    )
    b.add(
        "causal-bookmark",
        S2,
        "Write read-your-writes with a causal bookmark.",
        kind="block",
        code=(
            "with driver.session() as w:\n"
            '    w.run("MERGE (p:Product {product_id:$id}) SET p.name=$n", id="wm-001", n="Washer")\n'
            "    bookmarks = w.last_bookmarks()\n"
            "with driver.session(bookmarks=bookmarks) as r:  # guaranteed to see the write\n"
            '    r.run("MATCH (p:Product {product_id:$id}) RETURN p", id="wm-001")'
        ),
        language="python",
        explain="Causal consistency: a writer gets a bookmark; a reader using that bookmark is guaranteed to reflect at least that write — so scaling reads across replicas never shows a user stale data after their own change.",
        mental_model="A receipt that proves your change landed before you go read it back.",
        memory_hook="Write → bookmark → read-your-writes.",
        what="Causal-consistency bookmark chaining.",
        how="session.last_bookmarks() → session(bookmarks=...).",
        where="Neo4j driver (REFERENCE — needs a cluster to matter).",
        when="Read-after-write across replicas.",
        who="App developer.",
        why="Prevents stale reads after a user's own write.",
        blank="bookmarks = w.____()  # then session(bookmarks=bookmarks)",
        answers=["last_bookmarks"],
        sources=[
            {
                "title": "Neo4j — Causal consistency / bookmarks",
                "url": "https://neo4j.com/docs/operations-manual/current/clustering/introduction/",
                "kind": "docs",
            },
        ],
        run_hint="[REFERENCE] single-node demo does not need bookmarks.",
    )
    b.add(
        "three-caches",
        S2,
        "Name the three distinct caching layers.",
        kind="concept",
        explain="(1) Page cache — Neo4j's store-file cache. (2) Read replicas acting as warm 'graph caches' that also run read Cypher. (3) Cache sharding — route each request to the member that already has that slice warm.",
        mental_model="Don't conflate them: RAM cache, replica-as-cache, and warm-routing are three things.",
        memory_hook="Page · Replica · Shard-route.",
        what="The three-layer caching model.",
        how="Tune page cache; add replicas; route by warm slice.",
        where="REFERENCE (cluster) + app TTL cache is the repo's practical 3rd layer.",
        when="Progressively as read load grows.",
        who="Ops + platform.",
        why="Conflating them is a common design mistake.",
        pitfalls=["Cache sharding trades even load for higher hit rate — only worth it with natural partitions."],
        sources=[
            {"title": "docs/16-Enterprise-Runtime-Capabilities.md", "kind": "docs"},
            {"title": "docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md", "kind": "docs"},
        ],
        run_hint="Repo's real caching layer = runtime/cache.py (next card).",
    )
    b.add(
        "app-cache",
        S2,
        "Write the as-built application TTL cache usage.",
        kind="block",
        code=(
            "from runtime.cache import get_named_cache, invalidate_all_named_caches\n\n"
            'cache = get_named_cache("product_subgraph", ttl_seconds=60, maxsize=128)\n'
            'data = cache.get_or_set("wm-001", lambda: expensive_load("wm-001"))\n'
            "# after an ETL load, drop stale hot reads:\n"
            "invalidate_all_named_caches()"
        ),
        language="python",
        explain="Named TTL cache (memory, or Redis when REDIS_URL set) for stable reads: ontology 300s, subgraphs 60s. Invalidated after every successful ETL load so a catalog change never serves stale parts/warranty.",
        mental_model="Sticky notes for answers that rarely change; peel them all off after a data reload.",
        memory_hook="get_or_set to read; invalidate after load.",
        what="Application-layer request cache (3rd caching layer, as-built).",
        how="get_named_cache(...).get_or_set(key, loader); invalidate on load.",
        where="runtime/cache.py.",
        when="Stable GETs (schema, product subgraphs).",
        who="API runtime.",
        why="Cuts repeated Neo4j/CPU for hot reads; Redis shares it across pods.",
        blank='cache.____("wm-001", lambda: expensive_load("wm-001"))',
        answers=["get_or_set"],
        pitfalls=[
            "Never cache free-text diagnosis without a full key (message+product+asset+policy+batch) — wrong-answer + privacy risk."
        ],
        sources=[
            {"title": "docs/16-Enterprise-Runtime-Capabilities.md", "kind": "docs"},
        ],
        run_hint="[AS-BUILT] GET /health shows cache stats + redis mode.",
    )
    b.add(
        "why-sharding-hard",
        S2,
        "Why is graph sharding harder than relational sharding? What's the modern answer?",
        kind="concept",
        explain="Relational rows are mostly independent so they shard cleanly; a graph's value IS the connections, so a naive split forces cross-network hops on every traversal. Modern Neo4j: PROPERTY sharding keeps nodes+relationships together (only shards heavy property data); COMPOSITE databases (ex-Fabric) federate genuinely distinct domains.",
        mental_model="Don't cut the roads between houses; only distribute the furniture inside them.",
        memory_hook="Structure stays local; only properties/domains split.",
        what="Graph sharding difficulty + property sharding / composite DB.",
        how="Property sharding (Infinigraph) vs composite databases (federation).",
        where="REFERENCE / [NON-CLAIM] — not deployed here.",
        when="Only after vertical + replicas are genuinely exhausted.",
        who="Architect.",
        why="Naive sharding destroys traversal locality — the reason to use a graph DB.",
        pitfalls=[
            "Most teams shard too early and pay complexity for nothing.",
            "[NON-CLAIM] no Fabric/composite shards in this repo.",
        ],
        sources=[
            {
                "title": "Neo4j — Composite databases (concepts)",
                "url": "https://neo4j.com/docs/operations-manual/current/database-administration/composite-databases/concepts/",
                "kind": "docs",
            },
        ],
        run_hint="Natural shard key here = product line / brand / region.",
    )
    b.add(
        "partition-keys",
        S2,
        "Write the as-built logical partition key helper.",
        kind="block",
        code=(
            "# runtime/partitioning.py\n"
            'def partition_for_request(*, tenant_id="default", product_id=None, **_):\n'
            "    bits = [f\"tenant={tenant_id or 'default'}\"]\n"
            "    if product_id:\n"
            '        bits.append(f"product={product_id}")\n'
            '    return "|".join(bits)   # e.g. "tenant=acme|product=wm-001"'
        ),
        language="python",
        explain="Logical partition KEYS (not physical shards) shared by rate-limit buckets and cache namespaces. Prepares multi-tenant SaaS with stable keys without rewriting handlers.",
        mental_model="One naming language so limits, caches, and lineage all agree who owns a request.",
        memory_hook="tenant=…|product=… — logical, not physical.",
        what="Logical partitioning via canonical keys.",
        how="Build a 'tenant=…|product=…' string for cache/rate namespaces.",
        where="runtime/partitioning.py.",
        when="Every multi-tenant request / cache / rate-limit lookup.",
        who="API platform.",
        why="No cross-tenant bleed in limits/cache; enables later physical shards.",
        blank='return "|".join(bits)  # "tenant=acme|____=wm-001"',
        answers=["product"],
        pitfalls=[
            "Keys are NOT security — enforce auth separately.",
            "[NON-CLAIM] no hard tenant ACL / Fabric multi-DB.",
        ],
        sources=[{"title": "docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md", "kind": "docs"}],
        run_hint="[AS-BUILT] same key language for rate limit + cache.",
    )
    b.add(
        "bounded-parallel",
        S2,
        "Write the bounded parallel-extract helper + the concurrency rule.",
        kind="block",
        code=(
            "# runtime/concurrency.py\n"
            "from concurrent.futures import ThreadPoolExecutor\n\n"
            "def parallel_map(items, fn, max_workers=4, preserve_order=True):\n"
            "    with ThreadPoolExecutor(max_workers=max_workers) as ex:\n"
            "        return list(ex.map(fn, items))"
        ),
        language="python",
        explain="Concurrency lives at two layers: inside one algorithm (choose Delta-Stepping over Dijkstra) and across requests (bounded thread pools + replicas). Parallelize connector fetch; keep Bayes ranking serial.",
        mental_model="Many workers fetch from 4 systems at once; one diagnosis is scored by a single careful worker.",
        memory_hook="Parallel extract, serial transform, sequential load.",
        what="Bounded I/O parallelism for connector extract.",
        how="ThreadPoolExecutor(max_workers) → ex.map.",
        where="runtime/concurrency.py; admission in concurrency_limit.py.",
        when="Independent connector fetches; NOT single-diagnosis ranking.",
        who="ETL runtime.",
        why="Hide I/O latency; protect Bolt pool + upstream rate limits.",
        blank="def parallel_map(items, fn, max_workers=4, ...):  # bounded ____",
        answers=["max_workers"],
        pitfalls=[
            "Unbounded fan-out can DDoS Neo4j / SaaS APIs.",
            "[NON-CLAIM] multi-threading does NOT speed up Bayes ranking here.",
        ],
        sources=[
            {
                "title": "Python concurrent.futures",
                "url": "https://docs.python.org/3/library/concurrent.futures.html",
                "kind": "docs",
            },
            {
                "title": "Google SRE — Handling overload",
                "url": "https://sre.google/sre-book/handling-overload/",
                "kind": "docs",
            },
        ],
        run_hint="[AS-BUILT] wraps connector fetch in the ETL extract stage.",
    )

    # ---- PART 3: Pipeline ----
    S3 = "Part 3 — Structured / semi / unstructured → graph"
    b.add(
        "structured-loadcsv",
        S3,
        "Write the structured LOAD CSV mapping (row → node).",
        kind="block",
        code=(
            "LOAD CSV WITH HEADERS FROM 'file:///error_codes.csv' AS row\n"
            "MERGE (e:ErrorCode {error_code_id: row.code})\n"
            "SET e.description = row.description"
        ),
        language="cypher",
        explain="Structured = rows/columns already. Neo4j-ETL infers a model from FK structure; LOAD CSV (+APOC for batching/typing) is the simplest batch import. Mapping is mechanical: model row → :Product, fault row → :ErrorCode, FK → relationship.",
        mental_model="Spreadsheet rows walk straight in as nodes.",
        memory_hook="Row → MERGE node; FK → relationship.",
        what="Structured batch import.",
        how="LOAD CSV WITH HEADERS → MERGE on a business key → SET props.",
        where="REFERENCE; repo uses connectors → populate_graph MERGE.",
        when="One-time / scheduled batch of clean tabular data.",
        who="ETL.",
        why="Deterministic, mechanical, high-confidence (strong nodes).",
        blank="LOAD CSV WITH HEADERS FROM '...' AS row\\nMERGE (e:ErrorCode {error_code_id: row.____})",
        answers=["code"],
        pitfalls=["Pair MERGE with a uniqueness constraint or you get duplicates."],
        sources=[
            {
                "title": "Neo4j — LOAD CSV",
                "url": "https://neo4j.com/docs/cypher-manual/current/clauses/load-csv/",
                "kind": "docs",
            },
        ],
        run_hint="[AS-BUILT] repo structured path = connectors → populate_graph.",
    )
    b.add(
        "semi-apoc",
        S3,
        "Write the semi-structured APOC JSON load + name the repo extractor.",
        kind="block",
        code=(
            "CALL apoc.load.json('file:///work_orders.json') YIELD value\n"
            "MERGE (w:WorkOrder {work_order_id: value.id})\n"
            "SET w.status = value.status"
        ),
        language="cypher",
        explain="Semi-structured = JSON/XML/telemetry/tickets. APOC JSON/XML procedures parse nested shapes LOAD CSV can't; Kafka + Neo4j sink handles continuous streams. Repo extractor: extractors/semi_structured.py (work_orders.jsonl, parts_delta.csv).",
        mental_model="Nested boxes that APOC unpacks into flat nodes.",
        memory_hook="APOC for JSON/XML; Kafka for streams.",
        what="Semi-structured ingestion.",
        how="apoc.load.json/xml → MERGE; or Kafka sink for streams.",
        where="graph/enterprise_pipeline/extractors/semi_structured.py.",
        when="Nested files or continuous event feeds.",
        who="ETL.",
        why="Handles structure LOAD CSV alone can't.",
        blank="CALL apoc.load.____('file:///work_orders.json') YIELD value",
        answers=["json"],
        sources=[
            {
                "title": "Neo4j APOC — Load JSON",
                "url": "https://neo4j.com/docs/apoc/current/import/load-json/",
                "kind": "docs",
            },
        ],
        run_hint="[AS-BUILT] semi_structured.py normalizes rows → staging JSON.",
    )
    b.add(
        "unstructured-schema-bound",
        S3,
        "Write the schema-BOUND LLM extractor (the critical practice).",
        kind="block",
        code=(
            "from langchain_experimental.graph_transformers import LLMGraphTransformer\n\n"
            "transformer = LLMGraphTransformer(\n"
            "    llm=llm,\n"
            '    allowed_nodes=["Product", "ErrorCode", "Symptom", "DiagnosticStep", "Resolution"],\n'
            '    allowed_relationships=["CAN_EXHIBIT", "MAY_INDICATE", "CONFIRMED_BY", "LEADS_TO"],\n'
            ")\n"
            "docs = transformer.convert_to_graph_documents(clean_text_chunks)"
        ),
        language="python",
        explain="Unstructured (manuals, PDFs, transcripts) is the hard case. Bind the LLM to your five classes + four properties via allowed_nodes/allowed_relationships so it can ONLY propose ontology-legal triples — never an invented type. Tools ladder: llm-graph-builder → GraphRAG SimpleKGBuilder → LangChain LLMGraphTransformer → unstructured.io for clean text first.",
        mental_model="A form with only 5 dropdowns — the model can't write outside the boxes.",
        memory_hook="allowed_nodes + allowed_relationships = ontology handcuffs.",
        what="Schema-constrained LLM graph extraction.",
        how="LLMGraphTransformer(allowed_nodes=..., allowed_relationships=...).",
        where="REFERENCE; repo uses deterministic regex extractor today.",
        when="Extracting graph from free text.",
        who="Knowledge pipeline.",
        why="Free-form extraction on small models yields 'an unusable, inconsistent mess'.",
        blank="LLMGraphTransformer(llm=llm, ____=[...5 classes...], allowed_relationships=[...])",
        answers=["allowed_nodes"],
        pitfalls=[
            "[NON-CLAIM] repo extraction is regex/heuristic (unstructured_text.py), not an LLM — this is the upgrade path."
        ],
        sources=[
            {
                "title": "LangChain — LLMGraphTransformer",
                "url": "https://python.langchain.com/docs/how_to/graph_constructing/",
                "kind": "docs",
            },
            {
                "title": "Neo4j — Build KG from unstructured data",
                "url": "https://neo4j.com/developer/genai-ecosystem/importing-graph-from-unstructured-data/",
                "kind": "docs",
            },
        ],
        run_hint="[REFERENCE] pair with unstructured.io to clean text first.",
    )
    b.add(
        "strong-weak-merge",
        S3,
        "How does resolution merge weak nodes into strong ones? Repo status?",
        kind="concept",
        code=('delta = compute_product_entity_delta("esp-001", compare_env="production")'),
        language="python",
        explain="Structured → strong (verified) nodes. LLM/unstructured → weak (unverified) nodes. A resolution pass merges weak into strong for the same real-world thing ('engine idles rough' → 'rough idle') via exact/fuzzy string + embedding similarity. Repo today: identity resolution = MERGE on business key + entity_delta comparing catalog↔Neo4j.",
        mental_model="Two notes about the same fault get stapled together, not filed twice.",
        memory_hook="Strong absorbs weak; don't keep duplicates.",
        what="Strong/weak node resolution.",
        how="Exact/fuzzy + embedding match (ref); MERGE-by-key + entity_delta (as-built).",
        where="graph/enterprise_pipeline/entity_delta.py.",
        when="After combining structured + extracted outputs.",
        who="Knowledge pipeline.",
        why="Prevents confusing near-duplicate nodes.",
        pitfalls=["[NON-CLAIM] embedding/fuzzy weak-node merge is NOT implemented — dedupe is exact-key MERGE."],
        sources=[{"title": "docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md", "kind": "docs"}],
        run_hint="[AS-BUILT] entity_delta shows NEW vs IN_SYNC per product.",
    )
    b.add(
        "shacl-validate",
        S3,
        "Write the as-built shape validation + its formal SHACL equivalent.",
        kind="block",
        code=(
            "# graph/enterprise_pipeline/ontology_validate.py  (SHACL-inspired)\n"
            "MIN_SYMPTOMS = 1\n"
            "MIN_FAILURE_MODES = 1\n"
            "MIN_INDICATES_LINKS = 1   # every product needs >=1 symptom->FM with confidence"
        ),
        language="python",
        explain="Neo4j does NOT enforce OWL restrictions natively — close the gap deliberately. Check min-cardinality (every :ErrorCode has >=1 :CONFIRMED_BY), disjointness, and link referential integrity BEFORE materialize/promote. Failures go to a REVIEW QUEUE — flag, don't silently fix or drop.",
        mental_model="A bouncer at the door checking IDs before facts enter the graph.",
        memory_hook="Validate → fail-closed → review queue.",
        what="Ontology-conformance validation (SHACL-style).",
        how="In-code min-cardinality + link-integrity checks pre-promote.",
        where="graph/enterprise_pipeline/ontology_validate.py.",
        when="Before every materialize/promote (fail-closed).",
        who="Knowledge pipeline.",
        why="Catches junk/incomplete ABox before runtime trusts it.",
        blank="MIN_INDICATES_LINKS = ____   # symptom->failure_mode with confidence",
        answers=["1"],
        shacl=(
            ":ErrorCodeShape a sh:NodeShape ;\n"
            "    sh:targetClass :ErrorCode ;\n"
            "    sh:property [ sh:path :confirmedBy ; sh:minCount 1 ] ."
        ),
        pitfalls=["[NON-CLAIM] no external SHACL/OWL reasoner — lightweight in-code validator only."],
        sources=[
            {"title": "W3C SHACL", "url": "https://www.w3.org/TR/shacl/", "kind": "spec"},
        ],
        run_hint="[AS-BUILT] runs in the validate stage before promote.",
    )

    # ---- PART 4: Infra ----
    S4 = "Part 4 — Docker, GitHub Actions, Kubernetes"
    b.add(
        "docker-two-uses",
        S4,
        "The two distinct uses of Docker here?",
        kind="concept",
        explain="(1) Run Neo4j itself in a container (official image) for local dev/test. (2) Containerize your own pipeline code — ETL, extraction, validation each as their own image. Note: Neo4j Desktop does NOT support docker-compose.",
        mental_model="One image for the database, separate images for your scripts.",
        memory_hook="Neo4j image + your pipeline images.",
        what="Docker packaging for DB and pipeline code.",
        how="docker/Dockerfile.api|etl|frontend|mock|ui + docker-compose.infra.yaml.",
        where="docker/.",
        when="Local dev and image build/publish.",
        who="Everyone.",
        why="Reproducible, isolated, signable images.",
        blank="docker/docker-compose.____.yaml runs prod :7687 + staging :7688",
        answers=["infra"],
        sources=[{"title": "docs/sdd/AS_BUILT.md", "kind": "docs"}],
        run_hint="[AS-BUILT] docker compose -f docker/docker-compose.infra.yaml up -d",
    )
    b.add(
        "ci-gate",
        S4,
        "Write the merge-blocking CI gate excerpt.",
        kind="block",
        code=(
            "# .github/workflows/ci.yml\n"
            "- name: Ruff lint\n"
            "  run: ruff check .\n"
            "- name: Multi-source packs + TBox/ABox discipline (no Neo4j required)\n"
            "  run: |\n"
            "    pytest tests/test_multi_source_tbox_abox.py \\\n"
            "      tests/test_warranty_ontology.py tests/test_rdf_ontology_export.py -q"
        ),
        language="yaml",
        explain="GitHub Actions gates every ontology/query/prompt change before merge. Maps to the doc's four gates: (1) ontology validation = TBox/ABox + rdf_export pytest; (2) golden-set eval = evals/ smoke in CI; (3) scheduled ingestion = K8s CronJob; (4) Cypher/APOC changes ride the same build→test→deploy. Also: gitleaks, CodeQL, Trivy, SBOM/provenance, cosign; cd.yml eval-gate + Argo canary.",
        mental_model="Nothing merges until lint + ontology tests + eval + build all pass.",
        memory_hook="Lint → TBox tests → eval → build (merge-block).",
        what="CI/CD gate for ontology + pipeline code.",
        how="pytest TBox/ABox + eval smoke as required checks.",
        where=".github/workflows/ci.yml, cd.yml, eval-nightly.yml.",
        when="Every PR to main / feature branches.",
        who="CI.",
        why="Spec/ontology is the source of truth — regressions blocked pre-merge.",
        blank="- name: Ruff lint\\n  run: ____ check .",
        answers=["ruff"],
        pitfalls=["[NON-CLAIM] dedicated Turtle-syntax + SHACL CI job is roadmap — validation runs as pytest."],
        sources=[{"title": ".github/workflows/ci.yml", "kind": "docs"}],
        run_hint="[AS-BUILT] runs on push to main and feature/**.",
    )
    b.add(
        "k8s-statefulset",
        S4,
        "Why is Neo4j core a StatefulSet, and write the skeleton.",
        kind="block",
        code=(
            "apiVersion: apps/v1\n"
            "kind: StatefulSet\n"
            "metadata: { name: neo4j }\n"
            "spec:\n"
            "  serviceName: neo4j\n"
            "  replicas: 1\n"
            "  volumeClaimTemplates:\n"
            "    - metadata: { name: neo4j-data }\n"
            '      spec: { accessModes: ["ReadWriteOnce"] }'
        ),
        language="yaml",
        explain="Core servers need a STABLE network identity + their own persistent volume each — exactly what a StatefulSet gives, unlike a Deployment (interchangeable, identity-less pods). Stable identity is what makes Raft consensus work across pod restarts.",
        mental_model="Named, numbered lockers (StatefulSet) vs a pile of identical chairs (Deployment).",
        memory_hook="Raft needs identity → StatefulSet, not Deployment.",
        what="Core Neo4j as a StatefulSet.",
        how="kind: StatefulSet + volumeClaimTemplates for per-pod PVC.",
        where="k8s/base/neo4j-statefulset.yaml (replicas: 1 in demo).",
        when="Running Neo4j on Kubernetes.",
        who="Platform/ops.",
        why="Stable network id + own PVC = Raft survives restarts.",
        blank="kind: ____   # not Deployment — Raft needs stable identity",
        answers=["StatefulSet"],
        pitfalls=[
            "[NON-CLAIM] no Helm chart/Operator, no elastic replica pool, no NetworkPolicy — raw manifests + kustomize only."
        ],
        sources=[
            {
                "title": "Kubernetes — StatefulSets",
                "url": "https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/",
                "kind": "docs",
            },
        ],
        run_hint="[AS-BUILT] k8s/base + overlays/staging|prod.",
    )
    b.add(
        "k8s-cronjob",
        S4,
        "Write the ingestion CronJob skeleton.",
        kind="block",
        code=(
            "apiVersion: batch/v1\n"
            "kind: CronJob\n"
            "metadata: { name: etl-pipeline }\n"
            "spec:\n"
            '  schedule: "0 2 * * *"          # nightly ingestion\n'
            "  concurrencyPolicy: Forbid\n"
            "  jobTemplate:\n"
            "    spec:\n"
            "      template:\n"
            "        spec:\n"
            "          restartPolicy: OnFailure"
        ),
        language="yaml",
        explain="Scheduled ingestion runs as a Kubernetes CronJob — the production home for batch ingestion, rather than a GitHub Actions runner reaching into prod. Actions triggers/validates the pipeline; the CronJob executes it on cluster-local compute.",
        mental_model="A nightly cron on the cluster, not a CI runner poking production.",
        memory_hook="Ingestion = CronJob (schedule + Forbid overlap).",
        what="Batch ingestion as a CronJob.",
        how="kind: CronJob, schedule cron, concurrencyPolicy: Forbid.",
        where="k8s/base/etl-cronjob.yaml.",
        when="Nightly (0 2 * * *) or on schedule.",
        who="Ops.",
        why="Long/large ingestion belongs on cluster compute, not a CI runner.",
        blank='schedule: "0 2 * * *"  # concurrencyPolicy: ____',
        answers=["Forbid"],
        sources=[
            {
                "title": "Kubernetes — CronJob",
                "url": "https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/",
                "kind": "docs",
            },
        ],
        run_hint="[AS-BUILT] k8s/base/etl-cronjob.yaml.",
    )
    b.add(
        "end-to-end-chain",
        S4,
        "Recite how Docker, Actions, and K8s chain end to end.",
        kind="concept",
        explain="Change ontology/Cypher/prompt → GitHub Actions (lint + TBox/ABox tests + eval + build image) as a merge-blocking gate → image pushed to registry (Docker) → Kubernetes rolling-updates the pipeline Deployment/CronJob to the new image, Neo4j StatefulSet keeps running → new data flows Part 3 Steps 1–5 → validated before trusted.",
        mental_model="Gate at merge, package as image, run on the cluster, validate before trust.",
        memory_hook="Gate → image → run → validate.",
        what="The end-to-end delivery chain.",
        how="Actions gate → registry → K8s rollout → validated ingestion.",
        where="ci.yml/cd.yml → registry → k8s/.",
        when="Every change to ontology/query/prompt/pipeline.",
        who="Platform.",
        why="Each tool does one job; together = safe continuous knowledge delivery.",
        blank="Actions gate → push image → K8s rollout → validate before ____",
        answers=["trust"],
        sources=[{"title": "docs/sdd/AS_BUILT.md", "kind": "docs"}],
        run_hint="Recite in under 30 seconds for the final boss.",
    )

    return b.cards


MASTERCLASS_CARDS: dict[str, list[MemoryCard]] = {
    "mc-01-rdf-owl-ontology-turtle": _build_ontology(),
    "mc-02-smart-cypher-agent": _build_agent(),
    "mc-03-graph-ops-index-delta-scale": _build_graph_ops(),
    "mc-04-scaling-populating-kg": _build_scaling_populate(),
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
