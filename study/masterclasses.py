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


# ── Guide 3: Indexing, delta, partition, concurrency, sharding ─────────────
_GRAPH_OPS_BODY = """# Master This Code: Graph Ops — Indexes, Delta, Partition, Concurrency, Sharding

### A Memorize-It, Write-It, Explain-It Guide — scale the knowledge graph without lying about Fabric

## HOW TO USE THIS GUIDE

Same method as the Turtle ontology guide: read the Story until you can retell it, read the annotated code once, drill **Flashcards** (5W+H + code + pitfalls + sources), run **Test** (fill blanks → write a snippet → write a section), then the Final Boss. Space across sessions.

**How this relates to the Turtle guide (do not replace it):** the Turtle masterclass defines the **rulebook** (TBox) and sample facts. This guide is what happens **after** facts land in Neo4j: **indexes for identity**, **delta for incremental ABox**, **logical partitions**, **bounded concurrency**, and honest **non-claims** about sharding/HA. Keep the Turtle chapter untouched; this is a sibling track.

**Authoritative product docs:** `docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md`, `docs/19-Indexes-Constraints-and-Lookup-Performance.md`, `docs/sdd/AS_BUILT.md`.

## PART 0 — THE STORY (your memory anchor)

> **"I do not invent a Fabric cluster on day one. First I put phone books on every business key — unique constraints so Product and Symptom can be found by id without scanning the warehouse. Then I load with MERGE so re-runs do not duplicate the world. When new bulletins arrive, I do not rebuild the fleet: I preview change, compute entity delta, select products, validate, materialize, promote staging, then production, and invalidate caches. Multi-tenant limits and caches share one language of keys: tenant|product. Connector fetches may fan out on a few threads; one diagnosis ranks serially under an admission bouncer so Neo4j does not melt. Only if one database cannot hold the SLO do I plan product-line shards — relationships stay inside a shard, and I never claim Fabric is live in this demo."**

The one-sentence chant: **Seek → Delta → Key → Cap → Shard-later.**

| Beat | Name | What you memorize |
|------|------|-------------------|
| 1 | Unique constraints (indexes) | `create_constraints` + MERGE + PROFILE |
| 2 | Delta stepping (ABox) | change_preview → entity_delta → promote |
| 3 | Partition & concurrency | partition keys, parallel_map, admission |
| 4 | Retrieval + honesty | index-backed MATCH; Fabric = not as-built |

## PART 1 — BEAT 1: INDEXING (as-built code)

### Why indexes first

Without uniqueness, `MERGE (p:Product {product_id: $id})` can create duplicates under race, and `MATCH (p:Product {product_id: $id})` becomes a label scan. Neo4j 5: `CREATE CONSTRAINT … REQUIRE prop IS UNIQUE` builds a **unique index**.

### The function you must be able to write

```python
def create_constraints(tx) -> None:
    for query in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (fm:FailureMode) REQUIRE fm.failure_mode_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ds:DiagnosticStep) REQUIRE ds.step_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Part) REQUIRE p.part_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:HistoricalResolution) REQUIRE r.resolution_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Model) REQUIRE m.model_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sku:SKU) REQUIRE sku.sku_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.component_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ec:ErrorCode) REQUIRE ec.error_code_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wp:WarrantyPolicy) REQUIRE wp.policy_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (cl:Claim) REQUIRE cl.claim_id IS UNIQUE",
    ]:
        tx.run(query)
```

**File:** `graph/populate_graph.py` — called **before** MERGEs:

```python
with driver.session() as session:
    session.execute_write(create_constraints)
    # then MERGE products, symptoms, …
```

### MERGE paired with the index

```cypher
MERGE (p:Product {product_id: $product_id})
SET p.name = $name
```

### Prove the planner seeks

```cypher
SHOW CONSTRAINTS;
SHOW INDEXES;

PROFILE
MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
RETURN fm LIMIT 5
```

Look for **NodeUniqueIndexSeek** (or similar) on Product — not NodeByLabelScan for that step.

### 5W+H (Beat 1)

| W/H | Answer |
|-----|--------|
| **What** | Unique constraints that materialize unique indexes on business keys |
| **How** | `CREATE CONSTRAINT IF NOT EXISTS … REQUIRE … IS UNIQUE` then MERGE/MATCH on that property |
| **Where** | `graph/populate_graph.py` `create_constraints`; Browser `SHOW INDEXES` |
| **When** | Every populate/promote load; used on every diagnose seek |
| **Who** | ETL creates; GraphRAG uses |
| **Why** | Fast identity + no duplicate products/symptoms |

**Sources:** [Neo4j constraints](https://neo4j.com/docs/cypher-manual/current/constraints/), [MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/), [query tuning](https://neo4j.com/docs/cypher-manual/current/query-tuning/), repo `docs/19-…`, `docs/25-…`.

**Pitfalls:** Index every property (write tax); full-text/vector ≠ unique key; create constraint only after cleaning duplicate data.

**Run:** `python -m graph.populate_graph` → open http://localhost:7474 → `SHOW CONSTRAINTS;`

## PART 2 — BEAT 2: DELTA STEPPING (ABox, not the shortest-path algorithm)

### Two meanings (do not mix)

| Term | Meaning | Here? |
|------|---------|-------|
| Delta-stepping **algorithm** | Parallel SSSP (Meyer/Sanders) | **No** |
| Delta **data** stepping | Apply only NEW/UPDATE knowledge packs | **Yes** |

### Operator chant

**Fetch → Select → Validate ABox → Materialize → Smoke → Approve → Promote staging → Promote production → Invalidate caches.**

### Code anchors

- `graph/enterprise_pipeline/change_preview.py` — NEW / UPDATE / IN_SYNC vs production
- `graph/enterprise_pipeline/entity_delta.py` — per-product entity diffs
- Promote path uses **MERGE** into staging (:7688) then production (:7687)
- Chat **never** reads staging

```python
# Conceptual
delta = compute_product_entity_delta("esp-001", compare_env="production")
# Admin: select product_ids → validate → materialize → promote
```

### 5W+H (Beat 2)

| W/H | Answer |
|-----|--------|
| **What** | Incremental ABox change application by product selection |
| **How** | change_preview → entity_delta → validate → MERGE promote |
| **Where** | Admin wizard + enterprise_pipeline modules |
| **When** | Bulletin/onboard updates — not every chat turn |
| **Who** | Knowledge operator / control plane |
| **Why** | Avoid full fleet rewrite; fail-closed promote |

**Sources:** `docs/25`, `docs/20`, `docs/22`; industry CDC/delta ETL practice (not fully wired as live SAP CDC here).

## PART 3 — BEAT 3: PARTITIONING & CONCURRENCY

### Logical partition keys (as-built)

```python
# runtime/partitioning.py
def partition_for_request(*, tenant_id="default", product_id=None, ... ) -> str:
    bits = [f"tenant={tenant_id or 'default'}"]
    if product_id:
        bits.append(f"product={product_id}")
    ...
    return "|".join(bits)
```

Same key language for rate limits and cache namespaces. Work partition = **selection `product_ids`** lists in promote.

**Not as-built:** hard multi-tenant ACL, Neo4j Fabric multi-DB shards.

### Bounded parallel I/O

```python
# runtime/concurrency.py
from concurrent.futures import ThreadPoolExecutor

def parallel_map(items, fn, max_workers=4, preserve_order=True):
    ...
```

Use for connector fetch fan-out. **Do not** parallelize Bayes ranking inside one diagnosis.

### Admission control (bulkhead)

Cap in-flight `/diagnose` (default 32). Acquire → work → **always** release in `finally`. Redis-backed when `REDIS_URL` is set for multi-pod.

### 5W+H (Beat 3)

| W/H | Answer |
|-----|--------|
| **What** | Logical keys + bounded threads + diagnose admission |
| **How** | `partition_*` helpers; ThreadPoolExecutor max_workers; ConcurrencyLimiter |
| **Where** | `runtime/partitioning.py`, `concurrency.py`, `concurrency_limit.py` |
| **When** | Every multi-tenant request; every extract fan-out; every diagnose under load |
| **Who** | API platform + ETL |
| **Why** | No cross-tenant bleed in limits/cache; protect p99 and Bolt pool |

**Sources:** [Python concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html), [Google SRE — overload](https://sre.google/sre-book/handling-overload/).

## PART 4 — BEAT 4: RETRIEVAL PATH + SHARDING HONESTY

### Hot path (index + product scope)

```cypher
MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
WHERE s.symptom_id IN $symptom_ids
RETURN fm.failure_mode_id AS id, sum(coalesce(ind.confidence, 0)) AS score
ORDER BY score DESC
```

Request path: rate-limit key → admission → optional cache → **unique index seek** → expand product-local edges → hybrid match + Bayes (serial) → release admission.

### Sharding (roadmap only)

Neo4j **composite databases / Fabric**: separate graphs; relationships typically **do not cross shards**. Natural shard key for this domain: **product line / brand / region**. Demo: **not deployed** (`AS_BUILT` non-claim). Cluster HA (primaries/secondaries) also **not** as-built — single prod + staging containers.

### Non-claims (say these only if you want to fail the demo)

- “We have Neo4j Fabric sharding.”
- “We have full CDC from SAP.”
- “We have causal cluster HA.”
- “Delta-stepping shortest-path is in the product.”
- “Multi-threading speeds up Bayes ranking.”

**Say instead:** selection-scoped ABox deltas with MERGE, logical tenant/product keys, bounded concurrency; Fabric/HA designed against official Neo4j docs but not live here.

## PART 5 — SELF-QUIZ (no peeking)

1. Write `create_constraints` for Product and Symptom.
2. What runs first in `populate_graph`: constraints or MERGEs?
3. PROFILE shows NodeByLabelScan on Product — what is wrong?
4. Delta-stepping algorithm vs product delta — which do we implement?
5. Recite the promote chant.
6. Write `partition_for_request` key shape for tenant + product.
7. Why is ranking serial inside one diagnose?
8. Is Fabric multi-shard as-built?

## PART 6 — PRACTICE LEVELS

**Level 1 — Flashcards:** Masters → this guide → Flashcards. Flip for 5W+H, code, pitfalls, sources, run hints. Mark known.

**Level 2 — Fill blanks:** Test → Fill blanks (product_id, run, CONSTRAINTS, …).

**Level 3 — Write snippet / section:** Write `create_constraints`, `parallel_map`, PROFILE block, retrieval MATCH from memory.

**Level 4 — Run it:** `python -m graph.populate_graph`; Browser SHOW INDEXES; PROFILE a product MATCH; Admin delta path for one product.

## PART 7 — FINAL BOSS TEST

1. Explain Seek → Delta → Key → Cap → Shard-later in under 90 seconds.
2. Write create_constraints + one MERGE + PROFILE from a blank page.
3. Narrate entity_delta for `esp-001` from catalog vs production to promote.
4. Draw request path with admission + index seek.
5. State three non-claims without notes.

## PART 8 — CODE & DOC MAP

| Concern | Location |
|---------|----------|
| Unique indexes | `graph/populate_graph.py` `create_constraints` |
| Entity delta | `graph/enterprise_pipeline/entity_delta.py` |
| Change preview | `graph/enterprise_pipeline/change_preview.py` |
| Parallel extract | `runtime/concurrency.py` |
| Admission | `runtime/concurrency_limit.py` |
| Partition keys | `runtime/partitioning.py` |
| Implementation guide | `docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md` |
| Index deep dive | `docs/19-Indexes-Constraints-and-Lookup-Performance.md` |
| As-built / gaps | `docs/sdd/AS_BUILT.md`, `08-GAPS.md` |

If you can reconstruct the chant and the constraint+MERGE pair from memory, you understand how this product scales **truthfully**.
"""


