#!/usr/bin/env python3
"""
Generate multi-volume PDFs for the full WarrantyGraph project.

Volumes:
  00 Master Index
  01 Architecture & System Map
  02 Algorithms & Theory  (FMEA, Bayes, TF-IDF, GraphRAG, parts)
  03 Code Deep-Dive (annotated what/why)
  04 Ontology RDF OWL Turtle
  05 Pipelines Deploy Tests Data

Usage:
  python docs/multi-volume/generate_all_volumes.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
PNG = ROOT / "docs" / "graphviz" / "rendered" / "png"
TTL_SCHEMA = ROOT / "docs" / "ontology" / "warranty-diagnosis-schema.ttl"
OWL_SAMPLE = ROOT / "docs" / "ontology" / "warranty-diagnosis.owl"

TEAL_DARK = colors.HexColor("#134e4a")
NAVY = colors.HexColor("#1e3a5f")
SLATE = colors.HexColor("#334155")
LIGHT = colors.HexColor("#f8fafc")
CODE_BG = colors.HexColor("#0f172a")
AMBER = colors.HexColor("#fff7ed")
BLUE = colors.HexColor("#eff6ff")
GREEN = colors.HexColor("#f0fdf4")
BORDER = colors.HexColor("#cbd5e1")


def styles():
    b = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle(
            "c", parent=b["Title"], fontSize=18, textColor=TEAL_DARK, alignment=TA_CENTER, leading=22
        ),
        "sub": ParagraphStyle("s", parent=b["Normal"], fontSize=10, textColor=SLATE, alignment=TA_CENTER, leading=13),
        "h1": ParagraphStyle(
            "h1", parent=b["Heading1"], fontSize=13, textColor=TEAL_DARK, spaceBefore=8, spaceAfter=5, leading=16
        ),
        "h2": ParagraphStyle(
            "h2", parent=b["Heading2"], fontSize=11, textColor=NAVY, spaceBefore=7, spaceAfter=3, leading=13
        ),
        "h3": ParagraphStyle(
            "h3", parent=b["Heading3"], fontSize=9.5, textColor=SLATE, spaceBefore=5, spaceAfter=2, leading=12
        ),
        "body": ParagraphStyle(
            "body",
            parent=b["Normal"],
            fontSize=8.5,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_JUSTIFY,
            leading=11,
            spaceAfter=3,
        ),
        "small": ParagraphStyle("sm", parent=b["Normal"], fontSize=7.5, textColor=SLATE, leading=10, spaceAfter=2),
        "bullet": ParagraphStyle("bu", parent=b["Normal"], fontSize=8, leading=10.5),
        "code": ParagraphStyle(
            "co", parent=b["Code"], fontSize=6.5, textColor=colors.HexColor("#e2e8f0"), leading=8.2, fontName="Courier"
        ),
        "why": ParagraphStyle("why", parent=b["Normal"], fontSize=8, textColor=TEAL_DARK, leading=10.5, leftIndent=2),
        "center": ParagraphStyle("ce", parent=b["Normal"], fontSize=8, alignment=TA_CENTER, textColor=SLATE),
        "math": ParagraphStyle(
            "math",
            parent=b["Normal"],
            fontSize=9,
            textColor=NAVY,
            alignment=TA_CENTER,
            leading=12,
            spaceBefore=3,
            spaceAfter=3,
        ),
    }


def footer_factory(title: str):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(12 * mm, 10 * mm, A4[0] - 12 * mm, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawCentredString(A4[0] / 2, 5.5 * mm, f"{title}  ·  p.{doc.page}")
        canvas.restoreState()

    return footer


def tbl(headers, rows, st, widths):
    data = [[Paragraph(f"<font color='white'><b>{h}</b></font>", st["small"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), st["small"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_DARK),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    return t


def bullets(items, st):
    return ListFlowable(
        [ListItem(Paragraph(i, st["bullet"]), leftIndent=5, value="•") for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=8,
        spaceAfter=3,
    )


def code_block(text: str, st, max_lines: int = 45):
    lines = text.rstrip().splitlines()[:max_lines]
    if len(text.rstrip().splitlines()) > max_lines:
        lines.append("…")
    paras = [Paragraph((ln.replace(" ", "&nbsp;").replace("<", "&lt;") or "&nbsp;"), st["code"]) for ln in lines]
    box = Table([[p] for p in paras], colWidths=[176 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (0, 0), 4),
                ("BOTTOMPADDING", (0, -1), (0, -1), 4),
                ("TOPPADDING", (0, 1), (-1, -2), 0.4),
                ("BOTTOMPADDING", (0, 1), (-1, -2), 0.4),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 3)])


def why_box(title: str, body: str, st, bg=AMBER):
    p = Paragraph(f"<b>{title}</b><br/>{body}", st["why"])
    box = Table([[p]], colWidths=[176 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 3)])


def wwwh(st, what: str, where: str, when: str, how: str, why: str):
    """What / Where / When / How / Why card used across volumes."""
    rows = [
        ("WHAT", what),
        ("WHERE", where),
        ("WHEN", when),
        ("HOW", how),
        ("WHY", why),
    ]
    data = []
    for label, text in rows:
        data.append(
            [
                Paragraph(f"<b>{label}</b>", st["small"]),
                Paragraph(text, st["small"]),
            ]
        )
    t = Table(data, colWidths=[18 * mm, 158 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return KeepTogether([t, Spacer(1, 4)])


def img(name, st, cap=None, max_h=78):
    path = PNG / name
    out = []
    if not path.exists():
        out.append(Paragraph(f"<i>[diagram {name} not rendered]</i>", st["small"]))
        return out
    im = Image(str(path))
    max_w, max_hh = 176 * mm, max_h * mm
    aspect = im.imageHeight / float(im.imageWidth)
    w, h = max_w, max_w * aspect
    if h > max_hh:
        h = max_hh
        w = h / aspect
    im.drawWidth, im.drawHeight = w, h
    out += [im]
    if cap:
        out.append(Paragraph(f"<i>{cap}</i>", st["center"]))
    out.append(Spacer(1, 3))
    return out


def cover(story, st, vol: str, title: str, subtitle: str):
    story.append(Spacer(1, 28 * mm))
    story.append(Paragraph(f"Volume {vol}", st["sub"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("WarrantyGraph", st["cover"]))
    story.append(Paragraph(title, st["cover"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(subtitle, st["sub"]))
    story.append(Spacer(1, 8 * mm))
    story.append(
        why_box(
            "Full project library",
            "This multi-volume set covers the entire repository — not a single session. "
            "Algorithms, theory, annotated code, RDF/OWL, pipelines, and deploy are all included.",
            st,
            BLUE,
        )
    )
    story.append(PageBreak())


def build_pdf(path: Path, title: str, build_fn):
    st = styles()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=11 * mm,
        bottomMargin=13 * mm,
        title=title,
        author="WarrantyGraph Project",
    )
    story: list = []
    build_fn(story, st)
    doc.build(story, onFirstPage=footer_factory(title), onLaterPages=footer_factory(title))
    print(f"Wrote {path} ({path.stat().st_size // 1024} KB)")


# ═══════════════════════════════════════════════════════════════════════════
# VOLUME 00 — Master Index
# ═══════════════════════════════════════════════════════════════════════════


def vol00(story, st):
    cover(
        story,
        st,
        "00",
        "Master Index",
        "Reading map for the multi-volume technical library",
    )
    story.append(Paragraph("1. Volume map", st["h1"]))
    story.append(
        tbl(
            ["Vol", "Title", "Read when you need…"],
            [
                ["00", "Master Index", "Orientation"],
                ["01", "Architecture & System Map", "Layers, packages, APIs, network"],
                ["02", "Algorithms & Theory", "FMEA, Bayes, TF-IDF, GraphRAG math"],
                ["03", "Code Deep-Dive", "Real code + what it does + why"],
                ["04", "Ontology RDF OWL Turtle", "Formal schema & serializations"],
                ["05", "Pipelines Deploy Tests Data", "ETL, k8s, evals, fixtures"],
            ],
            st,
            [14 * mm, 55 * mm, 107 * mm],
        )
    )
    story.append(Paragraph("2. Recommended reading orders", st["h1"]))
    story.append(
        bullets(
            [
                "<b>New engineer:</b> 01 → 03 (services+graph_rag) → 05 runbook → 02 algorithms",
                "<b>Data scientist / academic:</b> 02 first → 04 ontology → 03 reliability.py",
                "<b>Architect:</b> 01 → 05 deploy → 02 ranking design → 04 schema contract",
                "<b>Interview prep:</b> 02 theory whiteboard → 03 diagnose path → docs/interview PDF",
            ],
            st,
        )
    )
    story.append(Paragraph("3. Core idea in one paragraph", st["h1"]))
    story.append(
        Paragraph(
            "WarrantyGraph turns appliance failure knowledge into a <b>Neo4j property graph</b>. "
            "At runtime it matches free-text symptoms, ranks failure modes with <b>FMEA + naive Bayes</b>, "
            "walks diagnostic trees and BOM edges for parts, and returns explainable confidence with provenance. "
            "Knowledge is ETL’d from enterprise-like sources; LLM is optional and off by default.",
            st["body"],
        )
    )
    story.append(Paragraph("4. Ports & entrypoints", st["h1"]))
    story.append(
        tbl(
            ["Service", "Port / command"],
            [
                ["Next.js UI", ":3000 — frontend/ npm run dev"],
                ["FastAPI", ":8080 — uvicorn api.main:app"],
                ["Neo4j", ":7687 Bolt — populate_graph.py"],
                ["Mock enterprise", ":8090 — simulation.mock_enterprise_apps"],
                ["Redis optional", ":6379 — REDIS_URL"],
                ["ETL spine", "python -m graph.enterprise_pipeline.orchestrator"],
            ],
            st,
            [45 * mm, 131 * mm],
        )
    )
    story.append(Paragraph("5. How every topic is documented (WWWH)", st["h1"]))
    story.append(
        Paragraph(
            "Across volumes we use a fixed lens: <b>What</b> (plain English) · "
            "<b>Where</b> (file/package) · <b>When</b> (batch vs request) · "
            "<b>How</b> (mechanism) · <b>Why</b> (design reason). "
            "Indexes: see Vol 05 §Indexes and docs/19-Indexes-Constraints-and-Lookup-Performance.md.",
            st["body"],
        )
    )
    story.append(
        wwwh(
            st,
            "Uniqueness constraints + SQLite PKs/status indexes",
            "populate_graph.create_constraints · utils/persistence.py",
            "Constraints on every graph load; SQLite on first ops DB open",
            "Neo4j UNIQUE on *_id; SQLite PRIMARY KEY + idx_*_status",
            "Fast id seeks, no duplicate entities, agent list filters",
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# VOLUME 01 — Architecture
# ═══════════════════════════════════════════════════════════════════════════


def vol01(story, st):
    cover(story, st, "01", "Architecture &amp; System Map", "Layers, packages, APIs, topology")
    story.append(Paragraph("1. Problem &amp; solution", st["h1"]))
    story.append(
        Paragraph(
            "Warranty agents need consistent, explainable diagnosis: which failure mode, which part, "
            "is it covered? The system encodes OEM knowledge as a graph and serves multi-hop reasoning "
            "via GraphRAG — not free-form LLM invention.",
            st["body"],
        )
    )
    story.append(Paragraph("2. Six layers", st["h1"]))
    story.append(
        tbl(
            ["Layer", "Packages", "Job"],
            [
                ["L6 Experience", "frontend/", "Chat, explorer, claims, ops"],
                ["L5 Orchestration", "services/, agents/, integrations/", "Warranty, LangGraph, claims"],
                ["L4 Intelligence", "graph_rag, reliability, parts, trees", "Score & explain"],
                ["L3 Integration", "connectors, simulation", "PIM/CRM/FSM/Claims"],
                ["L2 Graph store", "neo4j_client, populate_graph", "MERGE + Cypher"],
                ["L1 Data platform", "ETL, OEM catalog, fixtures", "Author & load knowledge"],
            ],
            st,
            [32 * mm, 58 * mm, 86 * mm],
        )
    )
    story.extend(img("39-complete-enterprise-system-pipeline.png", st, "Complete pipeline", 72))
    story.extend(img("40-enterprise-network-topology.png", st, "Network topology", 70))
    story.append(Paragraph("3. Package map (entire repo)", st["h1"]))
    story.append(
        bullets(
            [
                "<b>api/</b> REST · <b>services/</b> business path · <b>agents/</b> LangGraph",
                "<b>graph/</b> intelligence + enterprise_pipeline ETL + OEM catalog",
                "<b>integrations/</b> CRM, warranty, claims, cases · <b>simulation/</b> mock :8090",
                "<b>runtime/</b> cache/Redis/concurrency · <b>guardrails/</b> safety",
                "<b>observability/</b> logs/metrics/traces · <b>gateway/</b> optional LLM",
                "<b>frontend/</b> Next.js · <b>evals/</b> + <b>tests/</b> quality",
                "<b>docker/ k8s/ deploy/ monitoring/ security/</b> production shape",
            ],
            st,
        )
    )
    story.append(Paragraph("4. HTTP API surface", st["h1"]))
    story.append(
        tbl(
            ["Method", "Path", "Why it exists"],
            [
                ["POST", "/diagnose", "Primary customer diagnosis"],
                ["GET", "/graph/*", "Explorer + schema + path subgraphs"],
                ["*/claims*", "Warranty claim lifecycle"],
                ["GET", "/health /metrics", "Ops readiness + Prometheus"],
                ["*/admin/pipeline/*", "ETL dry-run, validate, promote (gated)"],
            ],
            st,
            [22 * mm, 48 * mm, 106 * mm],
        )
    )
    story.append(Paragraph("5. Online vs batch", st["h1"]))
    story.append(
        code_block(
            "ONLINE: UI → API → diagnosis_service → LangGraph → graph_rag → Neo4j\n"
            "BATCH:  connectors → OntologyBuilder → catalog JSON → smoke → promote → MERGE",
            st,
        )
    )
    story.append(Paragraph("6. Core subsystems in What/Where/When/How/Why form", st["h1"]))
    story.append(
        wwwh(
            st,
            "POST /diagnose — customer diagnosis response",
            "api/main.py → services/diagnosis_service.py → agents + graph_rag",
            "Every agent/customer diagnosis request",
            "Guardrails → CRM/warranty → LangGraph → Cypher + FMEA/Bayes → format",
            "Single explainable path; no LLM required for facts",
        )
    )
    story.append(
        wwwh(
            st,
            "Knowledge load into Neo4j",
            "populate_graph.py · orchestrator · staging_promotion",
            "Batch / admin promote / CLI — not per diagnose",
            "create_constraints then MERGE nodes & relationships",
            "Idempotent catalog materialization for multi-hop reads",
        )
    )
    story.append(
        wwwh(
            st,
            "Neo4j unique indexes (via constraints)",
            "graph/populate_graph.py create_constraints",
            "Start of every populate_graph()",
            "REQUIRE product_id, symptom_id, failure_mode_id, … IS UNIQUE",
            "Index seek on MATCH {id:$x}; prevent duplicates",
        )
    )
    story.append(
        wwwh(
            st,
            "Optional Redis shared state",
            "runtime/redis_client.py · rate_limit · cache · budget · concurrency_limit",
            "When REDIS_URL is set and Redis reachable; else memory fallback",
            "Shared keys for multi-pod rate/cache/admission",
            "Correct multi-replica behavior without sticky sessions",
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# VOLUME 02 — Algorithms & Theory
# ═══════════════════════════════════════════════════════════════════════════


def vol02(story, st):
    cover(
        story,
        st,
        "02",
        "Algorithms &amp; Theory",
        "FMEA · Bayesian diagnosis · TF-IDF hybrid · GraphRAG · parts scoring",
    )

    # FMEA
    story.append(Paragraph("1. FMEA / FMECA (reliability engineering)", st["h1"]))
    story.append(
        Paragraph(
            "<b>What:</b> Failure Mode and Effects Analysis rates each failure mode on ordinal scales "
            "Severity (S), Occurrence (O), Detection (D). Classic <b>RPN = S × O × D</b>. "
            "Standards: MIL-STD-1629A, SAE J1739, AIAG-VDA FMEA Handbook 2019.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Why:</b> Industry-defensible triage instead of opaque ML scores. "
            "AIAG-VDA prefers <b>Action Priority (H/M/L)</b> because multiplying ordinals can reverse ranks "
            "(Kmenta &amp; Ishii, 2004).",
            st["body"],
        )
    )
    story.append(Paragraph("How we ground S / O / D in the graph", st["h2"]))
    story.append(
        tbl(
            ["Factor", "Graph source", "Mapping idea"],
            [
                ["Severity S", "Worst Symptom.severity on INDICATES path", "critical→10, high→8, medium→5, low→2"],
                ["Occurrence O", "Count Claim|HistoricalResolution -CONFIRMED→ FM", "More field evidence → higher O"],
                [
                    "Detection D",
                    "Count DiagnosticStep -CONFIRMS→ FM (+ error codes)",
                    "More coverage → easier detect → lower D",
                ],
                ["RPN", "S*O*D", "Continuity with classic FMEA"],
                ["Action Priority", "Severity-dominated rules", "High/Medium/Low triage"],
            ],
            st,
            [32 * mm, 72 * mm, 72 * mm],
        )
    )
    story.append(Paragraph("Formulas", st["h2"]))
    story.append(Paragraph("RPN = S × O × D &nbsp;&nbsp;(range 1…1000)", st["math"]))
    story.append(
        why_box(
            "Code",
            "Implemented in <font face='Courier'>graph/reliability.py</font>: "
            "severity_rating, occurrence_rating, detection_rating, rpn, action_priority.",
            st,
            GREEN,
        )
    )

    # Bayes
    story.append(Paragraph("2. Naive-Bayes diagnostic inference", st["h1"]))
    story.append(
        Paragraph(
            "<b>What:</b> Given observed symptoms S, rank failure modes by posterior probability. "
            "References: Pearl (1988); Russell &amp; Norvig AIMA.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "P(fm | S)  ∝  P(fm)  ×  ∏ᵢ  P(sᵢ | fm)",
            st["math"],
        )
    )
    story.append(
        Paragraph(
            "Then <b>normalize</b> across candidate failure modes so posteriors sum to 1. "
            "This is a proper probability distribution over the differential diagnosis.",
            st["body"],
        )
    )
    story.append(
        tbl(
            ["Term", "Meaning in our system"],
            [
                ["P(fm) prior", "From FMEA Occurrence rating → occurrence_prior(O) = O/10 (relative only)"],
                ["P(s|fm) likelihood", "Edge (Symptom)-[:INDICATES {confidence}]->(FailureMode)"],
                ["Missing edge", "DEFAULT_MISS_LIKELIHOOD = 0.15 (not zero — avoids wipeout)"],
                ["Observed symptoms", "Strong matches ≥ symptom_match_min_score (not weak secondary)"],
            ],
            st,
            [40 * mm, 136 * mm],
        )
    )
    story.append(Paragraph("Worked mini-example (whiteboard)", st["h2"]))
    story.append(
        code_block(
            "Symptoms observed: s1, s2\n"
            "FM_A: prior=0.6, P(s1|A)=0.9, P(s2|A)=0.8  → score = 0.6*0.9*0.8 = 0.432\n"
            "FM_B: prior=0.4, P(s1|B)=0.3, P(s2|B)=0.5  → score = 0.4*0.3*0.5 = 0.060\n"
            "Normalize: P(A|S)=0.432/0.492≈0.88,  P(B|S)≈0.12  → rank A first",
            st,
        )
    )
    story.append(
        why_box(
            "Why not pure neural ranking?",
            "Warranty needs auditability and reproducibility. Same graph + symptoms ⇒ same posterior every time "
            "(unit-tested in tests/test_reliability.py).",
            st,
        )
    )

    # Dominance
    story.append(Paragraph("3. Dominance boost &amp; recommendation strength", st["h1"]))
    story.append(
        Paragraph(
            "A posterior of 0.57 vs second 0.33 is a clearer winner than 0.57 vs 0.55. "
            "<font face='Courier'>dominance_boost</font> gently raises overall confidence when "
            "top/second ratio ≥ 1.8 and top ≥ 0.55, capped (default 0.92) so we never claim false certainty.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>recommendation_strength</b> maps (posterior, graph edge strength, language match, dominance) "
            "to Strong / Moderate / Weak / Insufficient data — categorical triage like Action Priority.",
            st["body"],
        )
    )

    # TF-IDF
    story.append(Paragraph("4. Hybrid symptom retrieval (lexical + TF-IDF)", st["h1"]))
    story.append(
        Paragraph(
            "<b>Problem:</b> Users paraphrase catalog symptoms. Pure token overlap is brittle; full embeddings need extra infra.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>TF-IDF:</b> term frequency × inverse document frequency. Rare terms weigh more. "
            "Cosine similarity between query vector and symptom description vector.",
            st["body"],
        )
    )
    story.append(Paragraph("sim(q,d) = (q·d) / (‖q‖ ‖d‖) &nbsp; in TF-IDF space", st["math"]))
    story.append(
        Paragraph(
            "<b>Hybrid:</b> blended = 0.45·lexical + 0.55·tfidf; if both ≥ 0.3 take max (agreement boost). "
            "Threshold filter; backfill weak secondary matches for UI context only.",
            st["body"],
        )
    )
    story.append(
        why_box(
            "Code",
            "graph/symptom_retrieval.py · used by graph_rag.match_symptoms when use_hybrid_symptom_matching=true.",
            st,
            GREEN,
        )
    )

    # GraphRAG
    story.append(Paragraph("5. GraphRAG algorithm (runtime path)", st["h1"]))
    story.append(
        Paragraph(
            "GraphRAG here means: <b>retrieve multi-hop evidence from a knowledge graph</b>, then assemble an answer. "
            "It is not “chunk PDFs into a vector store” (though vectors could be added later).",
            st["body"],
        )
    )
    story.append(
        code_block(
            "diagnose(message, product_id?, asset_id?):\n"
            "  1. resolve_product_for_diagnosis  # message keywords / CRM asset / explicit id\n"
            "  2. match_error_codes + match_symptoms (hybrid scores)\n"
            "  3. strong_symptom_ids = score ≥ min_score  # only these enter Bayes\n"
            "  4. rank_failure_modes via Cypher INDICATES + FMEA/Bayes\n"
            "  5. composite confidence + dominance + recommendation_strength\n"
            "  6. diagnostic_engine tree for top FM\n"
            "  7. parts_predictor(fm_posterior)\n"
            "  8. escalation rules (critical / low conf / ambiguity margin)\n"
            "  9. format_diagnosis_response + provenance + subgraph",
            st,
        )
    )
    story.extend(img("04-graphrag-diagnosis.png", st, "GraphRAG diagnosis flow", 68))
    story.extend(img("38-reliability-diagnosis-engine.png", st, "Reliability engine (if present)", 55))

    # Parts
    story.append(Paragraph("6. Parts prediction scoring", st["h1"]))
    story.append(
        Paragraph(
            "prediction_score ≈ P(fm|symptoms) × source_reliability × P(part|fm)",
            st["math"],
        )
    )
    story.append(
        tbl(
            ["Source path", "Reliability weight", "Meaning"],
            [
                ["REQUIRES_PART edge", "1.00", "Engineering primary part link"],
                ["SKU_FIT", "0.90", "Compatible with asset SKU"],
                ["CLAIM_PRECEDENT", "0.85", "Used on past confirmed claims"],
                ["BOM_COMPONENT", "0.70", "Via IMPACTS_COMPONENT → REALIZED_BY"],
            ],
            st,
            [45 * mm, 35 * mm, 96 * mm],
        )
    )
    story.append(
        why_box(
            "Why multiply by FM posterior?",
            "A part for an unlikely failure mode must not outrank a part for the leading diagnosis. "
            "Parts never appear more likely than the FM they treat.",
            st,
        )
    )

    # Trees
    story.append(Paragraph("7. Diagnostic decision trees", st["h1"]))
    story.append(
        Paragraph(
            "Graph edges NEXT_STEP (with optional conditions), CONFIRMS, RULES_OUT form a troubleshooting automaton. "
            "Traversal is deterministic graph walk — not LLM planning. "
            "Ambiguity for escalation uses posterior margin between top-2 FMs (settings.diagnosis_ambiguity_margin).",
            st["body"],
        )
    )

    # Escalation theory
    story.append(Paragraph("8. Escalation decision logic (theory of when not to auto-resolve)", st["h1"]))
    story.append(
        bullets(
            [
                "Critical severity symptom → always human",
                "Low overall confidence AND not strong-graph → escalate",
                "Weak language match → escalate (wrong catalog mapping risk)",
                "Ambiguous posteriors (margin &lt; threshold) → escalate",
                "Strong graph evidence can avoid escalate even if language is imperfect",
            ],
            st,
        )
    )

    # Caching theory brief
    story.append(Paragraph("9. Systems algorithms (runtime scale)", st["h1"]))
    story.append(
        bullets(
            [
                "<b>Sliding-window rate limit:</b> count events in last W seconds; Redis ZSET + Lua for multi-pod",
                "<b>TTL cache:</b> store ontology/product subgraphs; invalidate on ETL load",
                "<b>Admission control:</b> semaphore / Redis INCR for max concurrent diagnoses",
                "<b>Parallel map:</b> thread pool for independent I/O (connectors); serial transform for determinism",
            ],
            st,
        )
    )

    story.append(Paragraph("10. Theory quick reference card", st["h1"]))
    story.append(
        tbl(
            ["Topic", "One-liner", "Module"],
            [
                ["FMEA", "S,O,D → RPN + Action Priority", "reliability.py"],
                ["Bayes", "P(fm|S)∝P(fm)∏P(s|fm), normalize", "reliability.bayesian_posteriors"],
                ["TF-IDF hybrid", "lexical + cosine TF-IDF blend", "symptom_retrieval.py"],
                ["GraphRAG", "Cypher multi-hop + assemble answer", "graph_rag.diagnose"],
                ["Parts", "posterior × reliability × edge P", "parts_predictor.py"],
                ["Dominance", "boost clear winners carefully", "dominance_boost"],
            ],
            st,
            [32 * mm, 78 * mm, 66 * mm],
        )
    )
    story.append(Paragraph("11. Algorithms as What/Where/When/How/Why", st["h1"]))
    story.append(
        wwwh(
            st,
            "FMEA S/O/D + RPN + Action Priority",
            "graph/reliability.py; wired from graph_rag._apply_fmea_and_posteriors",
            "During failure-mode ranking for each diagnose",
            "S=worst symptom severity; O=claim/resolution count; D=step/error coverage; RPN=S*O*D; AP rules",
            "Industry-defensible risk triage; Severity-led AP avoids pure RPN rank reversals",
        )
    )
    story.append(
        wwwh(
            st,
            "Naive-Bayes posterior over failure modes",
            "reliability.bayesian_posteriors",
            "After strong symptoms are selected (≥ min_score)",
            "score=P(fm)×∏P(s|fm); missing edge uses miss=0.15; normalize sum to 1",
            "Differential diagnosis as probability; deterministic & unit-tested",
        )
    )
    story.append(
        wwwh(
            st,
            "Hybrid lexical + TF-IDF symptom match",
            "symptom_retrieval.hybrid_symptom_score · graph_rag.match_symptoms",
            "Each diagnose after product is known",
            "Token overlap + TF-IDF cosine; blend weights; agreement boost",
            "Paraphrases without embedding infrastructure",
        )
    )
    story.append(
        wwwh(
            st,
            "Parts multi-source score",
            "parts_predictor.predict_parts",
            "After top FM chosen",
            "posterior × path reliability × edge probability; merge by part_id",
            "Part never outranks its failure mode; BOM + claims evidence",
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# VOLUME 03 — Code deep dive
# ═══════════════════════════════════════════════════════════════════════════


def vol03(story, st):
    cover(
        story,
        st,
        "03",
        "Code Deep-Dive (Annotated)",
        "What the code does and why — real excerpts from the repo",
    )

    story.append(Paragraph("1. Reliability engine — FMEA ratings", st["h1"]))
    story.append(Paragraph("<b>File:</b> graph/reliability.py", st["small"]))
    story.append(
        code_block(
            "def severity_rating(severities):\n"
            "    # WHAT: map symptom labels to FMEA 1-10, take WORST case\n"
            "    # WHY: safety-critical failures must dominate triage\n"
            "    ratings = [SEVERITY_SCALE.get(s.lower(), 5) for s in severities]\n"
            "    return max(ratings) if ratings else 5\n\n"
            "def occurrence_rating(evidence_count):\n"
            "    # WHAT: more closed claims/resolutions → higher O\n"
            "    # WHY: empirical prior from field data, not a magic constant\n"
            "    n = max(int(evidence_count), 0)\n"
            "    if n == 0: return 3\n"
            "    ...\n\n"
            "def detection_rating(diagnostic_step_count, error_code_count=0):\n"
            "    # WHAT: more CONFIRMS steps / codes → lower D (easier to detect)\n"
            "    # WHY: Detection must reflect actual diagnostic assets in the graph\n"
            "    coverage = step_count + error_code_count\n"
            "    ...",
            st,
        )
    )
    story.append(
        why_box(
            "Why pure functions?",
            "No I/O inside reliability.py → unit tests prove determinism without Neo4j " "(tests/test_reliability.py).",
            st,
            GREEN,
        )
    )

    story.append(Paragraph("2. Bayesian posteriors", st["h1"]))
    story.append(
        code_block(
            "def bayesian_posteriors(priors, likelihoods, observed_symptoms,\n"
            "                        candidate_failure_modes, miss_likelihood=0.15):\n"
            "    unnormalized = {}\n"
            "    for fm in candidate_failure_modes:\n"
            "        score = max(priors.get(fm, 0.0), 0.0)\n"
            "        for symptom in observed_symptoms:\n"
            "            # multiply likelihoods; missing edge uses miss_likelihood ≠ 0\n"
            "            score *= likelihoods.get((symptom, fm), miss_likelihood)\n"
            "        unnormalized[fm] = score\n"
            "    total = sum(unnormalized.values())\n"
            "    return {fm: score/total for fm, score in unnormalized.items()}  # normalize",
            st,
        )
    )
    story.append(
        why_box(
            "Why miss_likelihood=0.15?",
            "If miss=0, one unmatched symptom multiplies the score to zero and kills a good FM. "
            "Bounded-away-from-zero likelihoods keep inference stable.",
            st,
        )
    )

    story.append(Paragraph("3. Wiring FMEA + Bayes into ranking", st["h1"]))
    story.append(Paragraph("<b>File:</b> graph/graph_rag.py — _apply_fmea_and_posteriors", st["small"]))
    story.append(
        code_block(
            "def _apply_fmea_and_posteriors(ranked, symptom_ids):\n"
            "    for row in ranked:\n"
            "        sev = reliability.severity_rating(row.pop('severities') or [])\n"
            "        occ = reliability.occurrence_rating(row.pop('evidence_count') or 0)\n"
            "        det = reliability.detection_rating(row.pop('step_count') or 0)\n"
            "        row['rpn'] = reliability.rpn(sev, occ, det)\n"
            "        row['action_priority'] = reliability.action_priority(sev, occ, det)\n"
            "        row['_prior'] = reliability.occurrence_prior(occ)\n"
            "    # build likelihoods from INDICATES confidences collected in Cypher\n"
            "    posteriors = reliability.bayesian_posteriors(...)\n"
            "    # SORT: posterior DESC, then RPN, then link_count\n"
            "    ranked.sort(key=lambda x: (x['posterior'], x['rpn'], x['link_count']), reverse=True)",
            st,
        )
    )
    story.append(
        why_box(
            "Why sort by posterior first?",
            "Diagnosis is about which FM is most probable given symptoms. RPN is secondary triage risk, "
            "not the primary differential-diagnosis score.",
            st,
        )
    )

    story.append(Paragraph("4. Cypher that feeds the scorer", st["h1"]))
    story.append(
        code_block(
            "MATCH (p:Product {product_id:$pid})-[:CAN_HAVE]->(fm:FailureMode)\n"
            "OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\n"
            "WHERE s.symptom_id IN $symptom_ids\n"
            "WITH fm, collect(... indications ...), sum(ind.confidence) AS total_confidence,\n"
            "     [ (sv)-[:INDICATES]->(fm) | sv.severity ] AS severities,\n"
            "     size([ (fm)<-[:CONFIRMED]-(ev) | ev ]) AS evidence_count,\n"
            "     size([ (ds)-[:CONFIRMS]->(fm) | ds ]) AS step_count\n"
            "RETURN ...",
            st,
        )
    )
    story.append(
        Paragraph(
            "<b>What:</b> Pull candidate FMs for product with observed INDICATES edges and graph-derived S/O/D inputs. "
            "<b>Why:</b> All scoring inputs come from stored knowledge — not the LLM.",
            st["body"],
        )
    )

    story.append(Paragraph("5. Hybrid symptom matching", st["h1"]))
    story.append(Paragraph("<b>File:</b> graph/symptom_retrieval.py + match_symptoms", st["small"]))
    story.append(
        code_block(
            "def hybrid_symptom_score(user_message, symptom_description, *,\n"
            "                        lexical_score, corpus=None, lexical_weight=0.45):\n"
            "    semantic = tfidf_similarity(user_message, symptom_description, corp)\n"
            "    blended = lexical_weight * lexical_score + (1-lexical_weight) * semantic\n"
            "    if lexical_score >= 0.3 and semantic >= 0.3:\n"
            "        blended = max(blended, lexical_score, semantic)  # agreement boost\n"
            "    return min(blended, 1.0)\n\n"
            "# In match_symptoms: only score >= min_score count as Bayes evidence;\n"
            "# weaker matches may still show for UI context (secondary fill).",
            st,
        )
    )

    story.append(Paragraph("6. diagnose() orchestration", st["h1"]))
    story.append(
        code_block(
            "def diagnose(user_message, product_id=None, asset_id=None):\n"
            "    product, asset_ctx, ... = resolve_product_for_diagnosis(...)\n"
            "    matched_error_codes = match_error_codes(pid, user_message)\n"
            "    matched_symptoms = match_symptoms(pid, user_message)\n"
            "    strong_symptom_ids = [s for s in matched if score >= min_score]\n"
            "    ranked = rank_failure_modes_with_error_codes(...)\n"
            "    confidence, graph_c, lang_c, rec_strength, dom = _composite_confidence(...)\n"
            "    # escalation: critical OR (low conf AND (weak language OR ambiguous))\n"
            "    ambiguous = (top_post - second_post) < diagnosis_ambiguity_margin\n"
            "    parts = predict_parts(..., fm_posterior=top.posterior)\n"
            "    return DiagnosisResult(...)",
            st,
        )
    )
    story.append(
        why_box(
            "Why only strong symptoms for Bayes?",
            "Weak secondary matches are for display. Feeding them into ∏P(s|fm) would invent evidence "
            "and create competing FMs the user never really described.",
            st,
        )
    )

    story.append(Paragraph("7. Parts predictor", st["h1"]))
    story.append(
        code_block(
            "SOURCE_RELIABILITY = {\n"
            "  'REQUIRES_PART': 1.00, 'CLAIM_PRECEDENT': 0.85,\n"
            "  'BOM_COMPONENT': 0.70, 'SKU_FIT': 0.90,\n"
            "}\n"
            "# score = fm_posterior * reliability * edge_probability\n"
            "base_score = weight * SOURCE_RELIABILITY['REQUIRES_PART'] * (probability or 0.9)",
            st,
        )
    )

    story.append(Paragraph("8. Shared service + LangGraph + API", st["h1"]))
    story.append(
        code_block(
            "# services/diagnosis_service.py — single business path\n"
            "def run_full_diagnosis(...):\n"
            "    if warranty enriched and not eligible: return warranty_blocked\n"
            "    result = run_diagnosis(message, product_id, asset_id)  # LangGraph\n"
            "    if escalated and customer+asset: create_case_from_escalation(...)\n"
            "    return DiagnosisOutcome(...)\n\n"
            "# agents/diagnosis_graph.py\n"
            "detect_product → run_diagnosis → format_response → handle_escalation → END\n\n"
            "# api/main.py diagnose()\n"
            "slot = concurrency_limiter.try_acquire()\n"
            "message = guard_request(...)\n"
            "crm = enrich_session_from_crm(...); warranty = check_warranty_eligibility(...)\n"
            "outcome = run_full_diagnosis(...); validate_output(...)",
            st,
        )
    )
    story.append(
        why_box(
            "Why diagnosis_service exists?",
            "Historically API and UI could diverge. One function owns warranty + diagnosis + escalation policy.",
            st,
            GREEN,
        )
    )

    story.append(Paragraph("9. ETL transform snippet", st["h1"]))
    story.append(
        code_block(
            "# knowledge_etl.py\n"
            "pairs = parallel_map(connectors.items(), fetch, max_workers=etl_connector_max_workers)\n"
            "catalog = OntologyBuilder(...).build_catalog_payload(pim, fsm, claims, crm)\n"
            "# write JSON catalogs + lineage\n"
            "if load_neo4j:\n"
            "    populate_graph(driver, catalog)\n"
            "    invalidate_all_named_caches()  # so UI doesn't serve stale subgraphs",
            st,
        )
    )
    story.append(
        Paragraph(
            "<b>What:</b> Parallel extract, serial merge, optional graph load. "
            "<b>Why parallel extract:</b> I/O bound. <b>Why serial transform:</b> deterministic confidence merges.",
            st["body"],
        )
    )

    story.append(Paragraph("10. Redis rate limit (multi-replica)", st["h1"]))
    story.append(
        code_block(
            "# guardrails/rate_limit.py — sliding window via Redis ZSET + Lua\n"
            "# ZREMRANGEBYSCORE old hits; ZCARD; if under max ZADD now; else reject\n"
            "# WHY: in-process counters diverge across API pods; Redis is shared truth",
            st,
        )
    )

    story.append(Paragraph("11. File → responsibility cheat sheet", st["h1"]))
    story.append(
        tbl(
            ["File", "What it does", "Why it exists"],
            [
                ["reliability.py", "FMEA+Bayes pure math", "Deterministic, testable scores"],
                ["graph_rag.py", "End-to-end diagnose", "Central intelligence orchestration"],
                ["symptom_retrieval.py", "Hybrid text match", "Paraphrase without embeddings infra"],
                ["parts_predictor.py", "Rank parts", "Multi-source BOM/claims evidence"],
                ["diagnostic_engine.py", "Tree walk", "Guided troubleshooting"],
                ["populate_graph.py", "MERGE catalog + constraints", "Idempotent knowledge load + indexes"],
                ["ontology_builder.py", "ETL transform", "Canonical catalog from sources"],
                ["diagnosis_service.py", "Business path", "One policy for API/UI"],
                ["diagnosis_graph.py", "LangGraph nodes", "Explicit multi-step agent"],
                ["runtime/cache.py", "TTL cache", "Fast schema/subgraph reads"],
            ],
            st,
            [42 * mm, 55 * mm, 79 * mm],
        )
    )
    story.append(Paragraph("12. Indexes used by this code (WWWH)", st["h1"]))
    story.append(
        wwwh(
            st,
            "Neo4j UNIQUE constraints on every entity *_id (backing unique indexes)",
            "graph/populate_graph.py → create_constraints()",
            "First lines of every populate_graph / promote / ETL load-to-Neo4j",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE · … ×13 labels",
            "MERGE safety + MATCH {id:$x} index seeks for diagnose/parts/viz",
        )
    )
    story.append(
        code_block(
            "def create_constraints(tx):\n"
            "    for query in [\n"
            "        'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE',\n"
            "        'CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE',\n"
            "        # FailureMode, Part, Asset, Claim, SKU, Component, ErrorCode, …\n"
            "    ]: tx.run(query)\n\n"
            "# Called when:\n"
            "session.execute_write(create_constraints)  # then MERGE all nodes",
            st,
        )
    )
    story.append(
        wwwh(
            st,
            "SQLite PRIMARY KEY + status indexes for agent ops tables",
            "utils/persistence.py OperationalStore._init_schema",
            "First open of data/diagnostics.db",
            "PK on case_id/claim_id; idx_escalations_status, idx_claims_status, …",
            "List open claims/escalations without full table scan",
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# VOLUME 04 — RDF OWL Turtle
# ═══════════════════════════════════════════════════════════════════════════


def vol04(story, st):
    cover(
        story,
        st,
        "04",
        "Ontology · RDF · OWL · Turtle",
        "Formal schema, serializations, Neo4j mapping, export tooling",
    )

    story.append(Paragraph("1. Concepts (beginner → precise)", st["h1"]))
    story.append(
        tbl(
            ["Term", "Plain English", "In this project"],
            [
                ["Ontology", "Dictionary of types + allowed links", "Product, Symptom, FM, Part…"],
                ["RDF", "Data as subject–predicate–object triples", "Export format / interchange"],
                ["RDFS", "Classes + domain/range basics", "Used in Turtle headers"],
                ["OWL", "Richer ontology language", "owl:Class, ObjectProperty, Ontology header"],
                ["Turtle (.ttl)", "Readable RDF text syntax", "docs/ontology/*.ttl"],
                ["RDF/XML (.owl)", "XML serialization of RDF/OWL", "warranty-diagnosis.owl"],
                ["TBox", "Schema layer", "Classes & properties"],
                ["ABox", "Instance layer", "wm-001, specific symptoms…"],
                ["Neo4j graph", "Operational store for Cypher", "Runtime truth for diagnosis"],
            ],
            st,
            [28 * mm, 58 * mm, 90 * mm],
        )
    )
    story.append(
        why_box(
            "Why both Neo4j and RDF?",
            "Neo4j is optimized for multi-hop runtime diagnosis. RDF/OWL is the formal interchange / documentation "
            "surface for semantic-web tools and enterprise ontology governance. "
            "Export with: python -m graph.rdf_ontology_export",
            st,
        )
    )

    story.append(Paragraph("2. Class model (OWL TBox)", st["h1"]))
    story.append(
        Paragraph(
            "Classes: Product, Model, SKU, Asset, Symptom, ErrorCode, FailureMode, DiagnosticStep, "
            "Component, Part, Claim, HistoricalResolution, WarrantyPolicy.",
            st["body"],
        )
    )
    story.append(
        code_block(
            "@prefix wd:   <https://example.org/warranty-diagnosis#> .\n"
            "@prefix owl:  <http://www.w3.org/2002/07/owl#> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n"
            "<https://example.org/warranty-diagnosis/ontology> a owl:Ontology ;\n"
            '  rdfs:label "Enterprise Warranty Diagnosis Ontology" ;\n'
            '  owl:versionInfo "1.0.0" .\n\n'
            "wd:Product a owl:Class ;\n"
            '  rdfs:label "Product" ;\n'
            '  rdfs:comment "A manufacturable product family / catalog product." .\n\n'
            "wd:FailureMode a owl:Class ;\n"
            '  rdfs:comment "Diagnosed failure mode (FMEA-aligned)." .\n\n'
            "wd:indicates a owl:ObjectProperty ;\n"
            "  rdfs:domain wd:Symptom ;\n"
            "  rdfs:range wd:FailureMode ;\n"
            '  rdfs:comment "Symptom indicates failure mode. Neo4j: INDICATES." .',
            st,
            40,
        )
    )
    story.append(
        Paragraph(
            "<b>What the code/export does:</b> declares machine-readable types. "
            "<b>Why:</b> tools and humans share one vocabulary; maps 1:1 to Neo4j labels/rel types.",
            st["body"],
        )
    )

    story.append(Paragraph("3. Object properties ↔ Neo4j relationships", st["h1"]))
    story.append(
        tbl(
            ["OWL property", "Neo4j type", "Meaning"],
            [
                ["wd:hasSymptom", "HAS_SYMPTOM", "Product presents symptom"],
                ["wd:indicates", "INDICATES", "Symptom→FM with confidence"],
                ["wd:requiresPart", "REQUIRES_PART", "FM needs part"],
                ["wd:impactsComponent", "IMPACTS_COMPONENT", "FM hits BOM subsystem"],
                ["wd:realizedBy", "REALIZED_BY", "Component→Part"],
                ["wd:nextStep", "NEXT_STEP", "Diagnostic tree branch"],
                ["wd:confirms / rulesOut", "CONFIRMS / RULES_OUT", "Step vs FM"],
                ["wd:instanceOf", "INSTANCE_OF", "Asset→Product"],
                ["wd:compatibleWith", "COMPATIBLE_WITH", "SKU→Part"],
            ],
            st,
            [48 * mm, 42 * mm, 86 * mm],
        )
    )

    story.append(Paragraph("4. Instance (ABox) Turtle example", st["h1"]))
    story.append(
        code_block(
            "wd:product_wm-001 a wd:Product ;\n"
            '  wd:productId "wm-001" ;\n'
            '  wd:name "AquaHome Front Load 8kg" ;\n'
            "  wd:hasSymptom wd:symptom_wm-s03 ;\n"
            "  wd:canHave wd:fm_wm-fm02 .\n\n"
            "wd:symptom_wm-s03 a wd:Symptom ;\n"
            '  wd:description "Will not drain / E21" ;\n'
            '  wd:severity "high" ;\n'
            "  wd:indicates wd:fm_wm-fm02 .\n\n"
            "wd:fm_wm-fm02 a wd:FailureMode ;\n"
            '  rdfs:label "Drain pump failure" ;\n'
            "  wd:impactsComponent wd:component_wm-c02 ;\n"
            "  wd:requiresPart wd:part_wm-p02 .\n\n"
            "wd:component_wm-c02 a wd:Component ;\n"
            '  wd:subsystem "Plumbing" ;\n'
            "  wd:realizedBy wd:part_wm-p02 .",
            st,
            40,
        )
    )
    story.append(
        why_box(
            "Confidence on edges",
            "Neo4j stores confidence on INDICATES relationships. In OWL export we reify with owl:Axiom + wd:confidence "
            "annotation so the triple can carry a literal weight.",
            st,
            BLUE,
        )
    )

    story.append(Paragraph("5. RDF/XML (OWL) fragment", st["h1"]))
    story.append(
        code_block(
            '<?xml version="1.0"?>\n'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n'
            '         xmlns:owl="http://www.w3.org/2002/07/owl#"\n'
            '         xmlns:wd="https://example.org/warranty-diagnosis#">\n'
            '  <owl:Ontology rdf:about="https://example.org/warranty-diagnosis/ontology"/>\n'
            '  <owl:Class rdf:about="https://example.org/warranty-diagnosis#Product"/>\n'
            '  <owl:ObjectProperty rdf:about="https://example.org/warranty-diagnosis#indicates">\n'
            '    <rdfs:domain rdf:resource="...#Symptom"/>\n'
            '    <rdfs:range rdf:resource="...#FailureMode"/>\n'
            "  </owl:ObjectProperty>\n"
            "</rdf:RDF>",
            st,
            25,
        )
    )
    story.append(
        Paragraph(
            "Same triples as Turtle, different syntax. Some enterprise tools prefer RDF/XML (.owl files).",
            st["body"],
        )
    )

    story.append(Paragraph("6. Export tooling (code that writes RDF)", st["h1"]))
    story.append(Paragraph("<b>File:</b> graph/rdf_ontology_export.py", st["small"]))
    story.append(
        code_block(
            "# WHAT: build TBox triples + optional ABox from catalog JSON\n"
            "# WHY: stdlib-only Turtle/RDF-XML without requiring rdflib at runtime\n"
            "python -m graph.rdf_ontology_export --schema-only \\\n"
            "  --out docs/ontology/warranty-diagnosis-schema.ttl\n"
            "python -m graph.rdf_ontology_export --product-id wm-001 \\\n"
            "  --out docs/ontology/wm-001.ttl\n"
            "python -m graph.rdf_ontology_export --format rdfxml \\\n"
            "  --out docs/ontology/warranty-diagnosis.owl",
            st,
        )
    )
    story.append(
        bullets(
            [
                "schema_triples_ttl() — classes + object/datatype properties",
                "instance_ttl_for_product() — one product neighborhood as individuals",
                "catalog_to_turtle() — full/filtered ABox + assets/claims/policies",
                "schema_to_rdfxml() — OWL/XML document",
            ],
            st,
        )
    )

    # embed live schema excerpt if present
    if TTL_SCHEMA.exists():
        story.append(Paragraph("7. Live schema excerpt from repo", st["h1"]))
        excerpt = "\n".join(TTL_SCHEMA.read_text(encoding="utf-8").splitlines()[:55])
        story.append(code_block(excerpt, st, 55))

    story.append(Paragraph("8. Standards alignment", st["h1"]))
    story.append(
        tbl(
            ["Standard", "Relevance"],
            [
                ["W3C RDF 1.1 / RDFS / OWL", "Serialization & ontology language"],
                ["W3C PROV-O", "Provenance fields on entities"],
                ["ISO 14224", "Equipment hierarchy + failure taxonomy inspiration"],
                ["ISO/IEC 81346", "Product-aspect structure ↔ Component/BOM"],
                ["FMEA / AIAG-VDA", "FailureMode scoring semantics"],
            ],
            st,
            [50 * mm, 126 * mm],
        )
    )
    story.extend(img("34-enterprise-blueprint-ERD.png", st, "ERD = property-graph view of the same ontology", 70))

    story.append(Paragraph("9. Topology note (do not confuse)", st["h1"]))
    story.append(
        Paragraph(
            "Industrial <b>product structure</b> (BOM components) is modeled <b>inside</b> this ontology "
            "(Component, IMPACTS_COMPONENT, REALIZED_BY). "
            "We do <b>not</b> maintain a separate Topology subsystem. "
            "W3C BOT (Building Topology Ontology) is for buildings — out of scope.",
            st["body"],
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# VOLUME 05 — Pipelines deploy tests
# ═══════════════════════════════════════════════════════════════════════════


def vol05(story, st):
    cover(
        story,
        st,
        "05",
        "Pipelines · Deploy · Tests · Data",
        "ETL spine, k8s, quality gates, fixtures",
    )
    story.append(Paragraph("1. Batch pipeline stages", st["h1"]))
    story.append(
        code_block(
            "orchestrator.run_all()\n"
            "  1 knowledge_etl      parallel extract → OntologyBuilder → JSON (+ optional Neo4j)\n"
            "  2 smoke_validation   enterprise scenarios must pass\n"
            "  3 staging_promotion  populate_graph MERGE if smoke OK",
            st,
        )
    )
    story.extend(img("41-etl-staging-graph-traversal.png", st, "ETL → graph traversal", 70))
    story.append(Paragraph("2. Data artifacts", st["h1"]))
    story.append(
        tbl(
            ["Path", "Role"],
            [
                ["data/synthetic_diagnosis_data.json", "Runtime catalog"],
                ["data/enterprise_knowledge_catalog.json", "Enterprise catalog"],
                ["data/enterprise_sources/*.json", "PIM/CRM/FSM/claims fixtures"],
                ["data/lineage/etl_batches.jsonl", "Batch audit"],
                ["data/diagnostics.db", "SQLite escalations/claims/cases"],
                ["data/provenance_manifest.json", "Default provenance"],
                ["docs/ontology/*", "Turtle + OWL exports"],
            ],
            st,
            [70 * mm, 106 * mm],
        )
    )
    story.append(Paragraph("3. Deploy topology", st["h1"]))
    story.append(
        bullets(
            [
                "docker/ Dockerfiles for api, etl, frontend, mock, ui",
                "k8s/base: deployments, Neo4j statefulset, ETL cronjob, ingress",
                "overlays staging/prod; deploy/rollouts Argo + Flagger",
                "monitoring/: Prometheus rules, Grafana, OTEL collector",
            ],
            st,
        )
    )
    story.extend(img("30-architecture-LLD-deployment-k8s.png", st, "K8s LLD", 65))
    story.append(Paragraph("4. Tests &amp; evals", st["h1"]))
    story.append(
        bullets(
            [
                "pytest: reliability pure math, API, guardrails, ETL, viz, runtime/redis, RDF, e2e",
                "evals/run_eval.py: golden smoke + safety injection thresholds",
                "pre-commit: ruff; pre-push: full pytest",
                "CI/CD: .github/workflows ci.yml, cd.yml, eval-nightly.yml",
            ],
            st,
        )
    )
    story.append(Paragraph("5. Security controls vs residuals", st["h1"]))
    story.append(
        tbl(
            ["Control", "Status"],
            [
                ["Input/output guardrails", "Yes"],
                ["Rate limit + admission", "Yes (Redis optional)"],
                ["Admin pipeline token", "Optional"],
                ["OIDC end-user auth", "Residual / not productized"],
                ["Live enterprise systems", "Mock by default"],
            ],
            st,
            [55 * mm, 121 * mm],
        )
    )
    story.append(Paragraph("6. Local full spine", st["h1"]))
    story.append(
        code_block(
            "source venv/bin/activate\n"
            "python graph/populate_graph.py\n"
            "uvicorn api.main:app --port 8080\n"
            "cd frontend && npm run dev\n"
            "python -m graph.enterprise_pipeline.orchestrator\n"
            "python -m graph.rdf_ontology_export --schema-only\n"
            "pytest -q",
            st,
        )
    )
    story.append(Paragraph("7. Indexes &amp; constraints (full WWWH)", st["h1"]))
    story.append(
        Paragraph(
            "Deep companion markdown: docs/19-Indexes-Constraints-and-Lookup-Performance.md",
            st["small"],
        )
    )
    story.append(Paragraph("7.1 Neo4j uniqueness constraints", st["h2"]))
    story.append(
        wwwh(
            st,
            "Uniqueness constraint + unique index on each entity natural key",
            "graph/populate_graph.py create_constraints; used by all MERGE/MATCH by id",
            "On every graph load/promote — not on each HTTP diagnose",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (x:Label) REQUIRE x.<id> IS UNIQUE "
            "for Product, Symptom, FailureMode, DiagnosticStep, Part, HistoricalResolution, "
            "Model, SKU, Component, ErrorCode, Asset, WarrantyPolicy, Claim",
            "Integrity (no duplicates) + performance (index seek on product_id etc.)",
        )
    )
    story.append(
        code_block(
            "SHOW CONSTRAINTS;   -- Neo4j Browser: see uniqueness constraints\n"
            "SHOW INDEXES;       -- backing indexes for those constraints\n\n"
            "-- Runtime uses them like:\n"
            "MATCH (p:Product {product_id: $pid})-[:HAS_SYMPTOM]->(s)\n"
            "-- ↑ index seek on product_id, then relationship expand",
            st,
        )
    )
    story.append(Paragraph("7.2 SQLite ops indexes", st["h2"]))
    story.append(
        wwwh(
            st,
            "PRIMARY KEY + secondary status indexes",
            "utils/persistence.py → data/diagnostics.db",
            "First OperationalStore init",
            "PK case_id/claim_id; CREATE INDEX idx_escalations_status ON escalations(status); "
            "same for ccaas_cases and claim_submissions",
            "Agent dashboards filter by status quickly",
        )
    )
    story.append(Paragraph("7.3 Not database indexes (but look-ups)", st["h2"]))
    story.append(
        bullets(
            [
                "<b>TTL cache</b> (runtime/cache): ontology + product subgraphs — when: graph GETs; invalidate after load",
                "<b>Redis keys</b>: multi-pod rate limit ZSETs / cache keys — when REDIS_URL set",
                "<b>No full-text / vector index</b> on symptoms — hybrid TF-IDF after product known",
            ],
            st,
        )
    )
    story.append(Paragraph("7.4 Timeline", st["h2"]))
    story.append(
        code_block(
            "T0 populate_graph  → create_constraints + MERGE entities\n"
            "T1 first claim/escalation → SQLite schema + status indexes\n"
            "T2 diagnose / graph GET → Cypher uses unique indexes; optional cache\n"
            "T3 next ETL load → constraints IF NOT EXISTS; MERGE; invalidate caches",
            st,
        )
    )
    story.append(Paragraph("8. Pipeline WWWH cards", st["h1"]))
    story.append(
        wwwh(
            st,
            "Knowledge ETL",
            "pipelines/knowledge_etl.py + connectors + OntologyBuilder",
            "Batch job / admin dry-run or load",
            "parallel_map fetch → build_catalog_payload → write JSON → optional populate_graph",
            "Keep Neo4j aligned with enterprise-ish sources",
        )
    )
    story.append(
        wwwh(
            st,
            "Smoke + promote gate",
            "smoke_validation.py · staging_promotion.py",
            "After ETL, before treating graph as promoted",
            "Run scenarios; only MERGE if smoke OK",
            "Bad catalog must not overwrite production graph blindly",
        )
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    volumes = [
        ("00-Master-Index.pdf", "Vol 00 Master Index", vol00),
        ("01-Architecture-and-System-Map.pdf", "Vol 01 Architecture", vol01),
        ("02-Algorithms-and-Theory.pdf", "Vol 02 Algorithms & Theory", vol02),
        ("03-Code-Deep-Dive-Annotated.pdf", "Vol 03 Code Deep-Dive", vol03),
        ("04-Ontology-RDF-OWL-Turtle.pdf", "Vol 04 Ontology RDF OWL", vol04),
        ("05-Pipelines-Deploy-Tests-Data.pdf", "Vol 05 Pipelines Deploy Tests", vol05),
    ]
    for name, title, fn in volumes:
        build_pdf(OUT_DIR / name, title, fn)
    print("Done. PDFs in", OUT_DIR)


if __name__ == "__main__":
    main()
