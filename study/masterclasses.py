"""Verbatim 'Master This Code' guides to memorize word-for-word.

These are stored EXACTLY as authored (code blocks cleaned so the Turtle/Python
is valid and accurately memorizable). Unlike the interactive StudyModules, a
Masterclass is meant to be memorized verbatim, then reproduced from a blank page.

Body is markdown; the frontend splits on headings for a reveal-based drill.
"""

from __future__ import annotations

from study.models import Masterclass

# ── Guide 1: RDF/OWL ontology in Turtle ────────────────────────────────────
_ONTOLOGY_BODY = """# Master This Code: The Car Diagnostics RDF/OWL Ontology (Turtle)

### A Memorize-It, Write-It, Explain-It Guide — the Precursor to Your Neo4j Graph

## HOW TO USE THIS GUIDE

Same method as the previous two guides: read the Story until you can retell it, read the fully annotated Turtle once, do the Self-Quiz **without looking**, fade through the three Practice Levels, then the Final Boss Test. Space these across a few sessions.

**Why this guide exists before the Neo4j guides, not after**: in your actual pipeline, this ontology is the **rulebook** that should exist before a single node gets created in Neo4j — it's the design-time contract that says what's allowed to exist and how it's allowed to connect, before you ever write a `CREATE` or a Cypher `MATCH`. The two "Master This" guides you already have (graph-only agent, smart-Cypher agent) are what **queries** this structure once it's populated. This guide is what **defines** the structure in the first place, in W3C-standard RDF/OWL, expressed in Turtle syntax.

## PART 0 — THE STORY (your memory anchor)

> **"Before I write down a single real fact about a real car, I build the rulebook. First I write a dictionary of short nicknames for long official web addresses — nobody wants to type the full name every time. Then I write a title page saying what this rulebook is for. Then I declare the five NOUNS allowed to exist in this world: Product, ErrorCode, Symptom, DiagnosticStep, Resolution. Then I pass a law: nothing is allowed to secretly be two nouns at once. Then I declare the VERBS — which noun is allowed to connect to which other noun, and in which direction. Then I pass minimum-requirement laws — an ErrorCode isn't allowed to exist with zero ways to confirm it, a DiagnosticStep isn't allowed to exist with zero resolution it leads to. Only after all of that do I write down real, actual facts — a real Camry, a real error code, a real symptom."**

The one-sentence version: **"Dictionary, title, nouns, no-overlap law, verbs, minimum-requirement laws, then real facts."**

| # | Beat | What it actually is | The Neo4j equivalent it precedes |
|---|---|---|---|
| 1 | Prefixes | Short nicknames for long W3C URIs | (no direct equivalent — Neo4j has no URIs) |
| 2 | Ontology header | Metadata: what this rulebook is, in one sentence | A README for your graph |
| 3 | Classes | The allowed categories of thing | Node **labels** (`:Product`, `:ErrorCode`, ...) |
| 4 | Disjointness | "Nothing is two classes at once" | A constraint you'd otherwise have to enforce in application code |
| 5 | Object properties | The allowed connections, with direction | Relationship **types** (`:CAN_EXHIBIT`, `:MAY_INDICATE`, ...) |
| 6 | Restrictions | Minimum-requirement rules on those connections | A constraint Neo4j does **not** enforce natively — more on this in Part 4 |
| 7 | Individuals | Real instance data | Actual nodes and relationships in the graph |

If you can recite this seven-row table from memory, you understand both the ontology **and** exactly how it becomes your Neo4j graph.

## PART 1 — THE FULLY ANNOTATED TURTLE

```turtle
# ============================================================
# BEAT 1: PREFIXES — the dictionary of short nicknames
# ============================================================
@prefix :     <http://example.org/car-diagnostics#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

# `:` (the empty prefix) is OUR namespace -- every term we invent below (:Product,
# :ErrorCode, :canExhibit...) actually expands to
# "http://example.org/car-diagnostics#Product", etc. The other four prefixes
# (rdf, rdfs, owl, xsd) are NOT ours -- they're the official W3C vocabularies
# we're building on top of. You almost never invent your own rdf:/owl: terms;
# you use theirs and define your own under your own prefix.

# ============================================================
# BEAT 2: ONTOLOGY HEADER — the title page
# ============================================================
<http://example.org/car-diagnostics> rdf:type owl:Ontology ;
    rdfs:label "Car Diagnostics Ontology" ;
    rdfs:comment "Governs Product, Symptom, ErrorCode, DiagnosticStep, and Resolution facts for a car-diagnostics knowledge graph." .

# Note this one line uses the FULL URI, not the : shorthand -- that's because
# this triple is describing the ontology document itself, not a term inside it.

# ============================================================
# BEAT 3: CLASSES — the allowed nouns
# ============================================================
:Product rdf:type owl:Class ;
    rdfs:label "Product" ;
    rdfs:comment "A car model/product line, e.g. Toyota Camry 2022." .

:ErrorCode rdf:type owl:Class ;
    rdfs:label "Error Code" ;
    rdfs:comment "A specific, catalogued fault code, e.g. P0300." .

:Symptom rdf:type owl:Class ;
    rdfs:label "Symptom" ;
    rdfs:comment "An observation reported by a customer or technician, e.g. rough idle." .

:DiagnosticStep rdf:type owl:Class ;
    rdfs:label "Diagnostic Step" ;
    rdfs:comment "A specific check that confirms an ErrorCode is really present." .

:Resolution rdf:type owl:Class ;
    rdfs:label "Resolution" ;
    rdfs:comment "The repair action that fixes a confirmed ErrorCode." .

# Five classes. Notice the pattern in every block above: rdf:type owl:Class
# declares WHAT this is; rdfs:label is the short human-readable name;
# rdfs:comment is the longer explanation. This three-line shape repeats
# constantly in OWL -- learn this shape once, reuse it everywhere.

# ============================================================
# BEAT 4: DISJOINTNESS — the no-overlap law
# ============================================================
[] rdf:type owl:AllDisjointClasses ;
   owl:members ( :Product :ErrorCode :Symptom :DiagnosticStep :Resolution ) .

# `[]` is a "blank node" -- an anonymous thing that exists only to hold this
# one statement together. We don't need to name it because nothing else in
# the file needs to refer back to it.
# `( ... )` with spaces, NOT commas, is Turtle's syntax for an RDF LIST --
# a specific, ordered collection structure, different from just writing
# five separate triples.
# In plain English: nothing can simultaneously be a Product AND an ErrorCode,
# or a Symptom AND a Resolution, etc. Without this, a data-entry mistake could
# silently create a node that's typed as two unrelated things, corrupting any
# query that assumes a node is exactly one type.

# ============================================================
# BEAT 5: OBJECT PROPERTIES — the allowed verbs, with direction
# ============================================================
:canExhibit rdf:type owl:ObjectProperty ;
    rdfs:domain :Product ;
    rdfs:range :ErrorCode ;
    rdfs:label "can exhibit" .

:mayIndicate rdf:type owl:ObjectProperty ;
    rdfs:domain :Symptom ;
    rdfs:range :ErrorCode ;
    rdfs:label "may indicate" .

:confirmedBy rdf:type owl:ObjectProperty ;
    rdfs:domain :ErrorCode ;
    rdfs:range :DiagnosticStep ;
    rdfs:label "confirmed by" .

:leadsTo rdf:type owl:ObjectProperty ;
    rdfs:domain :DiagnosticStep ;
    rdfs:range :Resolution ;
    rdfs:label "leads to" .

# `rdfs:domain` = "this property only ever starts FROM this class."
# `rdfs:range`  = "this property only ever points TO this class."
# Read :canExhibit as an arrow: (:Product) --canExhibit--> (:ErrorCode).
# Four verbs, four arrows, matching exactly the four relationship types
# you'll create in Neo4j later.

# ============================================================
# BEAT 6: RESTRICTIONS — minimum-requirement laws
# ============================================================
:ErrorCode rdfs:subClassOf [
    rdf:type owl:Restriction ;
    owl:onProperty :confirmedBy ;
    owl:minCardinality "1"^^xsd:nonNegativeInteger
] .

:DiagnosticStep rdfs:subClassOf [
    rdf:type owl:Restriction ;
    owl:onProperty :leadsTo ;
    owl:minCardinality "1"^^xsd:nonNegativeInteger
] .

# Read the first one as: "being an ErrorCode means being a subclass of
# [the set of things that have at least 1 :confirmedBy relationship]."
# In plain English: an ErrorCode with ZERO confirming DiagnosticSteps is not
# allowed to exist -- a diagnostic dead end gets caught here, at design time,
# instead of being discovered by a confused customer later.
# `"1"^^xsd:nonNegativeInteger` is Turtle's syntax for a TYPED LITERAL --
# the value "1", explicitly tagged as the xsd:nonNegativeInteger data type,
# not just a bare, ambiguous number.

# ============================================================
# BEAT 7: INDIVIDUALS — the real facts
# ============================================================
:Toyota_Camry_2022 rdf:type :Product ;
    rdfs:label "Toyota Camry 2022" ;
    :canExhibit :P0300 .

:P0300 rdf:type :ErrorCode ;
    rdfs:label "P0300" ;
    rdfs:comment "Random/multiple cylinder misfire detected" ;
    :confirmedBy :CheckSparkPlugs .

:RoughIdle rdf:type :Symptom ;
    rdfs:label "Rough idle" ;
    :mayIndicate :P0300 .

:CheckSparkPlugs rdf:type :DiagnosticStep ;
    rdfs:label "Check spark plugs and ignition coils" ;
    :leadsTo :ReplaceSparkPlugs .

:ReplaceSparkPlugs rdf:type :Resolution ;
    rdfs:label "Replace worn spark plugs" .

# THIS is the block that becomes actual nodes and relationships in Neo4j.
# Every `rdf:type :SomeClass` triple becomes a node with that label.
# Every :canExhibit / :mayIndicate / :confirmedBy / :leadsTo triple becomes
# a relationship of that type between two nodes.
```

## PART 1B — HOW THIS BECOMES YOUR NEO4J GRAPH

This is the bridge the previous two guides assumed but never spelled out. When you populate Neo4j from this ontology, the mapping is mechanical:

| In this Turtle file | Becomes, in Neo4j / Cypher |
|---|---|
| `:Toyota_Camry_2022 rdf:type :Product` | `CREATE (:Product {name: "Toyota Camry 2022"})` |
| `:P0300 rdf:type :ErrorCode` | `CREATE (:ErrorCode {code: "P0300", description: "..."})` |
| `:Toyota_Camry_2022 :canExhibit :P0300` | `CREATE (p:Product)-[:CAN_EXHIBIT]->(e:ErrorCode)` |
| `:RoughIdle :mayIndicate :P0300` | `CREATE (s:Symptom)-[:MAY_INDICATE]->(e:ErrorCode)` |

**The one gotcha worth memorizing on its own**: Neo4j does **not** natively enforce OWL restrictions (Beat 6). If you `CREATE` an `ErrorCode` node in Cypher with zero `CONFIRMED_BY` relationships, Neo4j will not stop you — the `owl:minCardinality` rule only means something if you're using an actual OWL reasoner (like a triple store — Apache Jena/Fuseki, or a SHACL validator) to check the data, or if you enforce it yourself in application code before writing to Neo4j. The ontology is the **design contract**; Neo4j is the **storage engine** — they don't automatically police each other unless you deliberately wire that check in.

## PART 2 — THE SELF-QUIZ (answer without looking)

1. What does the empty prefix `:` actually expand to, and why do we define our own prefix instead of only using `rdf:`/`owl:`/`rdfs:`?
2. What's the difference between `rdfs:label` and `rdfs:comment` — why do almost all of our class/property declarations use both?
3. Read `:canExhibit`'s `rdfs:domain`/`rdfs:range` pair out loud as a sentence with an arrow, the way Beat 5's annotation does. Do the same for `:confirmedBy`.
4. What does `[]` (a blank node) mean, and why doesn't the disjointness axiom need to name it?
5. In Turtle, how do you write an ordered list, and where in this file is one used?
6. Explain, in your own words, what `owl:minCardinality "1"` on `:ErrorCode`/`:confirmedBy` actually prevents.
7. What is a "typed literal," and where does one appear in Beat 6?
8. If you ran `CREATE (:ErrorCode {code: "P0999"})` in Neo4j with no linked `DiagnosticStep`, would Neo4j itself stop you? Why or why not?
9. Which Turtle punctuation mark means "same subject, new predicate" (`;`), and which one means "this statement is completely finished" (`.`)? Where would using the wrong one break Beat 3's class declarations?
10. Name, from memory, all seven Beats and what real-world Neo4j concept each one becomes (or doesn't become, for Beats 1–2 and 6).

## PART 3 — PROGRESSIVE PRACTICE

Cover Part 1 entirely for all three levels.

### Level 1 — Fill in the blanks

```turtle
@prefix :     <____> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <____> .
@prefix owl:  <____> .
@prefix xsd:  <____> .

:Product rdf:____ owl:Class ;
    rdfs:____ "Product" ;
    rdfs:comment "____" .

[] rdf:type owl:____ ;
   owl:____ ( :Product :ErrorCode :Symptom :DiagnosticStep :Resolution ) .

:canExhibit rdf:type owl:____ ;
    rdfs:____ :Product ;
    rdfs:____ :ErrorCode .

:ErrorCode rdfs:subClassOf [
    rdf:type owl:____ ;
    owl:onProperty :____ ;
    owl:____ "1"^^xsd:nonNegativeInteger
] .

:Toyota_Camry_2022 rdf:type :____ ;
    rdfs:label "____" ;
    :canExhibit :____ .
```

### Level 2 — Headers only

You get only the seven Beat names from Part 0's table. Write the entire ontology underneath each header, from memory, including at least one individual per class in Beat 7. Don't peek until genuinely finished.

### Level 3 — Blank page

You get only this sentence: **"Write a W3C-standard OWL ontology in Turtle for a car-diagnostics graph with classes Product, ErrorCode, Symptom, DiagnosticStep, and Resolution — Products can exhibit ErrorCodes, Symptoms may indicate ErrorCodes, ErrorCodes are confirmed by DiagnosticSteps, and DiagnosticSteps lead to Resolutions — with every ErrorCode requiring at least one confirming step and every DiagnosticStep requiring at least one resolution, and the five classes pairwise disjoint."** Write the whole file from nothing, then populate it with one real example per class.

## PART 4 — COMMON MISTAKES TO WATCH FOR

- **Forgetting the trailing period `.` at the end of a full statement, or using it where a semicolon `;` belongs.** In Turtle, `;` means "same subject, another predicate about it"; `.` means "that subject's statement is completely finished." Swapping them is the single most common Turtle syntax error, and it silently breaks parsing rather than giving an obviously helpful error.
- **Using `,` instead of `;` when adding a new predicate.** `,` is for listing multiple **objects** of the **same** predicate (e.g., a node with three labels); `;` is for adding a **different** predicate to the same subject. These are easy to confuse and produce very different (wrong) triples.
- **Forgetting `^^xsd:nonNegativeInteger` (or any datatype tag) on a numeric literal used inside a restriction** — an untyped `"1"` is just a string in RDF, not a number, and `owl:minCardinality` expects a properly typed integer.
- **Writing `owl:Class` declarations without also thinking about disjointness.** It's easy to declare five classes and forget the `owl:AllDisjointClasses` axiom entirely — the ontology will still "work" for basic queries, but nothing stops a future data-entry error from creating a node that's typed as two unrelated classes at once.
- **Getting `rdfs:domain`/`rdfs:range` backwards.** `:confirmedBy`'s domain is `:ErrorCode` and its range is `:DiagnosticStep` — meaning the arrow goes ErrorCode → DiagnosticStep. Writing it backwards silently flips the intended meaning of every fact that uses this property.
- **Forgetting that a restriction is attached via `rdfs:subClassOf`, not `rdf:type` directly.** The pattern is always "ClassName `rdfs:subClassOf` [a blank-node restriction]" — trying to attach a restriction with `rdf:type` instead produces invalid OWL.
- **Assuming Neo4j will enforce these rules automatically.** As covered in Part 1B, it will not — writing a beautiful, restriction-complete ontology and then populating Neo4j directly via Cypher with no validation step means the restrictions exist only on paper unless you deliberately check for them.

## PART 5 — THE FINAL BOSS TEST

1. Explain the whole ontology out loud in under 90 seconds, using the seven-Beat story from Part 0 as your outline.
2. Write the complete Turtle file from a blank page.
3. Narrate, from memory, exactly how Beat 7's individual data would become five `CREATE` statements in Neo4j (Part 1B) — say the node labels and relationship types out loud, not just "it becomes a graph."
4. Add one brand-new individual not in the original file (a different car model, error code, symptom, diagnostic step, and resolution of your own invention) and check that it obeys every rule from Beats 4 and 6 — no missing confirming step, no missing resolution, no class overlap.
5. Compare everything against Part 1. Whatever you hesitated on, drill again tomorrow, not today.
"""


