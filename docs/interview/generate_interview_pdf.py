#!/usr/bin/env python3
"""Generate a polished Interview Mastery Guide PDF (ReportLab)."""

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
OUT = Path(__file__).resolve().parent / "Remote-Diagnostics-Interview-Mastery-Guide.pdf"
PNG = ROOT / "docs" / "graphviz" / "rendered" / "png"

TEAL = colors.HexColor("#0f766e")
TEAL_DARK = colors.HexColor("#134e4a")
NAVY = colors.HexColor("#1e3a5f")
SLATE = colors.HexColor("#334155")
LIGHT = colors.HexColor("#f8fafc")
ORANGE_BG = colors.HexColor("#fff7ed")
ORANGE = colors.HexColor("#9a3412")
BLUE_BG = colors.HexColor("#dbeafe")
GREEN_BG = colors.HexColor("#dcfce7")
PURPLE_BG = colors.HexColor("#f3e8ff")
AMBER_BG = colors.HexColor("#ffedd5")
CODE_BG = colors.HexColor("#0f172a")


def styles():
    base = getSampleStyleSheet()
    s = {
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontSize=24,
            textColor=TEAL_DARK,
            alignment=TA_CENTER,
            spaceAfter=8,
            leading=28,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontSize=12,
            textColor=SLATE,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=16,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=TEAL_DARK,
            spaceBefore=14,
            spaceAfter=8,
            borderPadding=3,
            leading=20,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=12.5,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=6,
            leading=16,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontSize=11,
            textColor=SLATE,
            spaceBefore=8,
            spaceAfter=4,
            leading=14,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_JUSTIFY,
            leading=13,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontSize=9.5,
            leading=12.5,
            leftIndent=4,
            textColor=colors.HexColor("#0f172a"),
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontSize=8.5,
            textColor=SLATE,
            leading=11,
            spaceAfter=3,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=TEAL_DARK,
            leading=13,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "q": ParagraphStyle(
            "q",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=NAVY,
            leading=12.5,
            fontName="Helvetica-Bold",
            spaceAfter=2,
        ),
        "a": ParagraphStyle(
            "a",
            parent=base["Normal"],
            fontSize=9,
            textColor=SLATE,
            leading=12,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontSize=7.5,
            textColor=colors.HexColor("#e2e8f0"),
            leading=10,
            fontName="Courier",
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_CENTER,
        ),
        "center": ParagraphStyle(
            "center",
            parent=base["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=SLATE,
        ),
        "badge": ParagraphStyle(
            "badge",
            parent=base["Normal"],
            fontSize=8,
            textColor=TEAL_DARK,
            alignment=TA_CENTER,
        ),
    }
    return s


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.setLineWidth(0.5)
    canvas.line(16 * mm, 12 * mm, A4[0] - 16 * mm, 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawCentredString(
        A4[0] / 2,
        7 * mm,
        f"Remote Diagnostics Graph · Interview Mastery Guide  ·  {doc.page}",
    )
    canvas.restoreState()


def hrule():
    t = Table([[""]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, TEAL)]))
    return t


def pointer(text: str, S) -> KeepTogether:
    p = Paragraph(f"<b>Remember:</b> {text}", S["body"])
    box = Table([[p]], colWidths=[170 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ORANGE_BG),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fdba74")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 4)])


def persona_qa(persona: str, question: str, answer: str, S, bg) -> KeepTogether:
    header = Paragraph(f"<font color='#1e3a5f'><b>[{persona}] Q:</b> {question}</font>", S["q"])
    body = Paragraph(f"<b>A:</b> {answer}", S["a"])
    box = Table([[header], [body]], colWidths=[170 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 5)])


def simple_table(headers, rows, S, col_widths=None):
    data = [[Paragraph(f"<b>{h}</b>", S["small"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), S["small"]) for c in row])
    t = Table(data, colWidths=col_widths or [170 * mm / len(headers)] * len(headers), repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    # fix header text color via paragraph is already white parent? use white in header
    data[0] = [Paragraph(f"<font color='white'><b>{h}</b></font>", S["small"]) for h in headers]
    t = Table(data, colWidths=col_widths or [170 * mm / len(headers)] * len(headers), repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_DARK),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    return t


def code_block(text: str, S):
    lines = [Paragraph(line.replace(" ", "&nbsp;") or "&nbsp;", S["code"]) for line in text.splitlines()]
    box = Table([[l] for l in lines], colWidths=[170 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (0, 0), 6),
                ("BOTTOMPADDING", (0, -1), (0, -1), 6),
                ("TOPPADDING", (0, 1), (-1, -2), 1),
                ("BOTTOMPADDING", (0, 1), (-1, -2), 1),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 6)])