# ── Guide 4: Scaling & populating the KG (traversal, scale, pipeline, infra) ─
_SCALING_POPULATE_BODY = """# Master This Code: Scaling & Populating the Diagnostics Knowledge Graph

### A Memorize-It, Write-It, Explain-It Guide — traversal, high-volume scale, the full data pipeline, and where Docker / GitHub Actions / Kubernetes fit

## HOW TO USE THIS GUIDE

Same method as the other masterclasses: read the Story until you can retell it, read each Part's annotated code once, drill **Flashcards** (5W+H + code + pitfalls + sources), run **Test** (fill blanks → write a snippet → write a section), then the Final Boss. Space across sessions.

**Where this sits in the series.** The Turtle guide (`mc-01`) defines the **rulebook** (TBox). The Cypher-agent guide (`mc-02`) **queries** the graph. The Graph-Ops guide (`mc-03`) covers **indexes / delta / partition / concurrency / sharding honesty**. This guide answers four operational questions end to end: (1) how traversal / shortest-path actually works and whether it is built in, (2) how to scale to a very large graph under very high volume, (3) how raw structured / semi-structured / unstructured data becomes graph data, and (4) where Docker, GitHub Actions, and Kubernetes each fit.

**Honesty rule (unchanged across the series):** every snippet is tagged **[AS-BUILT]** (real repo code you can run), **[REFERENCE]** (correct Neo4j/GDS/K8s pattern documented as roadmap — not live in this demo), or **[NON-CLAIM]** (do not tell a buyer this is done).

**Authoritative product docs:** `docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md`, `docs/19-Indexes-Constraints-and-Lookup-Performance.md`, `docs/17-Enterprise-Landscape-Pipeline-and-Topology.md`, `docs/21-KG-Ingestion-Step-by-Step-Runbook.md`, `docs/sdd/AS_BUILT.md`.

## PART 0 — THE STORY (your memory anchor)

> **"First I decide whether I even need a shortest path — most of the time I want the *cheapest diagnostic route*, not the fewest hops, so I reach for a weighted algorithm and remember it runs on an in-memory projection, not the live store. Then I scale the boring way first: bigger page cache before any cluster, then read replicas, then three separate caching layers, and only *then* — if one database truly cannot hold the load — property sharding, never Fabric-on-day-one. Then I feed the graph: structured rows MERGE straight in as strong nodes, semi-structured JSON/CSV parse through APOC, and unstructured text goes through an LLM that is bound to my five classes so it can only ever propose things the ontology allows — those come in as weak nodes that get resolved into strong ones and validated against shapes before anyone trusts them. Finally I wrap it: Docker packages Neo4j and my pipeline code, GitHub Actions gates every ontology / query / prompt change before merge, and Kubernetes runs the core graph as a StatefulSet with read replicas and a nightly ingestion CronJob."**

The one-sentence chant: **Weighted-path → Scale-boring-first → Strong+Weak+Validate → Docker-gate-run.**

| Part | Theme | What you memorize |
|------|-------|-------------------|
| 1 | Traversal | `shortestPath()` vs GDS; projection first; weighted = cheapest route |
| 2 | Scale | page cache → replicas → 3 caches → property sharding last |
| 3 | Pipeline | structured MERGE, semi APOC, unstructured schema-bound LLM, strong/weak, SHACL |
| 4 | Infra | Docker packages, Actions gates, K8s runs (StatefulSet + CronJob) |

## PART 1 — TRAVERSAL & SHORTEST PATH

### Two tiers (memorize the split)

| Tier | Ships with Neo4j? | Weighted? | Use |
|------|-------------------|-----------|-----|
| Native Cypher `shortestPath()` / `allShortestPaths()` | **Yes** (built in) | No — fewest hops (BFS) | reachability: *is there any path at all?* |
| GDS library (Dijkstra, Delta-Stepping, A*, Yen's) | **No** — install separately | Yes — lowest total cost | *cheapest* diagnostic route by technician time / part cost |

### Native, unweighted — reachability [REFERENCE]

```cypher
// Is this Symptom connected to any Resolution at all? (fewest hops)
MATCH (s:Symptom {symptom_id: $symptom_id}), (r:Resolution)
MATCH path = shortestPath((s)-[*..6]-(r))
RETURN path
LIMIT 1
```

### Weighted — cheapest route needs a projection FIRST [REFERENCE]

The #1 trip-up: **GDS algorithms run on an in-memory graph projection, not your live store.** Project, then run, then optionally drop.

```cypher
// 1) Project the sub-shape you want to analyse (nodes + weighted rels)
CALL gds.graph.project(
  'diag',
  ['Symptom','FailureMode','DiagnosticStep','Resolution'],
  {
    INDICATES:  { properties: 'cost' },
    CONFIRMS:   { properties: 'cost' },
    LEADS_TO:   { properties: 'cost' }
  }
);

// 2) Cheapest route from one symptom to a resolution (weighted Dijkstra)
MATCH (src:Symptom {symptom_id: $symptom_id}), (dst:Resolution {resolution_id: $resolution_id})
CALL gds.shortestPath.dijkstra.stream('diag', {
  sourceNode: src, targetNode: dst, relationshipWeightProperty: 'cost'
})
YIELD totalCost, nodeIds, costs
RETURN totalCost, [gds.util.asNode(id) IN nodeIds | gds.util.asNode(id).name] AS route;

// 3) Free the projection when done
CALL gds.graph.drop('diag');
```

### The algorithm menu (pick on purpose, not "Dijkstra by default")

| Algorithm | Job | Weighted | Parallel |
|-----------|-----|----------|----------|
| `gds.shortestPath.dijkstra` | one source → one target | Yes | No (single-threaded) |
| `gds.allShortestPaths.dijkstra` | one source → all nodes | Yes | No |
| **Delta-Stepping** SSSP | one source → all, **fast** | Yes | **Yes (parallel)** |
| `A*` | source→target with a heuristic | Yes | No |
| Yen's | **k** shortest paths (alternatives) | Yes | Partial |
| BFS / DFS | plain reachability | No | No |

**Precise fact to keep:** GDS's Dijkstra is single-threaded **no matter how much concurrency you configure** — for genuinely parallel single-source shortest paths at scale you switch **algorithm** to Delta-Stepping; it is not a config flag on Dijkstra.

### In THIS repo [AS-BUILT]

The diagnosis hot path does **not** call `shortestPath()` or GDS. It is a **bounded, parameterized, product-scoped multi-hop `MATCH`** — start at a known product/symptom (unique index seek), expand product-local edges, score in Python. Fewest-hops reachability is not the question; ranked failure modes are.

```cypher
// graph/graph_rag.py style — bounded expansion, not a path search
MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
WHERE s.symptom_id IN $symptom_ids
RETURN fm.failure_mode_id AS id, sum(coalesce(ind.confidence, 0)) AS score
ORDER BY score DESC
```

**[NON-CLAIM]** "We run Delta-stepping / Dijkstra shortest-path in production." We do not — GDS is not installed (only APOC). The weighted-path blocks above are the correct pattern to add if a *cheapest-route* use case is prioritised.

## PART 2 — SCALING FOR HIGH VOLUME

Apply in order — each step is what you reach for once the previous stops being enough.

### Step 1 — Vertical first: the page cache [REFERENCE]

More RAM matters more for Neo4j than anything else, because the **page cache** decides whether a query reads from RAM or disk. Size it to hold your active working set before touching clustering.

```bash
# neo4j.conf (reference tuning — not tuned in the demo container)
server.memory.pagecache.size=8g
server.memory.heap.initial_size=4g
server.memory.heap.max_size=4g
```

### Step 2 — Read scaling: Core-Replica cluster [REFERENCE / NON-CLAIM here]

```text
                 ┌──────────── writes (HAProxy) ────────────┐
                 ▼                                            ▼
   Core-1 ◄─Raft─► Core-2 ◄─Raft─► Core-3     (odd number; quorum survives 1 loss)
     │                                  │
     └────── async replication ─────────┘
                 │            │            │
              Replica-1   Replica-2   Replica-N   ◄── load balancer sends READS here
```

- **Core servers**: authoritative, Raft consensus for writes — always an **odd** number (3 min).
- **Read replicas**: async copies, serve reads, no write consensus → "near-infinite" horizontal read scale.
- **Causal consistency**: a client that just wrote gets a **bookmark**; subsequent reads with that bookmark are guaranteed to reflect that write — so scaling reads never shows a user stale data after their own change.

```python
# Reference: read-your-writes with a bookmark (neo4j Python driver)
with driver.session() as w:
    w.run("MERGE (p:Product {product_id:$id}) SET p.name=$n", id="wm-001", n="Washer")
    bookmarks = w.last_bookmarks()
with driver.session(bookmarks=bookmarks) as r:   # guaranteed to see the write
    r.run("MATCH (p:Product {product_id:$id}) RETURN p", id="wm-001")
```

**[AS-BUILT]** This repo runs a **single** production Neo4j (`:7687`) plus a **separate staging** Neo4j (`:7688`). That is an **environment partition** (promote-first), **not** a causal cluster. Cluster HA is a documented **non-claim**.

### Step 3 — Caching is three layers, not one

| Layer | What it is | This repo |
|-------|-----------|-----------|
| 1 Page cache | Neo4j's own store-file cache (Step 1) | REFERENCE (untuned demo) |
| 2 Read replicas as a cache tier | replicas act like warm "graph caches" that also run read Cypher | REFERENCE / non-claim |
| 3 Cache sharding | route a request to whichever member already has that slice warm | REFERENCE |
| App request cache | TTL cache of stable reads (schema, subgraphs) | **[AS-BUILT]** `runtime/cache.py` |
| Query-plan reuse | parameterized Cypher so plans are cached | **[AS-BUILT]** always `$params` |

```python
# runtime/cache.py — application TTL cache (memory, or Redis when REDIS_URL set) [AS-BUILT]
from runtime.cache import get_named_cache, invalidate_all_named_caches

cache = get_named_cache("product_subgraph", ttl_seconds=60, maxsize=128)
data = cache.get_or_set("wm-001", lambda: expensive_load("wm-001"))
# after an ETL load, drop stale hot reads:
invalidate_all_named_caches()
```

```python
# Query-plan reuse: parameterize, never string-build ids into Cypher [AS-BUILT]
GOOD = "MATCH (p:Product {product_id: $id}) RETURN p"          # plan cached + injection-safe
BAD  = f"MATCH (p:Product {{product_id: '{pid}'}}) RETURN p"    # recompile + injection risk
```

### Step 4 — Partitioning & sharding (hardest) [REFERENCE / NON-CLAIM]

Graphs don't shard cleanly like relational rows — the whole value is that related things are connected, so a naive split forces cross-network hops on every traversal.

- **Property sharding** ("Infinigraph", 2025.12 line): keep nodes+relationships together on a shard (traversal never hops the network for the *connection*), shard only heavy **property** data.
- **Composite databases** (formerly Fabric): one query spanning separate databases — good for **federating distinct domains** (Product/ErrorCode vs Customer/Claims), not splitting one logical graph in half.
- **Analytics clustering**: a separate read tier for heavy GDS runs so a long algorithm doesn't fight live traffic.

**Practical rule:** reach for sharding only after vertical + replicas are genuinely exhausted. Most teams shard too early and pay complexity for nothing.

**[AS-BUILT]** logical partition **keys** only:

```python
# runtime/partitioning.py — logical keys shared by rate-limit + cache namespaces
def partition_for_request(*, tenant_id="default", product_id=None, **_):
    bits = [f"tenant={tenant_id or 'default'}"]
    if product_id:
        bits.append(f"product={product_id}")
    return "|".join(bits)          # e.g. "tenant=acme|product=wm-001"
```

### Step 5 — Concurrency happens at two layers

1. **Inside one algorithm** — an *algorithm choice*, not a setting: Dijkstra single-threaded; **Delta-Stepping** is the parallel alternative for the same job.
2. **Across requests** — what replicas / bounded pools solve: many simultaneous reads spread across processes.

```python
# runtime/concurrency.py — bounded parallel connector I/O [AS-BUILT]
from concurrent.futures import ThreadPoolExecutor

def parallel_map(items, fn, max_workers=4, preserve_order=True):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(fn, items)) if preserve_order else [f.result() for f in ex.map(fn, items)]
```

```python
# runtime/concurrency_limit.py — admission control (bulkhead) [AS-BUILT]
# cap in-flight /diagnose (default 32); acquire → work → ALWAYS release in finally.
```

**Say instead of over-claiming:** parallel **extract**, serial **transform**, sequential **MERGE** load; ranking inside one diagnosis stays **serial** for reproducibility.

### Step 6 — A sized reference topology [REFERENCE]

- Minimum viable cluster: **3 core** (write path, Raft quorum) + **2 read replicas per region**.
- Transaction-log disk ≈ **3× peak daily write volume** (disk-full on the tx log is a top avoidable outage).
- **Separate network interface** for causal-clustering heartbeat traffic.
- Route reads and writes through **separate paths** (LB→replicas for reads, HAProxy→core for writes).

## PART 3 — STRUCTURED, SEMI-STRUCTURED & UNSTRUCTURED → GRAPH

Five steps, per source. This is the pipeline that makes raw inputs obey the ontology.

### Step 1 — Structured (DBs, CSVs, parts catalogs)

Tools: **Neo4j-ETL** (infers a graph model from FK structure), **`LOAD CSV`** (+ APOC for batching/typing). Mapping is mechanical: a model row → `:Product`; a fault-code row → `:ErrorCode`; an FK link → a relationship.

```cypher
// Reference LOAD CSV shape (native Cypher) [REFERENCE]
LOAD CSV WITH HEADERS FROM 'file:///error_codes.csv' AS row
MERGE (e:ErrorCode {error_code_id: row.code})
SET e.description = row.description
```

```python
# [AS-BUILT] this repo's structured path: connectors → MERGE via populate_graph.py
def create_constraints(tx) -> None:
    for q in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ec:ErrorCode) REQUIRE ec.error_code_id IS UNIQUE",
        # … Symptom, FailureMode, DiagnosticStep, Part, Component, Asset, Claim, …
    ]:
        tx.run(q)
# populate_graph(): session.execute_write(create_constraints) FIRST, then MERGE entities.
```

### Step 2 — Semi-structured (JSON/XML, telemetry, tickets)

Tools: **APOC JSON/XML** procedures (nested shapes `LOAD CSV` can't), **Kafka + Neo4j sink** for continuous streams.

```cypher
// Reference APOC JSON load [REFERENCE]
CALL apoc.load.json('file:///work_orders.json') YIELD value
MERGE (w:WorkOrder {work_order_id: value.id})
SET w.status = value.status
```

```python
# [AS-BUILT] repo semi-structured extractor: CSV/JSONL → normalized staging rows
# graph/enterprise_pipeline/extractors/semi_structured.py  (work_orders.jsonl, parts_delta.csv)
```

### Step 3 — Unstructured (manuals, PDFs, transcripts, notes)

The hard case — and the point is to **constrain the LLM to your ontology**, not let it invent categories.

Tools, increasing DIY: **llm-graph-builder** (neo4j-labs UI) → **GraphRAG `SimpleKGBuilder`** (Python) → **LangChain `LLMGraphTransformer`** (lowest-level) → **unstructured.io** (clean the text first).

```python
# [REFERENCE] schema-BOUND extraction — the critical practice
from langchain_experimental.graph_transformers import LLMGraphTransformer
transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=["Product", "ErrorCode", "Symptom", "DiagnosticStep", "Resolution"],
    allowed_relationships=["CAN_EXHIBIT", "MAY_INDICATE", "CONFIRMED_BY", "LEADS_TO"],
)
docs = transformer.convert_to_graph_documents(clean_text_chunks)
# The model can only ever propose (:Symptom)-[:MAY_INDICATE]->(:ErrorCode) — never an invented type.
```

```python
# [AS-BUILT] repo unstructured path is deterministic (regex/heuristics), NOT an LLM:
# graph/enterprise_pipeline/extractors/unstructured_text.py → provisional symptoms / error codes.
```

**[NON-CLAIM]** "We extract graph triples from PDFs with an LLM." Today it is pattern/heuristic extraction; the schema-bound LLM block is the correct upgrade path (full NER is a documented roadmap gap).

### Step 4 — Strong node / weak node resolution

1. **Structured → strong nodes**: verified, from a system of record (`:Product` from the official catalog).
2. **LLM/unstructured → weak nodes**: plausible, schema-constrained, unverified until confirmed.
3. **Resolution pass** merges weak into strong for the same real-world thing ("engine idles rough" → existing "rough idle") via exact/fuzzy string + **embedding similarity** — not left as duplicates.

```python
# [AS-BUILT] identity resolution today = MERGE on the business key (idempotent upsert)
# + entity_delta comparing catalog ↔ Neo4j by those same keys:
delta = compute_product_entity_delta("esp-001", compare_env="production")  # NEW vs IN_SYNC
```

**[NON-CLAIM]** embedding/fuzzy weak-node merge is **not** implemented — dedupe is exact-key MERGE. The embedding-similarity resolver is the correct enhancement.

### Step 5 — Validate against the ontology before "real"

Neo4j does **not** enforce OWL restrictions natively — close the gap deliberately: does every new `:ErrorCode` have ≥1 `:CONFIRMED_BY`? Is a node accidentally two disjoint classes? Failures go to a **review queue** — flag, don't silently fix or drop.

```python
# [AS-BUILT] graph/enterprise_pipeline/ontology_validate.py — SHACL-*inspired* shape checks
MIN_SYMPTOMS = 1
MIN_FAILURE_MODES = 1
MIN_INDICATES_LINKS = 1   # every product needs ≥1 symptom→failure_mode with confidence
# + ALLOWED_LIST_KEYS map catalog keys → OWL classes; LINK_SPECS enforce referential integrity;
# run BEFORE materialize/promote — fail-closed.
```

```turtle
# [REFERENCE] the equivalent formal W3C SHACL shape (external engine — non-claim here)
:ErrorCodeShape a sh:NodeShape ;
    sh:targetClass :ErrorCode ;
    sh:property [ sh:path :confirmedBy ; sh:minCount 1 ] .
```

**[NON-CLAIM]** external SHACL/OWL reasoner in CI is roadmap; the repo uses a lightweight in-code validator.

## PART 4 — DOCKER, GITHUB ACTIONS, KUBERNETES

Three different jobs — not interchangeable.

### Step 1 — Docker packages (two uses) [AS-BUILT]

1. **Neo4j itself** in a container (official image) for local dev/test.
2. **Your pipeline code** — ETL, extraction, validation each as their own image.

```text
docker/Dockerfile.api · Dockerfile.etl · Dockerfile.frontend · Dockerfile.mock · Dockerfile.ui
docker/docker-compose.infra.yaml   # prod Neo4j :7687 + staging :7688 (+ Redis)
```

### Step 2 — GitHub Actions gates every change [AS-BUILT]

```yaml
# .github/workflows/ci.yml (excerpt) — merge-blocking gate
- name: Gitleaks secret scan
  uses: gitleaks/gitleaks-action@v2
- name: Ruff lint
  run: ruff check .
- name: Multi-source packs + TBox/ABox discipline (no Neo4j required)
  run: |
    pytest tests/test_multi_source_tbox_abox.py tests/test_pipeline_integration.py \
      tests/test_warranty_ontology.py tests/test_rdf_ontology_export.py -q
- name: Docs present for multi-source / TBox mechanism
  run: grep -q "TBox" docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md
```

Also present: `cd.yml` (**eval-gate** before deploy + opt-in Argo canary), `eval-nightly.yml`, CodeQL, Trivy, SBOM/provenance, cosign signing.

**Maps to the doc's four gates:** (1) ontology validation as a merge-block → the TBox/ABox + `rdf_ontology_export` pytest job; (2) golden-set eval on extraction → `evals/` smoke in CI; (3) scheduled ingestion → K8s CronJob (below); (4) Cypher/APOC changes ride the same build→test→deploy.

**[NON-CLAIM]** a dedicated Turtle-syntax + SHACL CI job is roadmap — validation runs as pytest, not a standalone SHACL step.

### Step 3 — Kubernetes runs it at scale [AS-BUILT skeleton]

- **Core Neo4j = StatefulSet** (stable network identity + own PVC each) — never a Deployment, because Raft needs stable identity across restarts.
- **Read replicas = separate, elastic pool** (HPA-style) — REFERENCE (not deployed).
- **Ingestion = CronJob** — the production home for batch ingestion.
- **Cluster heartbeat isolation = NetworkPolicy** — REFERENCE (not present today).

```yaml
# k8s/base/neo4j-statefulset.yaml (excerpt) [AS-BUILT — replicas: 1 in demo]
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: neo4j }
spec:
  serviceName: neo4j
  replicas: 1
  volumeClaimTemplates:
    - metadata: { name: neo4j-data }
      spec: { accessModes: ["ReadWriteOnce"] }
```

```yaml
# k8s/base/etl-cronjob.yaml (excerpt) [AS-BUILT]
apiVersion: batch/v1
kind: CronJob
metadata: { name: etl-pipeline }
spec:
  schedule: "0 2 * * *"          # nightly ingestion
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: etl
              image: ghcr.io/OWNER/REPO-diagnostics-etl:latest
```

**[NON-CLAIM]** Neo4j **Helm chart / Operator**, elastic **read-replica** pool, and a **NetworkPolicy** for heartbeat isolation are not in the repo — raw manifests + kustomize overlays (`k8s/overlays/staging|prod`) only, single Neo4j replica.

### Step 4 — How they chain end to end

```text
Change ontology rule / Cypher / extraction prompt
        │
        ▼
GitHub Actions: lint + TBox/ABox tests + eval + build image   ← merge-blocking gate
        │
        ▼
Image pushed to registry (Docker)
        │
        ▼
Kubernetes: rolling update of pipeline Deployment / CronJob picks up new image;
Neo4j StatefulSet keeps running unless the change targets cluster config
        │
        ▼
New data flows Part 3 Steps 1–5 → lands in Neo4j → validated before it is trusted
```

## PART 5 — THE CHECKLIST (recite it)

1. Decided **unweighted (`shortestPath()`)** vs **weighted (GDS + a named algorithm)** — not "Dijkstra by default".
2. GDS **projection** created before any GDS call.
3. **Page cache** sized to the working set before clustering or sharding.
4. Core-Replica cluster with an **odd** core count + tested **read/write path separation**.
5. Confirmed **property sharding / composite DBs** are actually justified, or replicas still have headroom.
6. Structured / semi / unstructured each mapped to Part 3's five steps, with **strong/weak** resolution for anything LLM-extracted.
7. **Ontology validation (SHACL or equivalent)** runs as a real check, not assumed.
8. **Docker** packages Neo4j + pipeline code; **Actions** gates every ontology/query/prompt change; **Kubernetes** runs core as a **StatefulSet** with replicas + ingestion **CronJobs**.

## PART 6 — SELF-QUIZ (no peeking)

1. Native `shortestPath()` vs GDS — which is weighted, which ships built in?
2. What must exist before any GDS algorithm call, and why does it trip people up?
3. Which algorithm gives parallel single-source shortest paths (not Dijkstra)?
4. Name the three caching layers.
5. Why is graph sharding harder than relational sharding?
6. What binds an LLM extractor to your five ontology classes?
7. Strong node vs weak node — which comes from a system of record?
8. Why is Neo4j core a StatefulSet and not a Deployment?

## PART 7 — FINAL BOSS TEST

1. Explain **Weighted-path → Scale-boring-first → Strong+Weak+Validate → Docker-gate-run** in under 90 seconds.
2. Write the GDS project → Dijkstra → drop sequence from a blank page.
3. Write `create_constraints` + one MERGE, and the `LLMGraphTransformer` schema-bound call.
4. Draw the Core-Replica topology with read/write path separation.
5. State three **non-claims** from this repo without notes.

## PART 8 — CODE & DOC MAP

| Concern | Location |
|---------|----------|
| Bounded diagnosis MATCH | `graph/graph_rag.py` |
| Unique indexes + MERGE | `graph/populate_graph.py` `create_constraints` |
| App cache (3rd layer) | `runtime/cache.py` |
| Partition keys | `runtime/partitioning.py` |
| Bounded parallel extract | `runtime/concurrency.py` |
| Admission control | `runtime/concurrency_limit.py` |
| Semi-structured extractor | `graph/enterprise_pipeline/extractors/semi_structured.py` |
| Unstructured extractor | `graph/enterprise_pipeline/extractors/unstructured_text.py` |
| Shape validation (SHACL-style) | `graph/enterprise_pipeline/ontology_validate.py` |
| Entity delta (strong/weak keys) | `graph/enterprise_pipeline/entity_delta.py` |
| Docker | `docker/Dockerfile.*`, `docker/docker-compose.infra.yaml` |
| CI gates | `.github/workflows/ci.yml`, `cd.yml`, `eval-nightly.yml` |
| K8s | `k8s/base/neo4j-statefulset.yaml`, `k8s/base/etl-cronjob.yaml`, `k8s/overlays/*` |
| Scale honesty | `docs/25-…`, `docs/17-…`, `docs/sdd/AS_BUILT.md` |

If you can recite the checklist and write the project→Dijkstra→drop sequence and the schema-bound extractor from memory, you understand how to **scale and populate** this graph truthfully.
"""


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
    Masterclass(
        id="mc-03-graph-ops-index-delta-scale",
        title="Master This Code: Graph Ops — Indexes, Delta, Partition, Concurrency, Sharding",
        subtitle="Memorize-It, Write-It, Explain-It — scale the KG without inventing Fabric",
        track="runtime",
        order=30,
        tags=["indexes", "delta", "partition", "concurrency", "sharding", "verbatim", "memorize"],
        estimated_minutes=55,
        body=_GRAPH_OPS_BODY,
    ),
    Masterclass(
        id="mc-04-scaling-populating-kg",
        title="Master This Code: Scaling & Populating the Diagnostics Knowledge Graph",
        subtitle="Memorize-It, Write-It, Explain-It — traversal, high-volume scale, the full data pipeline, Docker/Actions/K8s",
        track="runtime",
        order=40,
        tags=[
            "shortest-path",
            "gds",
            "scaling",
            "clustering",
            "pipeline",
            "shacl",
            "docker",
            "kubernetes",
            "verbatim",
            "memorize",
        ],
        estimated_minutes=70,
        body=_SCALING_POPULATE_BODY,
    ),
]

_BY_ID = {m.id: m for m in MASTERCLASSES}


def list_masterclasses() -> list[dict]:
    return [m.summary() for m in sorted(MASTERCLASSES, key=lambda m: m.order)]


def get_masterclass(mc_id: str) -> Masterclass | None:
    return _BY_ID.get(mc_id)