# ── Guide 2: Smart Cypher-generation agent ─────────────────────────────────
_SMART_CYPHER_BODY = '''# Master This Code: The Smart Cypher-Generation Diagnostics Agent

### A Memorize-It, Write-It, Explain-It Guide

## HOW TO USE THIS GUIDE

Same method again: Story until you can retell it, annotated code once, Self-Quiz **without looking**, then the three Practice Levels, then the Final Boss Test. Space it out.

**This is version 3 of the same evolving agent.** You went from "two tools with Python logic" → "one tool with hardcoded Cypher" → now "one tool that writes its own Cypher." Anchor this version to that lineage, not as a fresh thing to learn.

## PART 0 — THE STORY (your memory anchor)

> **"In the last version, my one worker walked into the filing room with two fixed search routines memorized — check the label, then check the drawers. This version fires that routine-memorizing habit entirely. Now the worker has a second, small assistant standing at the filing-room door whose only job is: listen to what the visitor wants, and write out, on the spot, exactly which drawer and shelf to check. Then my worker just follows those instructions and reports back what it finds."**

The one-sentence version: **"One smart tool — it asks a second LLM to write the Cypher, then runs whatever Cypher comes back."**

| # | What changed from the graph-only version | Why |
|---|---|---|
| 1 | **New import**: `from langchain_neo4j import Neo4jGraph` | A LangChain-native wrapper around Neo4j, replacing the raw `neo4j` driver |
| 2 | `driver` (raw driver) → `graph` (`Neo4jGraph` object) | `Neo4jGraph` gives you `.query()` directly — no manual `with driver.session()` boilerplate |
| 3 | Two fixed Cypher queries → zero fixed queries | The tool no longer "knows" any Cypher in advance at all |
| 4 | New concept inside the tool: a **second**, small LLM call just to generate Cypher text | This is the actual "smart" part — one LLM writes the query, a `try/except` runs it |
| 5 | New failure mode to handle: the generated Cypher could be wrong or unsafe | Handled with a plain `try/except`, returning the error as a string rather than crashing |
| 6 | Blocks 3, 4, 5 (State, Nodes/Graph, Run) | **Unchanged again** — same insight as before: the LangGraph skeleton is stable; only the tool's insides evolve |

**The pattern worth locking in across all three versions**: every upgrade so far has touched **only** the tool's internals. If you remember nothing else, remember that the outer skeleton (State → Nodes → Graph → Run) has now been identical across three versions in a row — which means once you know it, you never have to re-learn it, only recognize it.

## PART 1 — THE FULLY ANNOTATED CODE

```python
# ============================================================
# BEAT 1: IMPORTS + NEO4JGRAPH SETUP (LangChain-native this time)
# ============================================================
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import operator
from langchain_neo4j import Neo4jGraph     # NEW: replaces the raw `neo4j.GraphDatabase` driver

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)
# `graph` now exposes graph.query(cypher_string) directly --
# no manual session-opening boilerplate like the previous version needed.
# NOTE: this variable is called `graph`, and so is the LangGraph compiled object
# in Beat 5 below -- they are NOT the same thing, just an unlucky name collision
# in this specific example. Watch for that when reading Beat 5.

# ============================================================
# BEAT 2: ONE MODEL + ONE TOOL THAT WRITES ITS OWN QUERIES
# ============================================================
class DiagnosticQueryInput(BaseModel):
    user_input: str = Field(..., description="User's car problem (error code or symptoms)")

@tool(args_schema=DiagnosticQueryInput)
def query_graph(user_input: str) -> str:
    """
    Smart tool: Uses LLM to generate Cypher, then runs it on Neo4j.
    """
    # ---- STEP A: a second, small LLM call whose only job is writing Cypher ----
    cypher_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # this is a SEPARATE LLM instance from the one in diagnostic_agent_node below --
    # one LLM decides "should I call a tool," a different LLM call (inside the tool)
    # decides "what Cypher should this tool actually run"

    prompt = f"""
    You are an expert at writing Cypher queries for a car diagnostics knowledge graph.
    The graph has nodes: CarModel, ErrorCode, Symptom, Cause, Fix
    Relationships: HAS_ERROR, CAUSED_BY, FIXED_BY, LEADS_TO
    User query: "{user_input}"
    Generate a single, safe Cypher query that answers this.
    Only return the Cypher query, nothing else.
    """
    # this prompt does two jobs at once: (1) teaches the schema (node/relationship names)
    # so the LLM doesn't invent labels that don't exist, and (2) constrains the output
    # format ("only return the Cypher query") so the response is directly runnable

    cypher_response = cypher_llm.invoke(prompt)
    cypher_query = cypher_response.content.strip()
    # .strip() removes stray whitespace/newlines the LLM might wrap around the query

    # ---- STEP B: run whatever Cypher came back, defensively ----
    try:
        results = graph.query(cypher_query)
        if results:
            return str(results)
        else:
            return "No results found in the diagnostic graph."
    except Exception as e:
        return f"Error running query: {str(e)}"
        # if the generated Cypher is malformed, this is what stands between
        # "the tool returns a clean error message" and "the whole program crashes"

tools = [query_graph]

# ============================================================
# BEAT 3: STATE — unchanged, third version in a row
# ============================================================
class AgentState(TypedDict):
    messages: Annotated[List, operator.add]

# ============================================================
# BEAT 4: NODES + GRAPH — unchanged structure
# ============================================================
def diagnostic_agent_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)
    # this is the FIRST llm -- the one deciding whether to call query_graph at all.
    # it is a different call from cypher_llm inside the tool above.
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("diagnostic_agent", diagnostic_agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("diagnostic_agent")

    def should_continue(state):
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    workflow.add_conditional_edges("diagnostic_agent", should_continue)
    workflow.add_edge("tools", "diagnostic_agent")
    return workflow.compile()

# ============================================================
# BEAT 5: RUN — unchanged pattern (name collision noted above)
# ============================================================
if __name__ == "__main__":
    graph = build_graph()   # <-- reassigns the name `graph`! Now it means the compiled
                            #     LangGraph object, not the Neo4jGraph from Beat 1.
    state = {"messages": [("human", "My Honda Civic has P0420 error and check engine light")]}
    result = graph.invoke(state)
    print(result["messages"][-1].content)
```

## PART 2 — THE SELF-QUIZ (answer without looking)

1. Name the two different LLM calls in this file and, for each, say exactly what job it's doing.
2. What does `Neo4jGraph` give you that the raw `neo4j.GraphDatabase` driver from the previous version didn't?
3. What are the two jobs the Cypher-generation prompt is doing at once? (Hint: one is about vocabulary, one is about output format.)
4. Why does the prompt explicitly list node and relationship names (`CarModel, ErrorCode, Symptom...`) instead of just asking "write a Cypher query for this"?
5. What happens, step by step, if the LLM generates syntactically invalid Cypher?
6. There is a variable name used for two different things in this file. What is it, and what are the two different things?
7. Is there still any hardcoded `MATCH` statement anywhere in this file? Why or why not?
8. Which five things are identical to the previous (graph-only) version, structurally? Naming these matters as much as naming what's new.
9. `.strip()` is called on `cypher_response.content` — what problem is this specifically guarding against?

## PART 3 — PROGRESSIVE PRACTICE

Cover Part 1 completely for all three levels.

### Level 1 — Fill in the blanks

```python
from langchain_neo4j import ____

graph = ____(
    url=____,
    username=____,
    password=____
)

@tool(args_schema=____)
def query_graph(user_input: str) -> str:
    cypher_llm = ____(model="____", temperature=0)
    prompt = f"""
    You are an expert at writing ____ queries for a car diagnostics knowledge graph.
    The graph has nodes: ____
    Relationships: ____
    User query: "{____}"
    Generate a single, safe ____ query that answers this.
    Only return the ____, nothing else.
    """
    cypher_response = cypher_llm.____(prompt)
    cypher_query = cypher_response.____.____()
    try:
        results = ____.query(____)
        if results:
            return ____(results)
        else:
            return "____"
    except ____ as e:
        return f"____"
```

### Level 2 — Headers only

You get only the six-row "what changed" table from Part 0 and the five Beat names. Write the entire file underneath. No peeking until genuinely finished.

### Level 3 — Blank page

You get only this sentence: **"Take the graph-only diagnostics agent and replace its hardcoded Cypher queries with a tool that first asks a small LLM to generate the right Cypher query for the user's input — given the graph's schema — then safely executes whatever Cypher comes back."** Write the whole file from nothing.

## PART 4 — COMMON MISTAKES TO WATCH FOR

- **Forgetting the schema description in the Cypher-generation prompt.** Without explicitly listing node labels and relationship types, the LLM will confidently invent plausible-sounding but nonexistent labels, and every generated query will silently fail to match anything.
- **Forgetting `try/except` around `graph.query(...)`.** Generated Cypher is not guaranteed valid — treat it the same way you'd treat any other untrusted, dynamically-produced input.
- **Confusing the two LLM calls.** `cypher_llm` (inside the tool, writes Cypher) and the `llm` inside `diagnostic_agent_node` (decides whether to call the tool at all) are separate instances doing separate jobs — mixing them up when explaining this code out loud is the most common way people reveal they've only skimmed it.
- **Missing the `graph` name collision.** `graph` means `Neo4jGraph` in Beat 1 and the compiled LangGraph object in Beat 5 — in your own from-scratch rewrite, consider renaming one of them (e.g., `neo4j_graph` and `app`) to avoid this exact confusion, even though the original code uses this collision.
- **Forgetting `.strip()`** and passing a Cypher string with leading/trailing whitespace or an accidental code-fence wrapper (` ```cypher ... ``` `) straight into `graph.query(...)` — a common real-world failure when LLMs are asked to "just return the query."
- **Not returning the query itself in the error message** when debugging — `f"Error running query: {str(e)}"` tells you the Python-level error but not **which** Cypher string caused it; in your own version, consider logging `cypher_query` alongside the exception for real debuggability.

## PART 5 — THE FINAL BOSS TEST

1. Explain the whole file out loud in under 90 seconds, anchored on the "what changed from graph-only" table in Part 0 — specifically call out the two-LLM structure.
2. Write the complete file from a blank page.
3. Narrate the full execution trace for: **"My Ford F-150 is making a grinding noise when braking."** Specifically: what the Cypher-generation prompt receives, what kind of Cypher it's likely to produce given only the schema description, and what happens if that generated query happens to reference a relationship that doesn't exist in the schema.
4. Compare against Part 1. Whatever you hesitated on, drill again tomorrow — not today.

## THE THREE-VERSION LINEAGE, IN ONE TABLE (for when you want the whole arc at a glance)

| | Original agent | Graph-only agent | Smart Cypher agent |
|---|---|---|---|
| Tools | 2, general-purpose | 1, hardcoded Cypher | 1, LLM-generated Cypher |
| Domain logic lives in | Python `if` statements | Fixed Cypher queries | An LLM prompt describing the schema |
| Flexibility | Low | Medium | High |
| Determinism | Low (LLM reasons about domain) | High (fixed queries) | Medium (generated but schema-constrained) |
| What's unchanged throughout | — | State/Nodes/Graph/Run skeleton | State/Nodes/Graph/Run skeleton |

If you can reconstruct this table from memory, you understand not just three versions of code, but the actual engineering trade-off (flexibility vs. determinism) each version was making.
'''


