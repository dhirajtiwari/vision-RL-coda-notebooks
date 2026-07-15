"""Generate study modules from free-form docs (md, txt, ipynb, turtle, cypher)."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

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

_HEADER_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.M)
_FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)
_TERM_RE = re.compile(
    r"\b(TBox|ABox|OWL|RDF|SHACL|Cypher|SPARQL|LangGraph|Redis|Neo4j|"
    r"GraphRAG|Bayes|FMEA|partition|cache|thread|replica|INDICATES)\b",
    re.I,
)


def _slugify(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return s[:60] or f"module-{uuid.uuid4().hex[:8]}"


def _detect_language(fence_lang: str, code: str) -> str:
    fl = (fence_lang or "").lower()
    if fl in {"python", "py"}:
        return "python"
    if fl in {"cypher", "cql"}:
        return "cypher"
    if fl in {"turtle", "ttl", "rdf"}:
        return "turtle"
    if fl in {"sparql", "rq"}:
        return "sparql"
    if fl in {"ts", "tsx", "typescript"}:
        return "typescript"
    if fl in {"bash", "sh", "shell"}:
        return "bash"
    # heuristics
    if "MATCH (" in code or "CREATE (" in code or "MERGE (" in code:
        return "cypher"
    if "@prefix" in code or "owl:Class" in code or "a owl:" in code:
        return "turtle"
    if "SELECT" in code and "WHERE" in code and "{" in code:
        return "sparql"
    if "def " in code or "import " in code or "class " in code:
        return "python"
    return "text"


def _annotations_for_code(code: str, language: str) -> list[LineAnnotation]:
    notes: list[LineAnnotation] = []
    for i, line in enumerate(code.splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        note = None
        if language == "python":
            if s.startswith("from ") or s.startswith("import "):
                note = "Import — brings a library/module into scope."
            elif s.startswith("def ") or s.startswith("async def "):
                note = "Function definition — a reusable unit of work."
            elif s.startswith("class "):
                note = "Class / TypedDict — shapes state or domain objects."
            elif "StateGraph" in s:
                note = "LangGraph blueprint — nodes and edges for the agent."
            elif "@tool" in s:
                note = "Tool decorator — exposes a callable the agent can invoke."
            elif "try:" in s:
                note = "Defensive block — catch failures from dynamic queries."
        elif language == "cypher":
            if s.upper().startswith("MATCH"):
                note = "MATCH — pattern search over graph nodes/relationships."
            elif s.upper().startswith("CREATE") or s.upper().startswith("MERGE"):
                note = "Write path — create or upsert graph structure."
            elif s.upper().startswith("RETURN"):
                note = "RETURN — project result columns to the caller."
            elif s.upper().startswith("WHERE"):
                note = "WHERE — filter matched paths."
            elif "$" in s:
                note = "Parameter — never string-interpolate user input into Cypher."
        elif language == "turtle":
            if "owl:Class" in s or "a owl:Class" in s:
                note = "TBox class declaration."
            elif "ObjectProperty" in s:
                note = "Object property — edge between two resources."
            elif "DatatypeProperty" in s:
                note = "Datatype property — literal attribute."
            elif "owl:equivalentClass" in s or "owl:disjointWith" in s:
                note = "OWL axiom — logical rule beyond plain RDF facts."
        elif language == "sparql":
            if s.upper().startswith("SELECT"):
                note = "SELECT — variables to return."
            elif s.upper().startswith("WHERE") or s == "{":
                note = "WHERE graph pattern — triple patterns to match."
            elif s.upper().startswith("PREFIX"):
                note = "PREFIX — short name for a namespace IRI."
        if note:
            notes.append(LineAnnotation(line=i, note=note))
        if len(notes) >= 12:
            break
    return notes


def _line_quiz_for_code(code: str, language: str) -> list[LineQuizItem]:
    items: list[LineQuizItem] = []
    lines = code.splitlines()
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if len(s) < 8 or s.startswith("#"):
            continue
        # Keep meaningful lines only
        if (
            language == "python"
            and not any(
                k in s for k in ("def ", "class ", "import ", "return ", "StateGraph", "@tool", "MATCH", "invoke")
            )
            and i % 4 != 0
        ):
            continue
        prompt = f"What does line {i} do?"
        answer = s[:120]
        distractors = [
            "Declares a CSS style rule",
            "Opens a network socket only",
            "Deletes the database permanently",
        ]
        items.append(
            LineQuizItem(
                line=i,
                prompt=prompt,
                answer=answer,
                choices=[answer] + distractors,
                why=f"Exact source line: `{s[:80]}`",
            )
        )
        if len(items) >= 8:
            break
    return items


def _fill_blanks_for_code(code: str, language: str) -> FillBlanks | None:
    lines = [ln for ln in code.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if len(lines) < 3:
        return None
    # Blank distinctive tokens
    tokens: list[str] = []
    for ln in lines[:12]:
        for tok in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", ln):
            if tok.lower() in {
                "from",
                "import",
                "return",
                "class",
                "true",
                "false",
                "none",
                "with",
                "self",
                "this",
            }:
                continue
            if tok not in tokens:
                tokens.append(tok)
            if len(tokens) >= 5:
                break
        if len(tokens) >= 5:
            break
    if len(tokens) < 2:
        return None
    snippet = "\n".join(lines[:14])
    blanks: list[BlankSpec] = []
    template = snippet
    for idx, tok in enumerate(tokens[:5], start=1):
        bid = f"b{idx}"
        # replace first occurrence only
        template = template.replace(tok, "{{" + bid + "}}", 1)
        blanks.append(BlankSpec(id=bid, answer=tok, hint=f"{language} token"))
    return FillBlanks(template=template, blanks=blanks)


def _concepts_from_text(text: str) -> list[ConceptCard]:
    found = sorted({m.group(1) for m in _TERM_RE.finditer(text)}, key=str.lower)
    defs = {
        "tbox": ("Terminological Box", "Shared schema: classes & properties (rule book)."),
        "abox": ("Assertional Box", "Instance facts about specific products/assets."),
        "owl": ("Web Ontology Language", "Formal ontology language built on Description Logic."),
        "rdf": ("Resource Description Framework", "Triple model: subject–predicate–object."),
        "shacl": ("Shapes Constraint Language", "Closed-world validation of instance data."),
        "cypher": ("Neo4j query language", "Pattern matching over property graphs."),
        "sparql": ("SPARQL Protocol and RDF Query Language", "Query language for RDF graphs."),
        "langgraph": ("LangGraph", "Stateful agent workflows as graphs of nodes/edges."),
        "redis": ("Redis", "In-memory store for shared cache, rate limits, locks."),
        "neo4j": ("Neo4j", "Property graph database used as operational ABox."),
        "graphrag": ("GraphRAG", "Retrieve typed graph evidence then ground an answer."),
        "bayes": ("Bayesian ranking", "Posterior ∝ prior × product of likelihoods."),
        "fmea": ("Failure Mode Effects Analysis", "Severity/Occurrence/Detection risk signals."),
        "partition": ("Partitioning", "Split work/keys for scale and isolation."),
        "cache": ("Caching", "Reuse hot results to cut latency and load."),
        "thread": ("Concurrency", "Parallel work with careful shared-state rules."),
        "replica": ("Read replica", "Scale reads while writes go to primary."),
        "indicates": ("INDICATES edge", "Symptom → FailureMode likelihood link."),
    }
    cards: list[ConceptCard] = []
    for term in found[:16]:
        key = term.lower()
        meta = defs.get(key)
        if meta:
            cards.append(ConceptCard(term=meta[0], definition=meta[1], analogy=""))
        else:
            cards.append(ConceptCard(term=term, definition=f"Key concept: {term}"))
    return cards


def _quiz_from_markdown(text: str) -> list[QuizItem]:
    items: list[QuizItem] = []
    # Q: / A: pairs
    for m in re.finditer(
        r"(?:^|\n)\s*(?:Q[:.]|\d+\.)\s*(.+?)(?:\n\s*A[:.]\s*(.+?))?(?=\n\s*(?:Q[:.]|\d+\.)|\Z)", text, re.S
    ):
        q = m.group(1).strip()
        a = (m.group(2) or "").strip()
        if len(q) > 12:
            items.append(QuizItem(q=q[:400], a=a[:600] or "See module story and beats.", difficulty="medium"))
        if len(items) >= 12:
            break
    if items:
        return items
    # Fallback: ask about headers
    headers = [h.strip() for _, h in _HEADER_RE.findall(text)][:8]
    for h in headers:
        items.append(
            QuizItem(
                q=f"In one sentence, what is «{h}» about?",
                a=f"Explain the core idea of section «{h}» from the uploaded material.",
                difficulty="easy",
            )
        )
    return items


def extract_text_from_ipynb(raw: str) -> str:
    nb = json.loads(raw)
    parts: list[str] = []
    for cell in nb.get("cells", []):
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "markdown":
            parts.append(src)
        elif cell.get("cell_type") == "code":
            parts.append("```python\n" + src + "\n```")
    return "\n\n".join(parts)


def generate_module_from_text(
    text: str,
    *,
    title: str = "",
    tags: list[str] | None = None,
    source: str = "upload",
    filename: str = "",
) -> StudyModule:
    text = text.strip()
    if not text:
        raise ValueError("Empty document — nothing to generate.")

    # Title
    first_header = next((h for _, h in _HEADER_RE.findall(text)), None)
    mod_title = title.strip() or first_header or Path(filename).stem or "Uploaded study module"
    mod_id = _slugify(mod_title)

    # Story = first long markdown paragraph
    story_parts = []
    for block in re.split(r"\n{2,}", text):
        if block.strip().startswith("#") or block.strip().startswith("```"):
            continue
        if len(block.strip()) > 80:
            story_parts.append(block.strip())
        if len(story_parts) >= 2:
            break
    story = "\n\n".join(story_parts)[:2000] or (
        f"Study module generated from «{mod_title}». Retell the story, then write the beats from memory."
    )

    fences = list(_FENCE_RE.finditer(text))
    beats: list[CodeBeat] = []
    if fences:
        for i, m in enumerate(fences, start=1):
            lang = _detect_language(m.group(1), m.group(2))
            code = m.group(2).strip("\n")
            if len(code.strip()) < 5:
                continue
            # Narrative: nearest previous header
            head = first_header or f"Beat {i}"
            before = text[: m.start()]
            heads = _HEADER_RE.findall(before)
            if heads:
                head = heads[-1][1].strip()
            beat_id = f"b{i:02d}"
            beats.append(
                CodeBeat(
                    id=beat_id,
                    title=head[:120],
                    language=lang,  # type: ignore[arg-type]
                    narrative=f"Master this {lang} fragment. Annotate each critical line, then hide it and rewrite.",
                    code=code[:8000],
                    annotations=_annotations_for_code(code, lang),
                    line_quiz=_line_quiz_for_code(code, lang),
                    fill_blanks=_fill_blanks_for_code(code, lang),
                )
            )
            if len(beats) >= 20:
                break
    else:
        # Prose-only: one text beat
        beats.append(
            CodeBeat(
                id="b01",
                title="Core narrative",
                language="text",
                narrative="Rewrite this section from memory after one careful read.",
                code=text[:4000],
                annotations=[LineAnnotation(line=1, note="Start of the section to memorize.")],
                line_quiz=[],
                fill_blanks=None,
            )
        )

    concepts = _concepts_from_text(text)
    quiz = _quiz_from_markdown(text)
    mistakes = [
        "Skimming code without saying each line's job out loud.",
        "Memorizing syntax without the story (why this exists).",
        "Confusing schema (TBox) with instances (ABox).",
    ]
    boss = [
        f"Explain «{mod_title}» in under 90 seconds.",
        "Write the most important code beat from a blank page.",
        "List three mistakes someone would make implementing this.",
    ]

    auto_tags = list(tags or [])
    for c in concepts[:6]:
        t = c.term.lower().replace(" ", "-")
        if t not in auto_tags:
            auto_tags.append(t)

    return StudyModule(
        id=mod_id if not mod_id.startswith(("01-", "02-", "03-")) else f"u-{mod_id}",
        title=mod_title,
        description=f"Upload-generated module from {filename or 'paste'} (not hand-authored).",
        tags=auto_tags[:12],
        track="foundations",
        story=story,
        one_liner=f"Review then rewrite: {mod_title}.",
        why_it_matters=["You uploaded this — edit say-aloud lines after first pass."],
        say_aloud=[
            f"This module is about {mod_title}.",
            "I will retell the story, then rewrite the main code beat.",
        ],
        cheat_sheet=[{"term": c.term, "meaning": c.definition} for c in concepts[:8]],
        beats=beats,
        concepts=concepts,
        self_quiz=quiz,
        common_mistakes=mistakes,
        final_boss=boss,
        source=source,
        order=500,
        estimated_minutes=max(20, min(90, 10 * len(beats))),
        grounded=False,
    )


def generate_from_bytes(filename: str, data: bytes, *, title: str = "", tags: list[str] | None = None) -> StudyModule:
    name = filename or "upload.md"
    lower = name.lower()
    raw = data.decode("utf-8", errors="replace")
    if lower.endswith(".ipynb"):
        text = extract_text_from_ipynb(raw)
        source = "notebook"
    else:
        text = raw
        source = "upload"
    return generate_module_from_text(text, title=title, tags=tags, source=source, filename=name)
