#!/usr/bin/env python3
"""Generate Full Project & Codebase Encyclopedia PDF (entire repo, not session-only)."""

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
OUT = Path(__file__).resolve().parent / "WarrantyGraph-Full-Project-Codebase-Encyclopedia.pdf"
PNG = ROOT / "docs" / "graphviz" / "rendered" / "png"

TEAL = colors.HexColor("#0f766e")
TEAL_DARK = colors.HexColor("#134e4a")
NAVY = colors.HexColor("#1e3a5f")
SLATE = colors.HexColor("#334155")
LIGHT = colors.HexColor("#f8fafc")
CODE_BG = colors.HexColor("#0f172a")
AMBER = colors.HexColor("#fff7ed")
BORDER = colors.HexColor("#cbd5e1")


def S():
    b = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle(
            "c", parent=b["Title"], fontSize=22, textColor=TEAL_DARK, alignment=TA_CENTER, leading=26
        ),
        "sub": ParagraphStyle(
            "s", parent=b["Normal"], fontSize=11, textColor=SLATE, alignment=TA_CENTER, leading=14, spaceAfter=4
        ),
        "h1": ParagraphStyle(
            "h1", parent=b["Heading1"], fontSize=14, textColor=TEAL_DARK, spaceBefore=10, spaceAfter=6, leading=17
        ),
        "h2": ParagraphStyle(
            "h2", parent=b["Heading2"], fontSize=11.5, textColor=NAVY, spaceBefore=8, spaceAfter=4, leading=14
        ),
        "h3": ParagraphStyle(
            "h3", parent=b["Heading3"], fontSize=10, textColor=SLATE, spaceBefore=6, spaceAfter=3, leading=12
        ),
        "body": ParagraphStyle(
            "body",
            parent=b["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_JUSTIFY,
            leading=12,
            spaceAfter=4,
        ),
        "small": ParagraphStyle("sm", parent=b["Normal"], fontSize=8, textColor=SLATE, leading=10.5, spaceAfter=2),
        "bullet": ParagraphStyle(
            "bu", parent=b["Normal"], fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a")
        ),
        "code": ParagraphStyle(
            "co", parent=b["Code"], fontSize=7, textColor=colors.HexColor("#e2e8f0"), leading=9, fontName="Courier"
        ),
        "center": ParagraphStyle("ce", parent=b["Normal"], fontSize=8.5, alignment=TA_CENTER, textColor=SLATE),
        "note": ParagraphStyle("no", parent=b["Normal"], fontSize=8.5, textColor=TEAL_DARK, leading=11, leftIndent=4),
    }


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(14 * mm, 11 * mm, A4[0] - 14 * mm, 11 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawCentredString(
        A4[0] / 2, 6.5 * mm, f"WarrantyGraph · Full Project & Codebase Encyclopedia  ·  {doc.page}"
    )
    canvas.restoreState()


def tbl(headers, rows, st, widths):
    data = [[Paragraph(f"<font color='white'><b>{h}</b></font>", st["small"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), st["small"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_DARK),
                ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    return t


def bullets(items, st):
    return ListFlowable(
        [ListItem(Paragraph(i, st["bullet"]), leftIndent=6, value="•") for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=10,
        spaceAfter=4,
    )


def code_block(text, st):
    lines = [Paragraph((line.replace(" ", "&nbsp;") or "&nbsp;"), st["code"]) for line in text.splitlines()]
    box = Table([[ln] for ln in lines], colWidths=[172 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (0, 0), 5),
                ("BOTTOMPADDING", (0, -1), (0, -1), 5),
                ("TOPPADDING", (0, 1), (-1, -2), 0.5),
                ("BOTTOMPADDING", (0, 1), (-1, -2), 0.5),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 4)])


def callout(text, st):
    p = Paragraph(text, st["note"])
    box = Table([[p]], colWidths=[172 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), AMBER),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#fdba74")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 4)])


def img(name, st, cap=None, max_h_mm=88):
    path = PNG / name
    out = []
    if not path.exists():
        out.append(Paragraph(f"<i>[Missing diagram {name}]</i>", st["small"]))
        return out
    im = Image(str(path))
    max_w, max_h = 172 * mm, max_h_mm * mm
    aspect = im.imageHeight / float(im.imageWidth)
    w, h = max_w, max_w * aspect
    if h > max_h:
        h = max_h
        w = h / aspect
    im.drawWidth, im.drawHeight = w, h
    out.append(im)
    if cap:
        out.append(Paragraph(f"<i>{cap}</i>", st["center"]))
    out.append(Spacer(1, 4))
    return out


def build():
    st = S()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title="WarrantyGraph Full Project & Codebase Encyclopedia",
        author="Diagnostic Chatbot Project",
    )
    story: list = []

    # COVER
    story.append(Spacer(1, 22 * mm))
    story.append(Paragraph("WarrantyGraph", st["cover"]))
    story.append(Paragraph("Full Project &amp; Codebase Encyclopedia", st["cover"]))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Complete inventory of the repository — every package, API, pipeline, UI surface,<br/>"
            "LLMOps control plane, deploy path, tests, and data artifact.",
            st["sub"],
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        callout(
            "<b>Not session-scoped.</b> This document covers the <b>entire project</b> as it exists in the repo "
            "(agents, API, graph, ETL, frontend, evals, security, k8s, docs corpus, etc.). "
            "Session notes (ontology, Redis, interview Q&amp;A) are only <i>parts</i> of this whole.",
            st,
        )
    )
    story.append(
        Paragraph(
            "Stack: Next.js 16 · FastAPI · Neo4j · LangGraph · GraphRAG · FMEA/Bayes · Enterprise ETL · LLMOps",
            st["center"],
        )
    )
    story.append(PageBreak())

    # 1 PURPOSE
    story.append(Paragraph("1. Product identity &amp; intent", st["h1"]))
    story.append(
        Paragraph(
            "WarrantyGraph is an <b>enterprise-style remote diagnostics platform</b> for appliance warranty support. "
            "A user describes a problem in natural language; the system resolves product/asset context, walks a "
            "<b>Neo4j knowledge graph</b>, ranks failure modes with <b>deterministic FMEA + Bayesian</b> scoring, "
            "returns steps/parts/provenance, and can escalate or submit a claim. "
            "<b>Core diagnosis does not require an LLM</b> — optional gateway is off by default.",
            st["body"],
        )
    )
    story.append(
        tbl(
            ["Facet", "Value"],
            [
                ["Primary UI", "frontend/ Next.js :3000"],
                ["API", "api/ FastAPI :8080"],
                ["Graph", "Neo4j Bolt :7687"],
                ["Mock enterprise", "simulation/ :8090"],
                ["Archived UI", "ui-streamlit-archive/"],
                ["Catalog size", "~13 products (10 OEM builders + 3 legacy)"],
            ],
            st,
            [45 * mm, 127 * mm],
        )
    )

    # 2 REPO MAP
    story.append(Paragraph("2. Repository map (top-level)", st["h1"]))
    story.append(
        code_block(
            "agents/ api/ config/ data/ deploy/ docker/ docs/ domain/ evals/\n"
            "finops/ frontend/ gateway/ graph/ guardrails/ infra/ integrations/\n"
            "k8s/ models/ monitoring/ observability/ promptops/ prompts/\n"
            "runtime/ security/ services/ simulation/ tests/ ui-streamlit-archive/\n"
            "utils/  + Makefile, restart-all.sh, requirements*.txt, .github/",
            st,
        )
    )

    # 3 LAYERS
    story.append(Paragraph("3. Layered architecture", st["h1"]))
    story.append(
        tbl(
            ["Layer", "Packages", "Responsibility"],
            [
                ["Experience", "frontend, ui-streamlit-archive", "Chat, explorer, claims, ops, admin"],
                ["API", "api", "HTTP contracts, middleware, admin pipelines"],
                ["Orchestration", "services, agents, integrations", "Warranty, LangGraph, claims/cases"],
                ["Intelligence", "graph (non-ETL)", "GraphRAG, reliability, trees, parts, viz"],
                ["Knowledge platform", "enterprise_pipeline, populate_graph, OEM catalog", "ETL → Neo4j"],
                [
                    "Cross-cutting",
                    "runtime, guardrails, observability, finops, gateway",
                    "Scale, safety, cost, LLM, telemetry",
                ],
                ["Config/domain", "config, domain", "Settings + typed outcomes"],
                ["Ops data", "utils persistence/lineage/escalation", "SQLite + JSONL"],
                ["Deploy", "docker, k8s, deploy, infra, monitoring", "Run & observe"],
            ],
            st,
            [32 * mm, 58 * mm, 82 * mm],
        )
    )
    story.extend(
        img("39-complete-enterprise-system-pipeline.png", st, "Fig. 1 — Complete system pipeline (as built)", 80)
    )
    story.extend(img("35-layer-architecture-symmetric.png", st, "Fig. 2 — Symmetric layer architecture", 75))

    # 4 PACKAGES
    story.append(PageBreak())
    story.append(Paragraph("4. Package encyclopedia (full codebase)", st["h1"]))

    story.append(Paragraph("4.1 api/ — REST surface", st["h2"]))
    story.append(
        Paragraph(
            "<font face='Courier'>main.py</font> FastAPI app; <font face='Courier'>schemas.py</font> request/response models.",
            st["body"],
        )
    )
    story.append(
        tbl(
            ["Method", "Path", "Purpose"],
            [
                ["GET", "/health", "Liveness + Neo4j + runtime/redis stats"],
                ["GET", "/metrics", "Prometheus metrics"],
                ["GET", "/products", "List products"],
                ["POST", "/diagnose", "Full diagnosis workflow"],
                ["GET", "/graph/ontology", "Schema meta-graph (cached)"],
                ["GET", "/graph/product/{id}", "Product neighborhood (cached)"],
                ["GET", "/graph/diagnosis-subgraph", "Path-focused subgraph"],
                ["GET/POST/PATCH", "/claims*", "Claim list/submit/status"],
                ["GET", "/lineage/batches", "ETL audit batches"],
                ["GET", "/integrations/status", "Connector health"],
                ["POST/GET", "/admin/pipeline/*", "dry-run, validate, review, promote, onboard, status"],
            ],
            st,
            [28 * mm, 58 * mm, 86 * mm],
        )
    )
    story.append(
        Paragraph(
            "Middleware: X-Request-ID, diagnose rate limit, concurrency admission, CORS, OTEL instrument, exception handler.",
            st["small"],
        )
    )

    story.append(Paragraph("4.2 services/ — single business path", st["h2"]))
    story.append(
        Paragraph(
            "<font face='Courier'>diagnosis_service.run_full_diagnosis</font>: warranty short-circuit → "
            "<font face='Courier'>agents.run_diagnosis</font> → optional case handoff. Shared so API/UI rules cannot drift.",
            st["body"],
        )
    )

    story.append(Paragraph("4.3 agents/ — LangGraph workflow", st["h2"]))
    story.append(
        bullets(
            [
                "<font face='Courier'>diagnosis_graph.py</font> — nodes: detect_product → run_diagnosis → format_response → handle_escalation",
                "<font face='Courier'>tools.py</font> — tool_diagnose, tool_detect_product, list products, steps, rank failures",
                "Runs without external LLM (graph-native demo mode)",
            ],
            st,
        )
    )
    story.extend(img("03-langgraph-workflow.png", st, "Fig. 3 — LangGraph workflow", 70))

    story.append(Paragraph("4.4 graph/ — intelligence + knowledge load", st["h2"]))
    story.append(
        tbl(
            ["Module", "Responsibility"],
            [
                ["neo4j_client.py", "Bolt driver singleton + connection pool"],
                ["populate_graph.py", "Constraints + MERGE catalog into Neo4j"],
                ["graph_rag.py", "diagnose(), product resolve, match, rank, format, provenance"],
                ["reliability.py", "FMEA S/O/D, RPN, Action Priority, Bayes, dominance, strength labels"],
                ["diagnostic_engine.py", "NEXT_STEP / CONFIRMS / RULES_OUT trees"],
                ["parts_predictor.py", "REQUIRES_PART + BOM + SKU + claim precedent"],
                ["symptom_retrieval.py", "Hybrid lexical + TF-IDF cosine"],
                ["graph_visualization.py", "Ontology/product/diagnosis graph JSON + HTML helpers"],
                ["knowledge_lineage.py", "Per-product knowledge profile"],
                ["provenance.py", "PROV-O aligned source metadata"],
                ["oem_product_catalog.py", "10 OEM product blueprint builders"],
                ["warranty_catalog_extensions.py", "Model/SKU/Component/Asset/Claim extensions"],
                ["synthetic_data_generator.py", "Legacy products + authoritative catalog build"],
                ["rdf_ontology_export.py", "Export Turtle / RDF-XML ontology"],
            ],
            st,
            [55 * mm, 117 * mm],
        )
    )

    story.append(Paragraph("4.5 graph/enterprise_pipeline/ — ETL platform", st["h2"]))
    story.append(
        tbl(
            ["Component", "Role"],
            [
                ["orchestrator.py", "Run ETL → smoke → promote in order"],
                ["connectors/pim|crm|claims|fsm", "HTTP mock or JSON fixture extract"],
                ["connectors/base.py", "ConnectorResult + ABC"],
                ["transformers/ontology_builder.py", "Merge sources → validated catalog + provenance"],
                ["transformers/pim_blueprint_sync.py", "OEM blueprints → pim_catalog.json"],
                ["pipelines/knowledge_etl.py", "Pipeline 1 extract/transform/write/load"],
                ["pipelines/smoke_validation.py", "Pipeline 2 scenario gate"],
                ["pipelines/staging_promotion.py", "Pipeline 3 promote if smoke passed"],
                ["http_client.py", "GET/POST JSON helper"],
            ],
            st,
            [58 * mm, 114 * mm],
        )
    )
    story.extend(img("41-etl-staging-graph-traversal.png", st, "Fig. 4 — ETL → staging → graph traversal", 78))

    story.append(Paragraph("4.6 integrations/ + simulation/", st["h2"]))
    story.append(
        bullets(
            [
                "<b>crm_enrichment.py</b> — customer/asset → product/SKU/warranty context",
                "<b>warranty_eligibility.py</b> — coverage decision, parts cost vs policy cap",
                "<b>claims_workflow.py</b> — submit/list/update claims; optional Neo4j Claim MERGE",
                "<b>case_management.py</b> — escalation → simulated CCaaS case",
                "<b>simulation/mock_enterprise_apps.py</b> — mock PIM/CRM/FSM/Claims/Cases on :8090",
            ],
            st,
        )
    )

    story.append(Paragraph("4.7 domain/ + config/", st["h2"]))
    story.append(
        Paragraph(
            "<font face='Courier'>domain/models.py</font>: WarrantyDecision, DiagnosisOutcome. "
            "<font face='Courier'>config/settings.py</font>: Neo4j, paths, demo flags, Redis, cache TTLs, rate limits, "
            "LLM keys, OTEL, FinOps budget, tenant, pools, admin token. Fails fast on default password outside demo_mode.",
            st["body"],
        )
    )

    story.append(Paragraph("4.8 runtime/ — scale primitives", st["h2"]))
    story.append(
        bullets(
            [
                "cache.py — in-process TTL or RedisTtlCache; named caches; invalidate after ETL",
                "redis_client.py — optional shared state; health for /health",
                "concurrency.py — parallel_map for connector I/O",
                "concurrency_limit.py — max concurrent diagnoses (503 when saturated)",
                "partitioning.py — tenant/product/batch keys + batch_items",
            ],
            st,
        )
    )

    story.append(Paragraph("4.9 guardrails/ + observability/ + finops/ + gateway/", st["h2"]))
    story.append(
        tbl(
            ["Package", "Modules / role"],
            [
                ["guardrails", "input (injection), output (PII/length), pipeline, action allowlist, rate_limit"],
                ["observability", "JSON logging + request_id, Prometheus metrics, OTEL tracing, redaction"],
                ["finops", "DailyCostBudget circuit breaker (memory or Redis)"],
                ["gateway", "ModelGateway: alias→provider, retry/fallback, meter, budget check"],
                ["promptops + prompts", "Versioned YAML prompts (e.g. diagnosis-rewriter/v1)"],
                ["models/", "registry.yaml pinned model aliases"],
            ],
            st,
            [40 * mm, 132 * mm],
        )
    )

    story.append(Paragraph("4.10 utils/", st["h2"]))
    story.append(
        bullets(
            [
                "persistence.py — SQLite OperationalStore (escalations, cases, claims)",
                "escalation_store.py / lineage_store.py — agent queue + ETL batch audit",
                "diagnosis_display.py — executive formatting, mermaid journeys, grounding tables",
                "connector_status.py — integration_status() for UI/ops",
                "logger.py — get_logger helper",
            ],
            st,
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("4.11 frontend/ — Next.js 16 experience", st["h2"]))
    story.append(
        tbl(
            ["Path", "Role"],
            [
                ["app/page.tsx", "Main UI: diagnosis chat, knowledge explorer, claims, ops, admin"],
                ["app/layout.tsx, providers.tsx", "Shell + React Query providers"],
                ["lib/api.ts", "Client for all backend routes"],
                ["lib/types.ts", "Frontend types"],
                ["globals.css", "Dark/light design tokens"],
            ],
            st,
            [48 * mm, 124 * mm],
        )
    )
    story.append(
        Paragraph(
            "Features: natural-language chat; recommendation strength badges; 3-tile confidence "
            "(posterior / graph link / text match); provenance trail; React Flow explorer with path highlight; "
            "agent cases; ETL lineage; admin pipeline actions.",
            st["body"],
        )
    )

    story.append(Paragraph("4.12 evals/ + tests/", st["h2"]))
    story.append(
        Paragraph(
            "<b>evals/</b>: run_eval.py gate; golden/smoke.jsonl; safety/injection.jsonl; thresholds.yaml. "
            "<b>tests/</b>: API, diagnosis, reliability, symptom retrieval, product resolution, services, "
            "guardrails, observability, OEM catalog, warranty ontology, pipeline integration, enterprise scenarios, "
            "graph viz, persistence, runtime/Redis, RDF export, e2e flow.",
            st["body"],
        )
    )

    story.append(Paragraph("4.13 data/", st["h2"]))
    story.append(
        tbl(
            ["Artifact", "Purpose"],
            [
                ["synthetic_diagnosis_data.json", "Primary runtime catalog (often ETL output)"],
                ["enterprise_knowledge_catalog.json", "Full enterprise catalog payload"],
                ["enterprise_sources/*.json", "PIM/CRM/FSM/claims fixtures"],
                ["provenance_manifest.json", "Default provenance by entity type"],
                ["lineage/etl_batches.jsonl", "Batch audit log"],
                ["diagnostics.db", "SQLite ops store"],
                ["escalations.json / simulated_cases.json", "Supporting/legacy case data"],
            ],
            st,
            [62 * mm, 110 * mm],
        )
    )

    story.append(Paragraph("4.14 Deploy · infra · security · monitoring", st["h2"]))
    story.append(
        bullets(
            [
                "<b>docker/</b> — Dockerfile.api|etl|frontend|mock|ui; compose observability + redis",
                "<b>k8s/base</b> — API, UI, mock, Neo4j StatefulSet, ETL CronJob, ingress, PVC, configmap",
                "<b>k8s/overlays</b> — staging / prod",
                "<b>deploy/rollouts</b> — Argo Rollouts + Flagger canary manifests",
                "<b>infra/terraform</b> — IaC modules/README",
                "<b>monitoring/</b> — alerts, Grafana dashboard, OTEL collector, SLO rules",
                "<b>security/</b> — threat-model.md, owasp-llm-mapping.md",
                "<b>docs/governance/</b> — classification, retention, DPIA",
                "<b>.github/workflows</b> — ci.yml, cd.yml, eval-nightly.yml",
            ],
            st,
        )
    )
    story.extend(img("40-enterprise-network-topology.png", st, "Fig. 5 — Enterprise network topology", 78))
    story.extend(img("30-architecture-LLD-deployment-k8s.png", st, "Fig. 6 — K8s deployment topology", 72))

    story.append(Paragraph("4.15 Documentation corpus (full, not only recent)", st["h2"]))
    story.append(
        bullets(
            [
                "docs/01–14 .docx — architecture, GraphRAG, Cypher, roadmaps, demos, methodology",
                "docs/15–18 .md — ontology/RDF, runtime, landscape, <b>this full encyclopedia</b>",
                "docs/c4 — Structurizr DSL + C4 diagrams",
                "docs/graphviz 01–41 — pipeline, ERD, reliability, topology, etc.",
                "docs/llmops-handbook 00–21 + PDFs + implementation playbook",
                "docs/interview — interview mastery PDF (persona Q&amp;A)",
                "docs/full-project — this encyclopedia PDF",
                "docs/runbooks — cost spike, latency, PII, injection, outage, quality, RAG stale",
                "docs/model-cards/system-card.md",
            ],
            st,
        )
    )

    # 4b INDEXES
    story.append(PageBreak())
    story.append(Paragraph("4b. Indexes &amp; constraints (What / Where / When / How / Why)", st["h1"]))
    story.append(
        Paragraph(
            "Companion: docs/19-Indexes-Constraints-and-Lookup-Performance.md",
            st["small"],
        )
    )
    story.append(
        tbl(
            ["", "Neo4j", "SQLite ops"],
            [
                ["What", "UNIQUE on each entity *_id (+ unique index)", "PK + status indexes"],
                ["Where", "populate_graph.create_constraints", "utils/persistence.py"],
                ["When", "Every graph load/promote", "First DB open"],
                ["How", "CREATE CONSTRAINT IF NOT EXISTS … IS UNIQUE", "CREATE INDEX idx_*_status"],
                ["Why", "Id seek + no duplicates + safe MERGE", "Filter agent queues"],
            ],
            st,
            [22 * mm, 80 * mm, 70 * mm],
        )
    )
    story.append(
        Paragraph(
            "Not used: Neo4j full-text/vector indexes. Symptom text is hybrid TF-IDF after product resolve. "
            "Runtime path: MATCH (p:Product {product_id:$pid}) uses constraint-backed index, then walks edges.",
            st["body"],
        )
    )
    story.append(Paragraph("Universal WWWH lens (use for every subsystem)", st["h2"]))
    story.append(
        tbl(
            ["Topic", "What", "Where", "When"],
            [
                ["Diagnosis", "Rank FM + parts", "api→service→graph_rag", "Each POST /diagnose"],
                ["FMEA/Bayes", "Risk + posteriors", "reliability.py", "During FM ranking"],
                ["ETL", "Catalog + graph", "enterprise_pipeline", "Batch/admin"],
                ["Redis opt.", "Shared multi-pod state", "runtime/", "If REDIS_URL set"],
            ],
            st,
            [32 * mm, 42 * mm, 52 * mm, 46 * mm],
        )
    )

    # 5 ONTOLOGY
    story.append(Paragraph("5. Knowledge model (ontology in Neo4j)", st["h1"]))
    story.append(
        Paragraph(
            "<b>Nodes:</b> Product, Model, SKU, Asset, Symptom, ErrorCode, FailureMode, DiagnosticStep, "
            "Component, Part, Claim, HistoricalResolution, WarrantyPolicy.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Relationships:</b> HAS_MODEL, HAS_SKU, INSTANCE_OF, BOUND_TO_SKU, HAS_SYMPTOM, HAS_ERROR_CODE, "
            "CAN_HAVE, INDICATES, HAS_DIAGNOSTIC_STEP, CONFIRMS, RULES_OUT, NEXT_STEP, IMPACTS_COMPONENT, "
            "REALIZED_BY, REQUIRES_PART, COMPATIBLE_WITH, CONFIRMED, USED_PART, FOR_PRODUCT, COVERED_BY.",
            st["body"],
        )
    )
    story.extend(img("34-enterprise-blueprint-ERD.png", st, "Fig. 7 — Enterprise blueprint ERD", 80))
    story.extend(img("04-graphrag-diagnosis.png", st, "Fig. 8 — GraphRAG diagnosis flow", 72))

    # 6 SEQUENCES
    story.append(Paragraph("6. End-to-end sequences", st["h1"]))
    story.append(Paragraph("6.1 Online diagnosis", st["h2"]))
    story.append(
        code_block(
            "POST /diagnose\n"
            "  rate limit + concurrency slot + guard_request\n"
            "  CRM enrich + warranty gate\n"
            "  run_full_diagnosis → LangGraph\n"
            "    detect product → graph_rag.diagnose\n"
            "      match symptoms/codes → rank FM (reliability)\n"
            "      diagnostic tree → parts_predictor → format + provenance\n"
            "    escalate? → escalation_store / case_management\n"
            "  validate_output → DiagnoseResponse",
            st,
        )
    )
    story.append(Paragraph("6.2 Batch knowledge", st["h2"]))
    story.append(
        code_block(
            "orchestrator /admin/pipeline/*\n"
            "  knowledge_etl: parallel_map(fetch) → OntologyBuilder → JSON + lineage\n"
            "                 optional populate_graph + cache invalidate\n"
            "  smoke_validation (block promote on fail)\n"
            "  staging_promotion → populate_graph MERGE",
            st,
        )
    )

    # 7 SETTINGS
    story.append(Paragraph("7. Configuration surface", st["h1"]))
    story.append(
        Paragraph(
            "Groups in settings: Neo4j + pool; data paths; demo/fixture/mock flags; connector URLs; "
            "API host/port/admin token; diagnosis thresholds (escalation, symptom score, ambiguity); "
            "cache TTLs + ETL workers; Redis URL/prefix; max concurrent diagnoses; rate limit; PII/length; "
            "OTEL/Prometheus; LLM enablement + keys; daily budget; default tenant.",
            st["body"],
        )
    )

    # 8 PRODUCTS
    story.append(Paragraph("8. Product catalog (13)", st["h1"]))
    story.append(
        Paragraph(
            "OEM builders (Samsung/LG/Whirlpool/Bosch/GE washers, dishwashers, dryer, range, fridge, microwave) "
            "plus legacy wm-001, dw-001, mw-001. Public-doc patterns; representative service BOM — not secret SKUs.",
            st["body"],
        )
    )

    # 9 RUN
    story.append(Paragraph("9. Local runbook", st["h1"]))
    story.append(
        code_block(
            "python -m venv venv && source venv/bin/activate\n"
            "pip install -r requirements.txt\n"
            "python graph/populate_graph.py\n"
            "uvicorn api.main:app --port 8080\n"
            "cd frontend && npm install && npm run dev\n"
            "# optional: python -m simulation.mock_enterprise_apps\n"
            "# optional: REDIS_URL=redis://localhost:6379/0\n"
            "python -m graph.enterprise_pipeline.orchestrator\n"
            "./restart-all.sh",
            st,
        )
    )

    # 10 QUALITY
    story.append(Paragraph("10. Quality gates", st["h1"]))
    story.append(
        bullets(
            [
                "pytest full suite (pre-push hook with venv)",
                "ruff lint/format (pre-commit)",
                "evals/run_eval.py golden + safety thresholds",
                "CI: tests, supply-chain audit, diagram render",
                "Nightly eval workflow; CD image publish",
            ],
            st,
        )
    )

    # 11 SECURITY
    story.append(Paragraph("11. Security posture (honest)", st["h1"]))
    story.append(
        tbl(
            ["Control", "Status"],
            [
                ["Input injection guardrails", "Implemented"],
                ["Output PII redaction", "Implemented"],
                ["Action allowlist / HITL hooks", "Implemented"],
                ["Rate limit / admission control", "Implemented (memory or Redis)"],
                ["Admin token for pipelines", "Optional setting"],
                ["End-user OIDC/JWT", "Not productized (demo open)"],
                ["Live SAP/SFDC", "Mock/fixtures by default; connectors pluggable"],
                ["Fixture honesty", "Provenance / simulated labels"],
            ],
            st,
            [55 * mm, 117 * mm],
        )
    )

    # 12 WHERE IS X
    story.append(Paragraph("12. Where is X? (quick index)", st["h1"]))
    story.append(
        tbl(
            ["Need", "Location"],
            [
                ["HTTP entry", "api/main.py"],
                ["Business rules once", "services/diagnosis_service.py"],
                ["Agent steps", "agents/diagnosis_graph.py"],
                ["Diagnosis brain", "graph/graph_rag.py"],
                ["Scoring math", "graph/reliability.py"],
                ["Parts ranking", "graph/parts_predictor.py"],
                ["Diagnostic trees", "graph/diagnostic_engine.py"],
                ["Load Neo4j", "graph/populate_graph.py"],
                ["ETL spine", "graph/enterprise_pipeline/"],
                ["OEM content", "graph/oem_product_catalog.py"],
                ["Settings", "config/settings.py"],
                ["UI API client", "frontend/lib/api.ts"],
                ["Mock backends", "simulation/mock_enterprise_apps.py"],
                ["Cache/Redis", "runtime/"],
                ["Guardrails", "guardrails/"],
                ["Metrics/traces", "observability/"],
                ["Optional LLM", "gateway/ + models/registry.yaml"],
                ["Eval gate", "evals/run_eval.py"],
                ["Kubernetes", "k8s/"],
                ["Diagrams", "docs/graphviz/ (esp. 34–41), docs/c4/"],
            ],
            st,
            [48 * mm, 124 * mm],
        )
    )

    # 13 GAPS
    story.append(Paragraph("13. Explicit gaps / non-goals", st["h1"]))
    story.append(
        bullets(
            [
                "Not full multi-tenant SaaS with OIDC out of the box",
                "Not live SAP/Salesforce by default (mock + fixtures)",
                "Not vector-DB-first RAG (graph-first; hybrid lexical optional)",
                "LLM not required for core path",
                "Future: async ETL workers, Neo4j HA, Postgres ops DB, claim→learning loop",
            ],
            st,
        )
    )

    story.append(Paragraph("14. How this relates to other docs", st["h1"]))
    story.append(
        tbl(
            ["Document", "Scope"],
            [
                ["This encyclopedia (18 + PDF)", "Entire codebase & project"],
                ["docs/15–17", "Ontology/RDF, runtime scale, landscape"],
                ["docs/interview/*", "Interview Q&amp;A style prep"],
                ["README.md", "Quick start & product overview"],
                ["PIPELINE-AND-MODULE-GUIDE.md", "Phase 0–5 blueprint→claim"],
                ["llmops-handbook/*", "LLMOps disciplines depth"],
            ],
            st,
            [55 * mm, 117 * mm],
        )
    )

    story.append(Spacer(1, 6 * mm))
    story.append(
        callout(
            "<b>Editable source of truth:</b> docs/18-FULL-PROJECT-CODEBASE-ENCYCLOPEDIA.md · "
            "Regenerate PDF: python docs/full-project/generate_full_project_pdf.py",
            st,
        )
    )

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUT}")
    return OUT


if __name__ == "__main__":
    build()