MASTERCLASSES: list[Masterclass] = [
    Masterclass(
        id="mc-01-rdf-owl-ontology-turtle",
        title="Master This Code: The Car Diagnostics RDF/OWL Ontology (Turtle)",
        subtitle="Memorize-It, Write-It, Explain-It — the precursor to your Neo4j graph",
        track="foundations",
        order=10,
        tags=["rdf", "owl", "turtle", "ontology", "verbatim", "memorize"],
        estimated_minutes=60,
        body=_ONTOLOGY_BODY,
    ),
    Masterclass(
        id="mc-02-smart-cypher-agent",
        title="Master This Code: The Smart Cypher-Generation Diagnostics Agent",
        subtitle="Memorize-It, Write-It, Explain-It — version 3 of the evolving agent",
        track="agent",
        order=20,
        tags=["langgraph", "cypher", "agent", "llm", "verbatim", "memorize"],
        estimated_minutes=45,
        body=_SMART_CYPHER_BODY,
    ),
]

_BY_ID = {m.id: m for m in MASTERCLASSES}


def list_masterclasses() -> list[dict]:
    return [m.summary() for m in sorted(MASTERCLASSES, key=lambda m: m.order)]


def get_masterclass(mc_id: str) -> Masterclass | None:
    return _BY_ID.get(mc_id)