def maybe_image(name: str, width_mm: float = 170, caption: str | None = None, S=None):
    path = PNG / name
    flow = []
    if path.exists():
        # scale to width, preserve aspect, cap height
        img = Image(str(path))
        max_w = width_mm * mm
        max_h = 95 * mm
        aspect = img.imageHeight / float(img.imageWidth)
        w = max_w
        h = w * aspect
        if h > max_h:
            h = max_h
            w = h / aspect
        img.drawWidth = w
        img.drawHeight = h
        flow.append(img)
        if caption and S:
            flow.append(Paragraph(f"<i>{caption}</i>", S["center"]))
        flow.append(Spacer(1, 6))
    elif S:
        flow.append(Paragraph(f"<i>[Diagram missing: {name} — run docs/graphviz/render_all.sh]</i>", S["small"]))
    return flow


def bullets(items, S):
    return ListFlowable(
        [ListItem(Paragraph(i, S["bullet"]), leftIndent=8, value="•") for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=12,
        spaceBefore=2,
        spaceAfter=6,
    )


def build():
    S = styles()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="Remote Diagnostics Graph — Interview Mastery Guide",
        author="Diagnostic Chatbot Team",
    )
    story = []

    # ── COVER ──
    story.append(Spacer(1, 28 * mm))
    story.append(Paragraph("Remote Diagnostics Graph", S["cover_title"]))
    story.append(hrule())
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Interview Mastery Guide", S["cover_title"]))
    story.append(
        Paragraph(
            "Explain everything end-to-end — product, theory, code, architecture, tools",
            S["cover_sub"],
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            "Beginner-friendly language  ·  Senior depth  ·  Academic theory  ·  Dev & Architect Q&amp;A",
            S["badge"],
        )
    )
    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            "Enterprise warranty diagnosis · Knowledge graph · GraphRAG · FMEA · Bayesian ranking<br/>"
            "ETL · Neo4j · LangGraph · LLMOps · Redis · Runtime scale",
            S["center"],
        )
    )
    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "<b>How to use:</b> Memorize §1 pitch → draw §3 diagrams → drill persona Q&amp;A → practice scenarios.",
            S["center"],
        )
    )
    story.append(Spacer(1, 12 * mm))
    story.append(
        Paragraph(
            "Golden rule for every answer:<br/>"
            "<b>(1) plain English</b> → <b>(2) why it matters</b> → <b>(3) how our app does it</b> → <b>(4) file/tool</b><br/>"
            "Plus WWWH: <b>What · Where · When · How · Why</b> (indexes worked example in §13 / docs/19).",
            S["quote"],
        )
    )
    story.append(PageBreak())

    # ── TOC ──
    story.append(Paragraph("1. Contents & interview map", S["h1"]))
    story.append(
        simple_table(
            ["Interviewer", "Read first", "Practice"],
            [
                ["Anyone (opening)", "§2 Elevator pitch + §3 What we built", "90-second story out loud"],
                ["Academic / research", "§6 Theory + Academic Q&A", "Derive Bayes & RPN on whiteboard"],
                ["Senior developer", "§5 Tools + §7 Code spine + Dev Q&A", "Trace POST /diagnose in IDE"],
                ["Senior architect", "§4 Architecture + Arch Q&A", "Draw ETL → Neo4j → API → UI"],
                ["Industry / domain", "§3 Domain chain + Industry Q&A", "Asset → FM → part → claim"],
            ],
            S,
            [42 * mm, 70 * mm, 58 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "Sections: 2 Pitch · 3 Product domain · 4 Architecture · 5 Tools · 6 Theory · 7 Code · "
            "8 Ontology/topology · 9 Persona Q&A · 10 Scenarios · 11 Memory cards · 12 Glossary",
            S["small"],
        )
    )

    # ── PITCH ──
    story.append(Paragraph("2. The 90-second elevator pitch (memorize)", S["h1"]))
    story.append(
        Paragraph(
            "We built an <b>enterprise remote-diagnostics system</b> for warranty support. "
            "A customer or agent describes a problem (“washer won’t drain, E21”). "
            "We resolve the <b>product/asset</b>, walk a <b>Neo4j knowledge graph</b> of "
            "symptoms → failure modes → parts, score candidates with <b>FMEA + Bayes</b>, "
            "return ranked diagnosis, troubleshooting steps, and predicted parts, then optionally "
            "open a <b>claim</b> or <b>escalate</b>.",
            S["body"],
        )
    )
    story.append(
        Paragraph(
            "Knowledge is <b>not invented by an LLM at runtime</b> — it is <b>authored as blueprints</b>, "
            "<b>ETL’d</b> from PIM/FSM/Claims, <b>validated</b>, and <b>MERGEd into Neo4j</b>. "
            "LLM (if enabled) only helps wording; <b>evidence is graph-native and deterministic</b>.",
            S["body"],
        )
    )
    story.append(Paragraph("<b>Non-technical one-liner</b>", S["h3"]))
    story.append(
        Paragraph(
            "“We help warranty agents find the right fix and part by searching a product knowledge graph "
            "instead of guessing from a chatbot.”",
            S["quote"],
        )
    )
    story.append(Paragraph("<b>Technical one-liner</b>", S["h3"]))
    story.append(
        Paragraph(
            "“Deterministic GraphRAG over a warranty ontology in Neo4j, with FMEA/Bayesian ranking, "
            "enterprise ETL, and LLMOps-ready API.”",
            S["quote"],
        )
    )

    # ── DOMAIN ──
    story.append(Paragraph("3. What the application does (domain)", S["h1"]))
    story.append(Paragraph("3.1 The problem", S["h2"]))
    story.append(
        Paragraph(
            "When a product fails, support must answer: what unit is this, what is wrong, how do we confirm, "
            "which part, is it under warranty? Without a graph, people dig PDFs and tribal knowledge. "
            "We encode knowledge as a <b>graph</b> so answers are consistent, explainable, and fast.",
            S["body"],
        )
    )
    story.append(Paragraph("3.2 Operational chain (whiteboard this)", S["h2"]))
    story.append(
        code_block(
            "Asset/Serial → Product/Model/SKU → Symptom + ErrorCode\n"
            "  → FailureMode (diagnosis) → DiagnosticStep\n"
            "  → Component (BOM) → Part → Claim / HistoricalResolution",
            S,
        )
    )
    story.append(
        simple_table(
            ["Business question", "Graph answer"],
            [
                ["What unit?", "Asset → Product / BOUND_TO_SKU"],
                ["What could be wrong?", "Symptom -INDICATES→ FailureMode"],
                ["How sure?", "Edge confidence + FMEA + Bayes posterior"],
                ["Which part?", "REQUIRES_PART + BOM + claims precedent"],
                ["Covered?", "Warranty policy + asset status"],
            ],
            S,
            [55 * mm, 115 * mm],
        )
    )
    story.append(pointer("Always narrate the chain Asset → Symptom → FailureMode → Part → Claim.", S))

    # ── ARCH ──
    story.append(Paragraph("4. End-to-end architecture (as built)", S["h1"]))
    story.append(Paragraph("4.1 Six layers", S["h2"]))
    story.append(
        simple_table(
            ["Layer", "Responsibility", "Key modules"],
            [
                ["L6 Experience", "UI", "Next.js frontend"],
                ["L5 Orchestration", "Agent, claims, warranty", "diagnosis_service, LangGraph"],
                ["L4 Intelligence", "GraphRAG, FMEA/Bayes, trees, parts", "graph_rag, reliability, …"],
                ["L3 Integration", "Enterprise systems", "connectors, CRM, mock :8090"],
                ["L2 Knowledge store", "Neo4j", "populate_graph, neo4j_client"],
                ["L1 Data platform", "Blueprints, ETL", "oem catalog, orchestrator"],
            ],
            S,
            [38 * mm, 55 * mm, 77 * mm],
        )
    )
    story.append(Paragraph("4.2 Complete system pipeline (diagram 39)", S["h2"]))
    story.extend(
        maybe_image(
            "39-complete-enterprise-system-pipeline.png",
            caption="Fig. 1 — Sources → ETL → gates → Neo4j → API/UI → claims (+ Redis optional)",
            S=S,
        )
    )
    story.append(
        bullets(
            [
                "<b>Author</b> OEM blueprints + warranty extensions (Model/SKU/Component)",
                "<b>Extract</b> PIM/FSM/Claims/CRM in parallel (<font face='Courier'>parallel_map</font>)",
                "<b>Transform</b> OntologyBuilder → catalog JSON + provenance",
                "<b>Gate</b> smoke validation → <b>Promote</b> MERGE into Neo4j",
                "<b>Serve</b> UI → API → LangGraph → GraphRAG Cypher multi-hop",
            ],
            S,
        )
    )
    story.append(Paragraph("4.3 Network topology (diagram 40)", S["h2"]))
    story.extend(
        maybe_image(
            "40-enterprise-network-topology.png",
            caption="Fig. 2 — Enterprise network: clients, ingress, app, data, integration zone, ops",
            S=S,
        )
    )
    story.append(
        simple_table(
            ["Component", "Port", "Role"],
            [
                ["Next.js UI", "3000", "Agent experience"],
                ["FastAPI", "8080", "Diagnose, graph, claims, admin"],
                ["Mock enterprise", "8090", "Simulated PIM/CRM/FSM/Claims"],
                ["Neo4j", "7687", "Knowledge graph (Bolt)"],
                ["Redis (optional)", "6379", "Shared cache / rate / budget"],
            ],
            S,
            [50 * mm, 30 * mm, 90 * mm],
        )
    )
    story.append(Paragraph("4.4 ETL → staging → fast traversal (diagram 41)", S["h2"]))
    story.extend(
        maybe_image(
            "41-etl-staging-graph-traversal.png",
            caption="Fig. 3 — Why multi-hop diagnosis is fast: pre-built edges + unique keys + short paths",
            S=S,
        )
    )
    story.append(
        pointer(
            "We don’t scan the whole graph each request. We land on a product node, then walk short pre-built paths.",
            S,
        )
    )
    story.append(Paragraph("4.5 Ontology schema (ERD)", S["h2"]))
    story.extend(
        maybe_image(
            "34-enterprise-blueprint-ERD.png",
            caption="Fig. 4 — Entity-relationship contract of the warranty ontology",
            S=S,
        )
    )
    story.append(Paragraph("4.6 GraphRAG diagnosis flow", S["h2"]))
    story.extend(
        maybe_image(
            "04-graphrag-diagnosis.png",
            caption="Fig. 5 — Runtime GraphRAG diagnosis path",
            S=S,
        )
    )

    # ── TOOLS ──
    story.append(Paragraph("5. Tools & technologies (plain English)", S["h1"]))
    story.append(
        simple_table(
            ["Tool", "Plain English", "Our role"],
            [
                ["Neo4j", "Database for relationships", "Stores nodes + edges for diagnosis"],
                ["Cypher", "SQL-for-graphs", "Multi-hop evidence queries"],
                ["FastAPI", "Python web API", "POST /diagnose, graph GETs"],
                ["LangGraph", "Workflow as steps", "detect → diagnose → format → escalate"],
                ["GraphRAG", "Retrieve graph, ground answer", "Cypher evidence + format"],
                ["Redis", "Shared fast memory (optional)", "Multi-pod cache/rate/budget"],
                ["FMEA", "Reliability worksheet", "S/O/D style signals"],
                ["Bayes", "Update beliefs with evidence", "Rank failure modes"],
                ["OWL/RDF", "Formal ontology languages", "Optional export, not runtime store"],
                ["OTEL / Prom", "Observability", "Traces & metrics"],
            ],
            S,
            [32 * mm, 58 * mm, 80 * mm],
        )
    )
    story.append(Paragraph("Neo4j vs relational", S["h3"]))
    story.append(
        Paragraph(
            "Relational DBs excel at transactions and fixed joins. Multi-hop diagnostic paths "
            "(symptom→FM→component→part→claim) are natural in a property graph with typed edges and "
            "edge properties (confidence, probability). We still use SQLite for simple ops tables "
            "(claims/escalations); Neo4j is the diagnostic brain.",
            S["body"],
        )
    )
    story.append(
        pointer("Is this an LLM chatbot? Core diagnosis is graph + math. LLM is optional and off by default.", S)
    )

    # ── THEORY ──
    story.append(Paragraph("6. Theory (academic + industry)", S["h1"]))
    story.append(Paragraph("6.1 Ontology vs knowledge graph vs topology", S["h2"]))
    story.append(
        simple_table(
            ["Term", "Meaning", "Our app"],
            [
                ["Taxonomy", "Category hierarchy", "Product categories"],
                ["Ontology", "Types + allowed relations", "Product, Symptom, FM, Part…"],
                ["Knowledge graph", "Ontology + instances", "wm-001 + real edges in Neo4j"],
                ["Topology (domain)", "Structure/composition", "BOM Component + diagnostic tree"],
                ["Topology (infra)", "Network of systems", "Diagram 40 — not domain model"],
            ],
            S,
            [40 * mm, 60 * mm, 70 * mm],
        )
    )
    story.append(Paragraph("6.2 FMEA / FMECA", S["h2"]))
    story.append(
        Paragraph(
            "<b>FMEA</b> = Failure Mode and Effects Analysis. For each failure mode estimate "
            "<b>S</b>everity, <b>O</b>ccurrence, <b>D</b>etection. Classic <b>RPN = S×O×D</b>. "
            "AIAG-VDA also uses Action Priority because raw RPN can rank-reverse. "
            "Our <font face='Courier'>graph/reliability.py</font> derives signals from graph data "
            "(symptom severity, claim counts, diagnostic coverage).",
            S["body"],
        )
    )
    story.append(Paragraph("6.3 Bayesian diagnostic inference", S["h2"]))
    story.append(
        Paragraph(
            "P(failure mode | symptoms) ∝ P(fm) × ∏ P(sᵢ | fm). "
            "Prior from history; likelihood from INDICATES.confidence; normalize across candidates. "
            "This is Pearl / AIMA-style belief update with evidence.",
            S["body"],
        )
    )
    story.append(
        pointer(
            "Whiteboard: two FMs, two symptoms, assign confidences, multiply × prior, normalize to 1.",
            S,
        )
    )
    story.append(Paragraph("6.4 ETL & systems concepts", S["h2"]))
    story.append(
        bullets(
            [
                "<b>ETL:</b> Extract (parallel I/O) → Transform (serial deterministic) → Load (MERGE)",
                "<b>Cache:</b> remember expensive stable reads (schema/subgraphs), not free-text diagnosis by default",
                "<b>Concurrency:</b> parallel independent fetches; keep one diagnosis ranking serial",
                "<b>Partition keys:</b> tenant|product for rate limits/caches; physical sharding later",
                "<b>Admission control:</b> cap concurrent diagnoses so Neo4j isn’t overwhelmed",
            ],
            S,
        )
    )
    story.append(Paragraph("6.5 LLMOps snapshot", S["h2"]))
    story.append(
        Paragraph(
            "PromptOps (versioned prompts) · EvalOps (golden tests) · Guardrails (input/output) · "
            "FinOps (daily budget circuit breaker) · Gateway (model routing) · Observability (OTEL/metrics).",
            S["body"],
        )
    )

    # ── CODE ──
    story.append(Paragraph("7. Code spine — how pieces connect", S["h1"]))
    story.append(Paragraph("7.1 Batch path", S["h2"]))
    story.append(
        code_block(
            "orchestrator.run_all()\n"
            "  knowledge_etl  → parallel_map(fetch) → OntologyBuilder → catalog JSON\n"
            "  smoke_validation  (block promote if fail)\n"
            "  staging_promotion → populate_graph() MERGE + constraints → Neo4j\n"
            "  invalidate_all_named_caches()",
            S,
        )
    )
    story.append(
        Paragraph(
            "Files: <font face='Courier'>orchestrator.py</font>, "
            "<font face='Courier'>knowledge_etl.py</font>, "
            "<font face='Courier'>ontology_builder.py</font>, "
            "<font face='Courier'>populate_graph.py</font>, "
            "<font face='Courier'>oem_product_catalog.py</font>",
            S["small"],
        )
    )
    story.append(Paragraph("7.2 Online path (POST /diagnose)", S["h2"]))
    story.append(
        code_block(
            "api/main.diagnose\n"
            "  → rate limit + concurrency slot + guard_request\n"
            "  → CRM enrich + warranty gate\n"
            "  → diagnosis_service.run_full_diagnosis\n"
            "       → LangGraph: detect → tool_diagnose → format → escalate\n"
            "            → graph_rag.diagnose (Cypher + reliability + tree + parts)\n"
            "  → validate_output → DiagnoseResponse JSON",
            S,
        )
    )
    story.append(Paragraph("7.3 Mini Cypher", S["h2"]))
    story.append(
        code_block(
            "MATCH (p:Product {product_id:$pid})-[:HAS_SYMPTOM]->(s:Symptom)\n"
            "MATCH (s)-[r:INDICATES]->(fm:FailureMode)\n"
            "RETURN fm, r.confidence ORDER BY r.confidence DESC",
            S,
        )
    )

    # ── ONTOLOGY ──
    story.append(Paragraph("8. Ontology, topology, RDF", S["h1"]))
    story.append(
        simple_table(
            ["Question", "Short answer"],
            [
                ["Separate topology system?", "No — BOM/Component is inside the ontology"],
                ["W3C BOT?", "Building spatial topology — not our domain"],
                ["ISO 14224?", "Equipment hierarchy + failure taxonomy — maps to us"],
                ["OWL/RDF export?", "Interchange/docs via rdf_ontology_export; runtime is Neo4j"],
            ],
            S,
            [50 * mm, 120 * mm],
        )
    )

    # ── Q&A ──
    story.append(PageBreak())
    story.append(Paragraph("9. Question bank by interviewer persona", S["h1"]))
    story.append(Paragraph("9.1 Academic / theory", S["h2"]))
    story.append(
        persona_qa(
            "ACADEMIC",
            "Formalize diagnosis as probabilistic inference.",
            "Failure modes = hypotheses; symptoms = evidence. Naive Bayes: posterior ∝ prior × ∏ P(sᵢ|fm). "
            "Likelihoods from INDICATES.confidence; priors from claim/history frequency; normalize. "
            "Code: reliability.py + GraphRAG ranking.",
            S,
            BLUE_BG,
        )
    )
    story.append(
        persona_qa(
            "ACADEMIC",
            "Why is RPN criticized? What do you do?",
            "Ordinal multiplication can rank-reverse. AIAG-VDA favors Action Priority. "
            "We expose RPN-like scores but rank diagnosis primarily by Bayesian posterior grounded in graph counts.",
            S,
            BLUE_BG,
        )
    )
    story.append(
        persona_qa(
            "ACADEMIC",
            "Ontology vs knowledge graph?",
            "Ontology = TBox (schema of classes/properties). KG = TBox + ABox (instances). "
            "OWL export ≈ TBox; Neo4j holds operational ABox for all products.",
            S,
            BLUE_BG,
        )
    )
    story.append(
        persona_qa(
            "ACADEMIC",
            "Why multi-hop graph over pure vector RAG?",
            "Typed edges encode expert causal/diagnostic constraints. Vectors help language match; "
            "final ranking stays on symbolic paths for explainability and audit.",
            S,
            BLUE_BG,
        )
    )
    story.append(
        persona_qa(
            "ACADEMIC",
            "How do you avoid LLM hallucination?",
            "Facts from Neo4j only; LLM optional for phrasing; provenance trail; evals/guardrails; LLM off by default.",
            S,
            BLUE_BG,
        )
    )

    story.append(Paragraph("9.2 Senior developer", S["h2"]))
    story.append(
        persona_qa(
            "SENIOR DEV",
            "Walk the code path of POST /diagnose.",
            "api/main.diagnose → admission + guardrails → CRM/warranty → run_full_diagnosis → "
            "LangGraph → graph_rag.diagnose Cypher+rank → format → JSON. Name the files in order.",
            S,
            GREEN_BG,
        )
    )
    story.append(
        persona_qa(
            "SENIOR DEV",
            "How is ETL idempotent?",
            "Neo4j MERGE on natural keys + uniqueness constraints. Re-promote updates properties, doesn’t duplicate.",
            S,
            GREEN_BG,
        )
    )
    story.append(
        persona_qa(
            "SENIOR DEV",
            "Why parallel extract, serial transform?",
            "Extract is I/O-bound and independent. Transform merges confidences and must stay deterministic.",
            S,
            GREEN_BG,
        )
    )
    story.append(
        persona_qa(
            "SENIOR DEV",
            "Redis without hard dependency?",
            "Empty REDIS_URL uses in-process memory. Same interfaces for cache, rate limit, budget, concurrency. "
            "Fall back to memory if Redis errors.",
            S,
            GREEN_BG,
        )
    )
    story.append(
        persona_qa(
            "SENIOR DEV",
            "Breakpoint for wrong part prediction?",
            "parts_predictor scoring; REQUIRES_PART/BOM edges; claim precedent; then check if wrong FM ranked upstream.",
            S,
            GREEN_BG,
        )
    )

    story.append(Paragraph("9.3 Senior architect", S["h2"]))
    story.append(
        persona_qa(
            "ARCHITECT",
            "Trust boundaries?",
            "Agents → Ingress → UI/API; Bolt private to Neo4j; outbound connectors; admin token for pipelines; "
            "Redis for multi-replica shared state. No public Bolt.",
            S,
            PURPLE_BG,
        )
    )
    story.append(
        persona_qa(
            "ARCHITECT",
            "Why Neo4j over Postgres recursive CTEs?",
            "Variable-length diagnostic/BOM paths, edge properties first-class, clearer domain model for multi-hop evidence. "
            "Postgres still fine for claim ledgers.",
            S,
            PURPLE_BG,
        )
    )
    story.append(
        persona_qa(
            "ARCHITECT",
            "Safe knowledge promotion?",
            "ETL → smoke scenarios → promote only if pass → MERGE with lineage batch id → invalidate caches.",
            S,
            PURPLE_BG,
        )
    )
    story.append(
        persona_qa(
            "ARCHITECT",
            "Where does LLM fit?",
            "Language edge tasks behind gateway with budget/evals — never sole source of failure-mode truth.",
            S,
            PURPLE_BG,
        )
    )
    story.append(
        persona_qa(
            "ARCHITECT",
            "Multi-tenant evolution?",
            "Logical partition keys now; next OIDC tenant claims + scoped queries; later Neo4j multi-DB if needed.",
            S,
            PURPLE_BG,
        )
    )

    story.append(Paragraph("9.4 Industry / domain senior", S["h2"]))
    story.append(
        persona_qa(
            "INDUSTRY",
            "How do you reduce wrong parts / MTTR?",
            "Ranked failure modes + linked parts from graph and claim precedent; BOM path shows subsystem impact.",
            S,
            AMBER_BG,
        )
    )
    story.append(
        persona_qa(
            "INDUSTRY",
            "Alignment to FMEA / ISO 14224?",
            "Failure modes + S/O/D-style signals; equipment hierarchy as Component/BOM; claims feedback as continuous improvement.",
            S,
            AMBER_BG,
        )
    )
    story.append(
        persona_qa(
            "INDUSTRY",
            "10,000 SKUs — scale?",
            "ETL by product line; cache hot subgraphs; index product_id; avoid global scans; async ETL workers when batch grows.",
            S,
            AMBER_BG,
        )
    )
    story.append(
        persona_qa(
            "INDUSTRY",
            "Salesforce / SAP integration?",
            "Connector abstraction already exists. Swap mock HTTP for real APIs; OntologyBuilder is the anti-corruption layer.",
            S,
            AMBER_BG,
        )
    )

    # ── SCENARIOS ──
    story.append(Paragraph("10. Practice scenarios", S["h1"]))
    story.append(Paragraph("A — CTO in 3 minutes", S["h3"]))
    story.append(
        bullets(
            [
                "Problem: inconsistent warranty diagnosis",
                "Approach: product knowledge graph + deterministic ranking",
                "Pipeline: enterprise systems → ETL → Neo4j → API",
                "Trust: provenance, gates, human escalation",
                "AI: LLM optional; evidence graph-first",
                "Scale: pools, caches, Redis, K8s shapes",
            ],
            S,
        )
    )
    story.append(Paragraph("B — Wrong diagnosis postmortem", S["h3"]))
    story.append(
        bullets(
            [
                "Wrong product resolution?",
                "Symptom match quality?",
                "INDICATES confidences / sparse priors?",
                "Part wrong but FM right? → parts_predictor",
                "Fix data quality vs algorithm",
            ],
            S,
        )
    )
    story.append(Paragraph("Closing master answer (if time is almost up)", S["h3"]))
    story.append(
        Paragraph(
            "“End-to-end: we author product diagnostic knowledge, ETL it through quality gates into Neo4j as a typed "
            "ontology of symptoms, failure modes, steps, and parts. At runtime, FastAPI and LangGraph call GraphRAG, "
            "which walks short Cypher paths and ranks failure modes with FMEA-style signals and Bayesian posteriors, "
            "then predicts parts and can open claims. Determinism, provenance, and optional LLM phrasing keep it "
            "enterprise-safe. Scale-out uses connection pools, caches, and Redis-backed limits for multi-replica APIs.”",
            S["quote"],
        )
    )

    # ── MEMORY ──
    story.append(Paragraph("11. Memory cards", S["h1"]))
    story.append(
        simple_table(
            ["Card", "Memorize"],
            [
                [
                    "Pipeline",
                    "Blueprints → Connectors → OntologyBuilder → Catalog → Smoke → Promote → Neo4j → GraphRAG",
                ],
                ["Ranking", "Posterior ∝ Prior × ∏ P(symptom|FM)"],
                ["FMEA", "S × O × D → RPN (+ Action Priority)"],
                ["Topology", "BOM Component structure lives inside ontology — not a separate system"],
                ["Ports", "3000 UI · 8080 API · 8090 mock · 7687 Neo4j · 6379 Redis"],
                ["Honesty", "Demo fixtures may be simulated — labeled in provenance"],
            ],
            S,
            [32 * mm, 138 * mm],
        )
    )
    story.append(Paragraph("Key files", S["h3"]))
    story.append(
        simple_table(
            ["Need", "File"],
            [
                ["HTTP entry", "api/main.py"],
                ["Business rules", "services/diagnosis_service.py"],
                ["Agent flow", "agents/diagnosis_graph.py"],
                ["Brain", "graph/graph_rag.py"],
                ["Math", "graph/reliability.py"],
                ["Load graph", "graph/populate_graph.py"],
                ["ETL", "enterprise_pipeline/.../knowledge_etl.py + orchestrator.py"],
                ["Runtime scale", "runtime/*"],
            ],
            S,
            [40 * mm, 130 * mm],
        )
    )

    # ── GLOSSARY ──
    story.append(Paragraph("12. Glossary", S["h1"]))
    story.append(
        simple_table(
            ["Term", "Meaning"],
            [
                ["Asset", "Installed unit with serial number"],
                ["SKU", "Sellable revision of a model"],
                ["Symptom", "Observed problem"],
                ["Error code", "Device-reported code (e.g. E21)"],
                ["Failure mode", "Diagnosed fault type"],
                ["Component", "BOM subsystem"],
                ["Part", "Replaceable spare"],
                ["Provenance", "Where a fact came from"],
                ["MERGE", "Neo4j upsert by key"],
                ["GraphRAG", "Retrieve graph evidence to ground answers"],
                ["LangGraph", "Stateful multi-step agent workflow"],
                ["RPN", "Risk Priority Number S×O×D"],
                ["Admission control", "Limit concurrent heavy requests"],
            ],
            S,
            [40 * mm, 130 * mm],
        )
    )

    story.append(Paragraph("13. Indexes &amp; constraints (WWWH — interview ready)", S["h1"]))
    story.append(
        Paragraph(
            "Use five questions for any subsystem: What · Where · When · How · Why. "
            "Full write-up: docs/19-Indexes-Constraints-and-Lookup-Performance.md",
            S["body"],
        )
    )
    story.append(
        simple_table(
            ["", "Neo4j uniqueness", "SQLite ops"],
            [
                ["What", "UNIQUE constraint on each *_id (backing unique index)", "PK + status indexes"],
                ["Where", "populate_graph.create_constraints", "utils/persistence.py"],
                ["When", "Every graph load/promote (not each diagnose)", "First DB open"],
                ["How", "CREATE CONSTRAINT IF NOT EXISTS ... IS UNIQUE", "CREATE INDEX idx_*_status"],
                ["Why", "Fast MATCH by id + no duplicates", "Filter agent queues by status"],
            ],
            S,
            [22 * mm, 80 * mm, 68 * mm],
        )
    )
    story.append(
        Paragraph(
            "<b>Say in interview:</b> We resolve product by unique product_id (constraint-backed index), "
            "expand HAS_SYMPTOM, then hybrid TF-IDF in Python. No full-text index today.",
            S["body"],
        )
    )
    story.append(Paragraph("14. Red flags to avoid", S["h1"]))
    story.append(
        simple_table(
            ["Don’t say", "Say instead"],
            [
                ["“The LLM figures out the failure mode”", "“Graph ranks FMs; LLM may phrase the answer”"],
                ["“We built a separate topology product”", "“Product structure is Component/BOM in the ontology”"],
                ["“Redis is required”", "“Redis is optional for multi-replica; memory works for demo”"],
                ["“It’s just RAG on PDFs”", "“Structured multi-hop graph with typed evidence edges”"],
                ["“Always 99% accurate”", "“Deterministic given data; escalate when ambiguous”"],
            ],
            S,
            [75 * mm, 95 * mm],
        )
    )

    story.append(Spacer(1, 8 * mm))
    story.append(hrule())
    story.append(
        Paragraph(
            "Deeper reading in repo: docs/15 (ontology/RDF), docs/16 (runtime), docs/17 (landscape), "
            "PIPELINE-AND-MODULE-GUIDE.md · Graphviz diagrams 04, 34, 39–41.",
            S["small"],
        )
    )

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUT}")
    return OUT


if __name__ == "__main__":
    build()
