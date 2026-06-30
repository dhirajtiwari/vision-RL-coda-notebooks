/**
 * Senior Solution Architect — Enterprise Implementation Roadmap
 * Run: node docs/scripts/generate_implementation_plan.js
 */

const fs = require("fs");
const path = require("path");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  Header,
  Footer,
  AlignmentType,
  LevelFormat,
  HeadingLevel,
  BorderStyle,
  WidthType,
  ShadingType,
  PageNumber,
  PageBreak,
} = require("docx");

const OUT_DIR = path.join(__dirname, "..");
const PAGE = {
  size: { width: 12240, height: 15840 },
  margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
};
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const p = (t) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun(t)] });
const pb = (ref, t) =>
  new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80 }, children: [new TextRun(t)] });
const code = (t) =>
  new Paragraph({
    spacing: { before: 80, after: 80 },
    shading: { fill: "F2F2F2", type: ShadingType.CLEAR },
    children: [new TextRun({ text: t, font: "Courier New", size: 20 })],
  });
const spacer = () => new Paragraph({ spacing: { after: 200 }, children: [] });
const pgBreak = () => new Paragraph({ children: [new PageBreak()] });

function tbl(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        children: headers.map((h, i) =>
          new TableCell({
            borders,
            width: { size: colWidths[i], type: WidthType.DXA },
            shading: { fill: "1F4E79", type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: "FFFFFF" })] })],
          })
        ),
      }),
      ...rows.map(
        (row) =>
          new TableRow({
            children: row.map((c, i) =>
              new TableCell({
                borders,
                width: { size: colWidths[i], type: WidthType.DXA },
                margins: cellMargins,
                children: [new Paragraph({ children: [new TextRun(String(c))] })],
              })
            ),
          })
      ),
    ],
  });
}

const numbering = {
  config: [
    {
      reference: "bullets",
      levels: [
        {
          level: 0,
          format: LevelFormat.BULLET,
          text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        },
      ],
    },
    {
      reference: "numbers",
      levels: [
        {
          level: 0,
          format: LevelFormat.DECIMAL,
          text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        },
      ],
    },
  ],
};

const styles = {
  default: { document: { run: { font: "Arial", size: 24 } } },
  paragraphStyles: [
    {
      id: "Heading1",
      name: "Heading 1",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 32, bold: true, font: "Arial", color: "1F4E79" },
      paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 },
    },
    {
      id: "Heading2",
      name: "Heading 2",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 28, bold: true, font: "Arial", color: "2E75B6" },
      paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 },
    },
    {
      id: "Heading3",
      name: "Heading 3",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 26, bold: true, font: "Arial" },
      paragraph: { spacing: { before: 120, after: 120 }, outlineLevel: 2 },
    },
  ],
};

function build() {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 300 },
      children: [
        new TextRun({ text: "Enterprise Diagnostics Platform", bold: true, size: 52, color: "1F4E79" }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [
        new TextRun({
          text: "Solution Architecture & Implementation Roadmap",
          size: 34,
          color: "2E75B6",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: "POC · MVP · Production — Warranty Claims Intelligent Triage",
          size: 24,
          italics: true,
        }),
      ],
    }),
    tbl(
      ["Document", "Version", "Date", "Author Role", "Classification"],
      [
        ["Implementation Roadmap", "1.0", "June 25, 2026", "Senior Solution Architect", "Internal — Program Planning"],
      ],
      [2200, 1200, 1800, 2400, 1760]
    ),
    spacer(),
    p(
      "This document defines how to build an enterprise-grade warranty diagnostics platform from the existing diagnostic-chatbot demonstration codebase. Estimates are intentionally conservative. Timelines assume a mid-to-large appliance or consumer durables enterprise with existing CRM, claims, PIM/PLM, and field service systems, moderate integration complexity, and formal change governance."
    ),
    pgBreak(),

    h1("1. Executive Summary"),
    h2("1.1 Business Objective"),
    p(
      "Reduce contact center load for warranty and support by resolving or deflecting low-risk cases through graph-backed automated diagnosis, while escalating only genuine, ambiguous, or safety-critical cases to human agents with a complete, source-traceable diagnostic dossier."
    ),
    h2("1.2 What Exists Today (Demonstration Baseline)"),
    p("The repository diagnostic-chatbot illustrates one possible technical pattern (not validated for any client):"),
    pb("bullets", "Neo4j knowledge graph with Product, Symptom, FailureMode, DiagnosticStep, Part, HistoricalResolution ontology"),
    pb("bullets", "populate_graph.py — MERGE-based Neo4j loader from validated JSON catalog"),
    pb("bullets", "graph/graph_rag.py — graph-native diagnosis (symptom match, failure ranking, escalation rules)"),
    pb("bullets", "agents/diagnosis_graph.py — LangGraph workflow (detect → diagnose → format → escalate)"),
    pb("bullets", "graph/enterprise_pipeline/ — scaffolded ETL with mock CRM, Claims, PIM, FSM connectors"),
    pb("bullets", "Streamlit UI — customer chat, human agent dashboard, knowledge explorer"),
    pb("bullets", "Three synthetic appliance products (wm-001, dw-001, mw-001) in a local demo — not client data; not validated for any enterprise"),
    h2("1.3 What Must Be Built for Enterprise"),
    pb("bullets", "Automated, governed knowledge ingestion from authoritative enterprise systems"),
    pb("bullets", "End-to-end source traceability and provenance on every graph entity and diagnosis evidence line"),
    pb("bullets", "Real CRM, claims, PIM/PLM, and FSM integrations with staging, validation, and operational monitoring"),
    pb("bullets", "Production API, security, SSO, case management handoff, and scalable Neo4j deployment"),
    pb("bullets", "Knowledge engineering operating model for hundreds of product families — not manual JSON authoring"),
    h2("1.4 Recommended Phasing"),
    tbl(
      ["Phase", "Duration", "Purpose", "Realistic Outcome"],
      [
        ["POC", "Weeks 1–8", "Prove graph diagnosis value on limited scope", "2 product families, 1 live read integration, provenance v1, agent dossier"],
        ["MVP", "Weeks 9–16", "Operational pilot with real handoff", "10–15 families, 3 integrations, scheduled ETL, SSO, case write-back"],
        ["Production", "Month 5–24+", "Scale, govern, harden", "100+ families, full connector suite, HA Neo4j, SME workflow, regional rollout"],
      ],
      [1400, 1400, 3200, 3360]
    ),
    spacer(),
    p(
      "Important: covering hundreds of applications with high accuracy is a multi-quarter to multi-year program, not a 16-week outcome. The MVP establishes the operating model; production scale is measured in catalog breadth, integration maturity, and governance — not demo feature count."
    ),

    h2("1.5 Prerequisites"),
    tbl(
      ["Prerequisite", "POC", "MVP", "Production"],
      [
        ["Executive sponsor + budget", "Required", "Required", "Required"],
        ["CRM sandbox / API access", "Read access", "Read + case write", "Full bidirectional"],
        ["Service engineering SME time", "4–8 hrs/week", "8–12 hrs/week", "Standing approval pool"],
        ["Neo4j environment", "Docker staging", "Aura Professional", "Aura Enterprise / cluster"],
        ["Demonstration codebase", "This repository", "Fork + harden", "Managed CI/CD deployment"],
        ["Contact center pilot agreement", "Optional", "Required", "Required"],
        ["Security / IAM review slot", "Deferred", "SSO integration", "Pen test + SOC2 alignment"],
      ],
      [2800, 1600, 2000, 2960]
    ),
    spacer(),

    h2("1.6 Program Assumptions"),
    pb("bullets", "Organization has existing CRM, claims, PIM/PLM, and FSM systems — not greenfield"),
    pb("bullets", "Graph-backed diagnosis remains the source of truth; LLM is formatting/UX augmentation only"),
    pb("bullets", "SME approval is mandatory for safety-related failure modes and diagnostic steps"),
    pb("bullets", "POC uses 2 product families; MVP expands to 10–15; production targets 100+ over 12–24 months"),
    pb("bullets", "Integration APIs are available in sandbox within 2 weeks of program start (or fixtures bridge the gap)"),
    pb("bullets", "Contact center will adopt escalation dossiers only if provenance is complete and override rate is acceptable"),
    pb("bullets", "Decisions on ontology and source precedence are made within 3 business days during POC"),

    h2("1.7 Dependencies"),
    tbl(
      ["Dependency", "Type", "POC Need", "Failure Impact", "Fallback"],
      [
        ["Neo4j 5.x", "Platform", "Staging instance", "No diagnosis", "Docker local; Aura trial"],
        ["PIM / FMEA exports", "Data", "1 family minimum", "Incomplete ontology", "Curated fixture + provenance flag"],
        ["CRM asset API", "Integration", "Sandbox read", "No warranty pre-bind", "Fixture customers (CUST-10042)"],
        ["FSM / Claims history", "Data", "Fixture acceptable", "Weak historical evidence", "Manual HistoricalResolution seed"],
        ["Knowledge engineer", "People", "1.0 FTE", "Blocked catalog build", "Architect bridges short-term"],
        ["Service SMEs", "People", "4 hrs/week", "Unvalidated symptoms", "Defer accuracy targets"],
        ["populate_graph.py", "Code", "Existing loader", "No graph refresh", "Already in repo"],
        ["LangGraph + GraphRAG", "Code", "Existing engine", "No runtime diagnosis", "Already in repo"],
        ["Case management API", "Integration", "JSON file (POC)", "No agent workflow", "Streamlit dashboard"],
        ["SSO / IdP", "Security", "Deferred to MVP", "No agent pilot", "Demo auth only"],
      ],
      [2000, 1400, 1800, 2000, 2160]
    ),
    spacer(),

    pgBreak(),
    h1("2. Solution Architecture"),
    h2("2.1 Logical Architecture"),
    code(
      "ENTERPRISE SOURCES                    PLATFORM                           CONSUMERS\n" +
        "─────────────────                    ────────                           ─────────\n" +
        "PIM/PLM (products, FMEA, manuals) ─┐\n" +
        "FSM (closed work orders)          ─┤\n" +
        "Claims (closed claims, policy)    ─┼──▶ ETL Pipeline ──▶ Staging ──▶ Neo4j KG\n" +
        "CRM (assets, warranty)            ─┤      (enterprise_pipeline)     (populate_graph)\n" +
        "Call center KB / PDF manuals      ─┘              │                        │\n" +
        "                                                  ▼                        ▼\n" +
        "                                         Provenance Store          GraphRAG Engine\n" +
        "                                         (source refs per node)    (graph_rag.py)\n" +
        "                                                                   │\n" +
        "                                         LangGraph Agent ◀─────────┘\n" +
        "                                         (diagnosis_graph.py)\n" +
        "                                               │\n" +
        "                    ┌──────────────────────────┼──────────────────────────┐\n" +
        "                    ▼                          ▼                          ▼\n" +
        "              Customer Channel          Agent Dashboard            Analytics / Audit"
    ),
    h2("2.2 Role of populate_graph.py"),
    p(
      "populate_graph.py is the Load step in ETL. It does not fetch enterprise data. It takes a validated ontology catalog (JSON) and writes nodes and relationships into Neo4j using MERGE, which makes re-runs idempotent."
    ),
    tbl(
      ["JSON Entity", "Neo4j Node / Relationship", "Production Notes"],
      [
        ["product", "(:Product)", "Authoritative ID from PIM"],
        ["symptoms", "(:Symptom) + HAS_SYMPTOM", "SME-reviewed symptom catalog"],
        ["failure_modes", "(:FailureMode) + CAN_HAVE", "From FMEA / reliability engineering"],
        ["diagnostic_steps", "(:DiagnosticStep) + HAS_DIAGNOSTIC_STEP", "From service manuals / SOPs"],
        ["parts", "(:Part)", "From PIM BOM"],
        ["symptom_failure_links", "INDICATES {confidence}", "Calibrated from field + claims data"],
        ["historical_resolutions", "(:HistoricalResolution) + CONFIRMED", "From FSM + claims closures"],
      ],
      [2800, 3200, 3360]
    ),
    spacer(),
    p(
      "In production, populate_graph.py targets staging Neo4j first. Promotion to production occurs only after validation gates and smoke tests pass. The loader logic itself changes little; orchestration, credentials, and governance around it change substantially."
    ),

    h2("2.3 Technology Stack"),
    tbl(
      ["Layer", "POC", "MVP", "Production", "Rationale"],
      [
        ["Knowledge store", "Neo4j Docker local", "Neo4j Aura Professional", "Neo4j Aura Enterprise / self-hosted cluster", "Graph traversal fits diagnostic reasoning"],
        ["ETL", "Python pipeline + fixtures", "Scheduled Airflow/cron job", "Managed ETL + CI/CD + data contracts", "Repeatable, auditable ingestion"],
        ["Agent orchestration", "LangGraph (existing)", "LangGraph + FastAPI", "Same, horizontally scaled API tier", "Typed multi-step workflow"],
        ["Retrieval", "graph_rag.py lexical", "Lexical + limited embeddings pilot", "Hybrid graph + vector retrieval", "Start deterministic; add vectors where justified"],
        ["UI", "Streamlit (acceptable POC)", "React/Next.js or enterprise portal embed", "Omnichannel: web, mobile, agent desktop", "Streamlit not enterprise customer channel"],
        ["Case / escalation", "JSON file", "Salesforce Cases / ServiceNow API", "Integrated ACD + CRM case objects", "Operational workflow requirement"],
        ["Auth", "None", "SSO OIDC (corporate IdP)", "SSO + RBAC + service accounts", "Enterprise security baseline"],
        ["Observability", "Basic logging", "Metrics + alerting on ETL", "Full APM, audit logs, lineage dashboards", "Operational necessity at scale"],
      ],
      [1200, 1600, 2000, 2160, 2400]
    ),
    spacer(),

    pgBreak(),
    h1("3. Source Traceability & Grounded Evidence (Required Design)"),
    p(
      "The current demonstration does not attach provenance metadata to graph entities. For enterprise and contact center trust, every diagnosis element shown to an agent must cite authoritative sources. This is a mandatory design addition — not optional polish."
    ),
    h2("3.1 Provenance Model (Proposed)"),
    p("Extend ontology and Neo4j schema with provenance attributes on nodes and relationships:"),
    code(
      "(:Symptom {\n" +
        "  symptom_id, description, severity,\n" +
        "  source_system: 'PIM|FSM|CallCenterKB|Manual',\n" +
        "  source_record_id: 'SAP-PLM-FMEA-8842',\n" +
        "  source_document_uri: 's3://manuals/wm-001/troubleshooting.pdf#page=14',\n" +
        "  source_version: '2026-Q2',\n" +
        "  ingested_at: '2026-06-01T02:00:00Z',\n" +
        "  approved_by: 'knowledge-engineer@org.com',\n" +
        "  approval_status: 'approved|draft|retired'\n" +
        "})"
    ),
    h2("3.2 What Agents Must See on Escalation"),
    tbl(
      ["Evidence Element", "Displayed To Agent", "Traceability Fields"],
      [
        ["Matched symptom", "Customer language + canonical symptom", "Source system, document, record ID, version, ingest date"],
        ["Ranked failure mode", "Name, confidence, safety notes", "FMEA ID, engineering owner, last calibration date"],
        ["Diagnostic step", "Ordered troubleshooting action", "Service manual section, SOP ID, technician certification level"],
        ["Historical resolution", "Similar past fix", "FSM work order ID or claim ID, closed date, technician notes"],
        ["Part recommendation", "Part number and cost estimate", "PIM BOM reference, supersession chain"],
        ["Warranty context", "Eligible / not eligible", "CRM asset ID, claims policy ID, purchase date source"],
        ["Escalation reason", "Rule that fired", "Rule version, threshold config, audit event ID"],
      ],
      [2400, 3200, 3760]
    ),
    spacer(),
    h2("3.3 Lineage Store"),
    p(
      "Recommendation: maintain a lineage table or graph meta-layer (could be PostgreSQL or Neo4j meta-nodes) mapping entity_id → source payloads, ETL batch ID, transformation version, and approver. GraphRAG evidence[] array should carry source references, not just human-readable strings."
    ),

    pgBreak(),
    h1("4. End-to-End Build Sequence"),
    p("Logical order to construct the platform — each step depends on the prior:"),
    tbl(
      ["Step", "Activity", "Primary Deliverable", "Depends On"],
      [
        ["1", "Confirm ontology with engineering + service SMEs", "Signed ontology spec v1", "Executive sponsorship"],
        ["2", "Inventory authoritative data sources per entity type", "Source system matrix", "Step 1"],
        ["3", "Implement connector contracts (PIM, FSM, Claims, CRM)", "Connector interfaces + mocks", "Step 2"],
        ["4", "Build transformation / OntologyBuilder with validation", "Pydantic schemas + unit tests", "Steps 1–3"],
        ["5", "Implement provenance + approval metadata", "Provenance schema + DB", "Step 4"],
        ["6", "Staging Neo4j + populate_graph.py automation", "Repeatable load job", "Steps 4–5"],
        ["7", "GraphRAG engine + evaluation test suite", "Diagnosis API with metrics", "Step 6"],
        ["8", "LangGraph workflow + escalation integration", "Agent orchestration service", "Step 7"],
        ["9", "Customer channel + agent dashboard with lineage UI", "Pilot UI", "Step 8"],
        ["10", "Operational runbooks, monitoring, SME workflow", "Governance model", "Step 9"],
      ],
      [800, 3600, 2800, 2160]
    ),
    spacer(),

    pgBreak(),
    h1("5. Phase 1 — Proof of Concept (Weeks 1–8)"),
    h2("5.1 POC Objectives"),
    pb("bullets", "Prove that graph-backed diagnosis is more explainable and operationally useful than LLM-only chat for warranty triage"),
    pb("bullets", "Validate ontology and ETL pattern on 2 product families (e.g., front-load washer + dishwasher)"),
    pb("bullets", "Demonstrate escalation dossier with source traceability v1 to contact center stakeholders"),
    pb("bullets", "Establish baseline accuracy metrics on 30–50 curated test scenarios"),
    h2("5.2 POC Scope — In"),
    tbl(
      ["Workstream", "In Scope for POC"],
      [
        ["Products", "2 families (~6–10 SKU variants mapped to family-level graph)"],
        ["Knowledge sources", "1 authoritative source live read (CRM sandbox assets) + PIM/FSM/Claims via controlled exports or fixtures transitioning to API"],
        ["Graph", "Single Neo4j staging instance; populate_graph.py automated in CI"],
        ["Diagnosis", "Existing GraphRAG + LangGraph; add provenance fields to DiagnosisResult"],
        ["UI", "Streamlit acceptable; agent view must show source citations"],
        ["Integrations", "1 read integration (CRM); escalation remains JSON or CRM case draft API in sandbox"],
        ["Security", "Non-prod secrets; no customer PII stored in graph"],
        ["Testing", "30–50 SME-authored scenarios; target ≥70% correct top-1 failure mode on curated set"],
      ],
      [2800, 6560]
    ),
    spacer(),
    h2("5.3 POC Scope — Out (Explicitly Deferred)"),
    pb("bullets", "Full catalog of 100+ product families"),
    pb("bullets", "Production SSO, WAF, multi-region HA"),
    pb("bullets", "Automated PDF manual ingestion at scale"),
    pb("bullets", "Embedding / vector search production rollout"),
    pb("bullets", "Real-time IoT telemetry ingestion"),
    pb("bullets", "Full claims write-back and warranty adjudication automation"),
    pb("bullets", "Customer-facing production channel (POC uses demo / pilot URL only)"),
    h2("5.4 POC Weekly Plan"),
    tbl(
      ["Week", "Focus", "Deliverables"],
      [
        ["1", "Discovery & mobilization", "Source system matrix, ontology workshop, environments provisioned"],
        ["2", "Ontology v1 + provenance schema", "Signed ontology spec, provenance data model, Neo4j staging"],
        ["3", "CRM connector (read) + PIM export pipeline", "Working connector, first catalog JSON for 1 family"],
        ["4", "populate_graph automation + GraphRAG baseline", "Automated load, baseline test harness"],
        ["5", "FSM/Claims historical resolution ingest", "HistoricalResolution nodes with source IDs"],
        ["6", "Agent dossier + traceability UI", "Escalation view with document/system citations"],
        ["7", "SME validation + accuracy benchmarking", "Test report, defect backlog, calibration adjustments"],
        ["8", "POC readout & MVP decision", "Executive demo, recommendation, refined estimate for MVP"],
      ],
      [1000, 3600, 4760]
    ),
    spacer(),
    h2("5.5 POC Team (Realistic)"),
    tbl(
      ["Role", "Allocation", "Responsibility"],
      [
        ["Solution / Enterprise Architect", "40%", "Architecture, integration patterns, governance design"],
        ["Technical Lead (Backend)", "100%", "Pipeline, GraphRAG, LangGraph, code quality"],
        ["Knowledge Engineer / Ontologist", "100%", "Symptom catalog, FMEA mapping, SME sessions"],
        ["Integration Engineer", "75%", "CRM connector, API auth, data contracts"],
        ["Graph / Data Engineer", "75%", "Neo4j, populate_graph, staging promotion"],
        ["Frontend / UX (Agent UI)", "50%", "Agent dashboard traceability views"],
        ["QA Engineer", "50%", "Scenario tests, regression harness"],
        ["Product Owner + Service SME", "25%", "Acceptance criteria, test scenarios"],
        ["DevOps", "25%", "Non-prod environments, CI pipeline"],
      ],
      [3200, 1600, 4560]
    ),
    spacer(),
    p("Effective core team: approximately 5.5–6.0 FTE for 8 weeks."),
    h2("5.6 POC Effort Estimate"),
    tbl(
      ["Metric", "Estimate", "Notes"],
      [
        ["Calendar duration", "8 weeks", "Assumes decisions within 3 business days"],
        ["Person-weeks", "44–52", "Conservative; excludes long procurement delays"],
        ["Direct labor cost (indicative)", "$220K–$380K", "Wide range by geography and contractor mix; excludes licenses"],
        ["Neo4j non-prod license", "$0–$5K", "Community Docker for POC; Aura trial possible"],
        ["Primary risk", "SME availability", "Knowledge engineering blocked without service engineering time"],
      ],
      [2800, 2400, 4160]
    ),
    spacer(),
    h2("5.7 POC Success Criteria"),
    pb("bullets", "≥70% top-1 failure mode accuracy on agreed 30–50 scenario test pack (SME-validated)"),
    pb("bullets", "100% of escalated cases show provenance for symptoms, failure modes, and steps"),
    pb("bullets", "End-to-end demo: CRM asset pre-bind → chat diagnosis → escalation dossier in <10 seconds P95 (non-prod)"),
    pb("bullets", "Documented MVP backlog with refined estimates from measured POC velocity"),

    pgBreak(),
    h1("6. Phase 2 — MVP (Weeks 9–16)"),
    h2("6.1 MVP Objectives"),
    pb("bullets", "Pilot with live contact center agents on limited product scope (10–15 families)"),
    pb("bullets", "Replace demo persistence with real case management integration"),
    pb("bullets", "Run scheduled ETL in non-prod → staging → production promotion with approval"),
    pb("bullets", "Establish minimum viable knowledge governance workflow"),
    h2("6.2 MVP Scope"),
    tbl(
      ["Dimension", "MVP Target", "Rationale"],
      [
        ["Product coverage", "10–15 families", "Enough to validate operations; not full catalog"],
        ["Integrations", "CRM read/write, Claims read, PIM or FSM read", "Minimum for eligibility + handoff + resolutions"],
        ["Channel", "Pilot web chat + agent desktop embed", "Streamlit retired"],
        ["Auth", "Corporate SSO", "Required for agent pilot"],
        ["ETL", "Nightly scheduled pipeline with monitoring", "Operational freshness"],
        ["Provenance", "v2 — linked document viewer URLs where available", "Agent trust requirement"],
        ["Accuracy target", "≥75% top-1 on pilot family test pack; track live override rate", "Measure agent corrections"],
        ["Volume assumption", "Low hundreds diagnoses/day", "Pilot scale only"],
      ],
      [2200, 4200, 2960]
    ),
    spacer(),
    h2("6.3 MVP Weekly Plan (Summary)"),
    tbl(
      ["Weeks", "Milestones"],
      [
        ["9–10", "FastAPI diagnosis service, SSO, retire Streamlit for pilot UI"],
        ["11–12", "CRM + Claims live connectors; case create/update on escalation"],
        ["13", "Scheduled ETL to staging + promotion workflow with SME sign-off queue"],
        ["14", "Expand catalog to 10–15 families via knowledge engineering sprint"],
        ["15", "Agent pilot UAT, override logging, provenance UI hardening"],
        ["16", "MVP go/no-go, production scale program charter"],
      ],
      [2000, 7360]
    ),
    spacer(),
    h2("6.4 MVP Team & Effort"),
    p("MVP requires approximately 6–7 FTE for 8 weeks (48–58 person-weeks). Adds part-time Security Architect (20%) and Change Manager (15%) for SSO and pilot onboarding."),
    tbl(
      ["Metric", "Estimate"],
      [
        ["Person-weeks", "48–58"],
        ["Indicative labor", "$260K–$450K"],
        ["Neo4j Aura Professional (pilot)", "$3K–$8K/month (environment dependent)"],
        ["Program risk", "Integration API instability; plan 2-week buffer for vendor environments"],
      ],
      [4680, 4680]
    ),
    spacer(),

    pgBreak(),
    h1("7. Phase 3 — Production Program (Month 5 Onward)"),
    p(
      "Production is a separate program, not a 2-week extension of MVP. For an enterprise with hundreds of product families, multiple brands, regions, and legacy systems, a realistic production timeline is 12–24 months to reach broad catalog coverage with governed automation — assuming dedicated program funding."
    ),
    h2("7.1 Production Objectives"),
    pb("bullets", "Scale knowledge graph to 100+ product families with governed ingestion"),
    pb("bullets", "Integrate all authoritative systems with incremental sync and lineage"),
    pb("bullets", "Support thousands of diagnoses per day with HA, DR, and SLOs"),
    pb("bullets", "Achieve sustained agent override rate reduction vs. baseline (target set after MVP pilot metrics)"),
    h2("7.2 Production Workstreams"),
    tbl(
      ["Workstream", "Key Activities", "Deliverables"],
      [
        ["Knowledge at scale", "SME workflow, FMEA onboarding factory, manual ingestion pipeline", "100+ families onboarded with approval audit trail"],
        ["Integration factory", "Connector templates, contract tests, secrets rotation", "CRM, Claims, PIM, FSM, CCaaS, IoT (as applicable)"],
        ["Graph platform", "Aura Enterprise cluster, read replicas, backup/DR", "99.9% availability target (business TBD)"],
        ["Retrieval quality", "Hybrid retrieval pilot → production where ROI proven", "Improved symptom recall on noisy customer language"],
        ["Security & compliance", "PII boundary reviews, pen test, SOC2 alignment", "Production security sign-off"],
        ["Operations", "SRE runbooks, on-call, ETL failure playbooks", "24×7 support model for peak season"],
        ["Change management", "Agent training, macro updates, KPI dashboards", "Adoption metrics tied to AHT and escalation rate"],
      ],
      [2400, 4200, 2760]
    ),
    spacer(),
    h2("7.3 Production Catalog Scaling (Realistic)"),
    p("Knowledge engineering throughput — based on industry experience for governed diagnostic content — is typically:"),
    pb("bullets", "2–4 product families per knowledge engineer per month (new onboarding with FMEA + symptoms + steps + SME review)"),
    pb("bullets", "100 families ≈ 25–50 engineer-months of knowledge work, parallelized across a team of 4–6 over 6–12 months"),
    pb("bullets", "Automation reduces manual effort but does not eliminate SME approval; FMEA and safety content require human sign-off"),
    h2("7.4 Production Team (Steady State Program)"),
    tbl(
      ["Role", "FTE", "Notes"],
      [
        ["Program Manager", "1.0", "Cross-workstream coordination"],
        ["Solution Architect", "0.5", "Ongoing design authority"],
        ["Knowledge Engineering Lead + engineers", "4–6", "Catalog scale bottleneck"],
        ["Backend / Graph engineers", "3–4", "ETL, GraphRAG, APIs"],
        ["Integration engineers", "2–3", "Enterprise connectors"],
        ["Frontend engineers", "2", "Customer + agent experiences"],
        ["QA / ML evaluation", "2", "Continuous accuracy regression"],
        ["DevOps / SRE", "1–2", "Platform operations"],
        ["Security architect", "0.25", "Reviews"],
        ["Service engineering SMEs", "0.25 each × pool", "Approval authority"],
      ],
      [3600, 1200, 4560]
    ),
    spacer(),
    h2("7.5 Production Effort & Timeline (Indicative)"),
    tbl(
      ["Horizon", "Scope", "Person-months", "Calendar"],
      [
        ["Foundation hardening", "HA, security, observability, CI/CD", "12–18", "Months 5–7"],
        ["Integration completion", "All planned connectors production-grade", "18–30", "Months 5–10"],
        ["Catalog expansion", "100 families governed", "30–50", "Months 6–18 (parallel)"],
        ["Channel rollout", "Omnichannel + regional", "12–20", "Months 10–18"],
        ["Total program (indicative)", "Broad production", "80–120+", "12–24 months"],
      ],
      [2200, 3600, 1800, 1760]
    ),
    spacer(),
    p(
      "Indicative fully loaded program cost over 18 months: $2.5M–$5.5M depending on geography, vendor licensing, and internal vs. external labor mix. Treat as order-of-magnitude for planning — refine after MVP pilot produces actual velocity data."
    ),

    pgBreak(),
    h1("8. Integration Matrix"),
    tbl(
      ["System", "Data Consumed", "Graph Entities Fed", "POC", "MVP", "Production"],
      [
        ["PIM / PLM", "SKU, BOM, FMEA, manuals metadata", "Product, Part, FailureMode, DiagnosticStep", "Export/fixture", "API read", "Incremental API + version sync"],
        ["FSM", "Closed work orders", "HistoricalResolution, confidence tuning", "Fixture", "API read", "Incremental nightly"],
        ["Claims", "Closed claims, policy", "HistoricalResolution, eligibility rules", "Fixture", "API read", "Read + selective write"],
        ["CRM", "Assets, warranty, customer", "Runtime context; not in static graph", "Sandbox read", "Read + case write", "Full bidirectional"],
        ["CCaaS", "Agent desktop", "Escalation handoff", "Out", "Pilot embed", "Production routing"],
        ["Document store", "PDF manuals", "DiagnosticStep provenance", "Manual", "Pilot URIs", "Automated ingestion assist"],
        ["IoT / error codes", "Smart appliance faults", "Symptom, ErrorCode nodes", "Out", "Out", "Phase 2 production"],
      ],
      [1400, 2200, 2400, 1200, 1200, 2960]
    ),
    spacer(),

    h1("9. Knowledge Base Build at Scale"),
    h2("9.1 Authoritative Source Hierarchy"),
    p("When sources conflict, precedence must be documented:"),
    pb("numbers", "Safety / regulatory content — engineering FMEA and official service manual (highest)"),
    pb("numbers", "Diagnostic steps — current service manual SOP version"),
    pb("numbers", "Symptom-failure confidence — field service + claims empirical data (calibrated, versioned)"),
    pb("numbers", "Customer language variants — call center KB (mapped to canonical symptoms)"),
    h2("9.2 Automated Pipeline (Target State)"),
    code(
      "02:00 UTC — Airflow DAG\n" +
        "  ├─ Extract PIM delta (products, parts, FMEA)\n" +
        "  ├─ Extract FSM closed orders (last 24h)\n" +
        "  ├─ Extract Claims closures (last 24h)\n" +
        "  ├─ Transform → OntologyBuilder + provenance\n" +
        "  ├─ Validate → Pydantic + business rules\n" +
        "  ├─ SME auto-queue (only changed entities)\n" +
        "  ├─ Load staging Neo4j (populate_graph.py)\n" +
        "  ├─ Smoke tests (test_diagnosis.py expanded)\n" +
        "  └─ Promote to production Neo4j (approved batch only)"
    ),
    h2("9.3 Human-in-the-Loop (Non-Negotiable for Safety Content)"),
    pb("bullets", "New failure modes and safety notes require reliability engineer approval"),
    pb("bullets", "Confidence changes >10% on safety-related links require review"),
    pb("bullets", "Retired products/models explicitly marked — never deleted without audit"),

    pgBreak(),
    h1("10. Deliverables Register"),
    tbl(
      ["ID", "Deliverable", "Phase", "Owner"],
      [
        ["D-01", "Ontology specification v1+", "POC", "Knowledge Engineer"],
        ["D-02", "Source system integration matrix", "POC W1", "Architect"],
        ["D-03", "Provenance & lineage schema", "POC W2", "Architect + Data Engineer"],
        ["D-04", "Enterprise ETL pipeline (connectors + OntologyBuilder)", "POC", "Tech Lead"],
        ["D-05", "populate_graph staging automation", "POC W4", "Graph Engineer"],
        ["D-06", "GraphRAG diagnosis API + evaluation harness", "POC", "Tech Lead"],
        ["D-07", "LangGraph agent with escalation", "POC", "Backend Engineer"],
        ["D-08", "Agent dashboard with source citations", "POC W6", "UX + Backend"],
        ["D-09", "POC accuracy & explainability report", "POC W7", "QA + Knowledge Engineer"],
        ["D-10", "FastAPI production service + SSO", "MVP", "Backend"],
        ["D-11", "CRM + Claims production connectors", "MVP", "Integration Engineer"],
        ["D-12", "Scheduled ETL + monitoring", "MVP", "DevOps + Data Engineer"],
        ["D-13", "Knowledge governance workflow tool", "MVP", "Knowledge Engineering Lead"],
        ["D-14", "MVP pilot operations runbook", "MVP W16", "Program Manager"],
        ["D-15", "Production HA Neo4j deployment", "Production", "SRE"],
        ["D-16", "Catalog onboarding playbook (100+ families)", "Production", "Knowledge Engineering Lead"],
        ["D-17", "Security & pen test sign-off pack", "Production", "Security Architect"],
        ["D-18", "KPI dashboard (deflection, override, AHT)", "Production", "Product Owner"],
      ],
      [800, 3600, 1400, 3560]
    ),
    spacer(),

    h1("11. Rationale for Phase Slicing"),
    h2("11.1 Why 8-Week POC"),
    pb("bullets", "Long enough to run real ETL + Neo4j + GraphRAG integration, not just slides"),
    pb("bullets", "Short enough to limit spend before proving accuracy and agent usefulness"),
    pb("bullets", "Defers expensive production hardening until value hypothesis is validated"),
    pb("bullets", "Forces focus on 2 families — exposes knowledge engineering bottlenecks early"),
    h2("11.2 Why MVP Before Production Scale"),
    pb("bullets", "Contact center adoption risk is organizational — must pilot with real agents"),
    pb("bullets", "Integration contracts and API reliability unknown until touched in anger"),
    pb("bullets", "Override rate and provenance usefulness are measurable only in live pilot"),
    pb("bullets", "MVP produces velocity metrics needed to forecast 100-family program honestly"),
    h2("11.3 Why Production Is a Separate Multi-Month Program"),
    pb("bullets", "Hundreds of families × governed SME review = throughput-limited, not code-limited"),
    pb("bullets", "Legacy system integration and regional variation multiply connector work"),
    pb("bullets", "HA, security, and compliance require dedicated engineering, not side-of-desk"),
    pb("bullets", "Accuracy expectations rise with coverage — regression testing burden grows linearly at minimum"),

    pgBreak(),
    h1("12. Risks & Mitigations"),
    tbl(
      ["Risk", "Likelihood", "Impact", "Mitigation"],
      [
        ["SME time unavailable", "High", "High", "Executive sponsor mandate; dedicated knowledge engineer bridge role"],
        ["PIM/FMEA data quality poor", "Medium", "High", "POC source assessment week 1; manual curation fallback with provenance flags"],
        ["Over-reliance on LLM proposed by stakeholders", "Medium", "High", "Architecture principle: graph truth first; LLM formatting only"],
        ["Neo4j licensing cost pushback", "Medium", "Medium", "Start Aura Professional; model TCO vs. contact center savings"],
        ["Integration API changes", "High", "Medium", "Contract tests; abstraction in connector layer (already scaffolded)"],
        ["Accuracy below agent trust threshold", "Medium", "High", "Curated test pack; human override logging; iterative calibration"],
        ["Traceability UI clutter", "Medium", "Medium", "Progressive disclosure: summary + expandable source detail"],
      ],
      [2800, 1400, 1400, 3760]
    ),
    spacer(),

    h1("13. Non-Functional Requirements (Production Targets)"),
    tbl(
      ["NFR", "MVP Pilot", "Production Target", "Notes"],
      [
        ["Diagnosis API P95 latency", "<3s", "<2s", "Excludes CRM enrichment timeouts"],
        ["ETL freshness", "Daily", "Daily + incremental hourly for resolutions", "Business to confirm"],
        ["Availability", "99% business hours", "99.9%", "Aura cluster + API redundancy"],
        ["Audit retention", "90 days", "7 years (if regulatory)", "Align with records management policy"],
        ["RPO / RTO (graph)", "24h / 8h", "1h / 4h", "Neo4j backup strategy"],
        ["Concurrent agents", "20", "500+", "Pilot vs. peak season"],
      ],
      [2800, 2200, 2200, 2160]
    ),
    spacer(),

    h1("14. Key Performance Indicators"),
    tbl(
      ["KPI", "Baseline (Pre-Program)", "MVP Target", "Production Aspirational"],
      [
        ["Tier-1 contact deflection", "Measure current", "+10–15% relative on pilot families", "+25–35% (validated post-scale)"],
        ["Agent average handle time (escalated)", "Measure current", "−10–15%", "−20–30%"],
        ["Top-1 failure mode accuracy (curated tests)", "N/A", "≥75%", "≥80–85% on governed catalog"],
        ["Agent override rate", "N/A", "<40%", "<25% as catalog matures"],
        ["Escalation dossier completeness (provenance)", "0%", "100%", "100%"],
        ["ETL success rate", "N/A", "≥98% weekly", "≥99.5%"],
      ],
      [3200, 2000, 2000, 2160]
    ),
    spacer(),
    p(
      "Note: deflection and AHT targets must be calibrated against your organization's baseline. Do not commit to executive targets until 4–6 weeks of MVP pilot data exist."
    ),

    pgBreak(),
    h1("15. Decision Gates"),
    tbl(
      ["Gate", "Timing", "Go Criteria", "No-Go Outcome"],
      [
        ["POC → MVP", "Week 8", "Accuracy ≥70%, agent dossier accepted by CC lead, CRM read proven", "Pause; fix knowledge or integration approach"],
        ["MVP → Production Program", "Week 16", "Override rate trending down, SSO pilot stable, ETL reliable 4 consecutive weeks", "Extend MVP; do not scale catalog"],
        ["Production regional rollout", "Month 12+", "80% accuracy on regional test pack, security sign-off, SRE ready", "Limit region; expand when metrics support"],
      ],
      [1600, 1600, 3600, 2560]
    ),
    spacer(),

    h1("16. Summary & Recommended Next Steps"),
    pb("numbers", "Week 0: Secure sponsor, allocate 5.5–6 FTE core team, confirm CRM sandbox access"),
    pb("numbers", "Week 1: Ontology workshop + source matrix + provision Neo4j staging"),
    pb("numbers", "Weeks 2–6: Build provenance-aware ETL, automate populate_graph, agent dossier UI"),
    pb("numbers", "Weeks 7–8: SME validation, POC metrics, MVP business case with measured velocity"),
    pb("numbers", "Weeks 9–16: MVP pilot — do not parallelize full 100-family catalog until pilot KPIs stabilize"),
    p(
      "If the graph diagnosis pattern is validated during POC, populate_graph.py may serve as the Load primitive. That is a hypothesis — not confirmed. Enterprise differentiation would come from governed Extract/Transform, provenance, integrations, and knowledge engineering throughput on real client data."
    ),

    h1("17. Document References"),
    pb("bullets", "12-Solution-Approach-and-Delivery-Methodology.docx — approach, rationale, and phased delivery method"),
    pb("bullets", "11-Enterprise-Delivery-Assumptions-Dependencies-and-Open-Questions.docx — authoritative assumptions register (read first)"),
    pb("bullets", "01-Architecture-and-Solution-Design.docx"),
    pb("bullets", "02-Knowledge-Graph-Ontology-and-GraphRAG-Deep-Dive.docx"),
    pb("bullets", "03-Beginners-Guide-Everything-Under-the-Hood.docx"),
    pb("bullets", "04-Cypher-Query-Walkthrough-with-Diagrams.docx"),
    pb("bullets", "10-Production-Pipelines-and-Phased-Roadmap.docx"),
    pb("bullets", "Repository: graph/populate_graph.py, graph/enterprise_pipeline/pipeline.py, graph/graph_rag.py"),
    p(
      "Note: Nothing is validated today. Estimates and phase scope are hypotheses. The reference demo does not confirm feasibility. See Document 11 — all assumptions are status H until client evidence moves them to V."
    ),
  ];
}

async function main() {
  const doc = new Document({
    styles,
    numbering,
    sections: [
      {
        properties: { page: PAGE },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: "Enterprise Diagnostics Platform — Implementation Roadmap",
                    size: 18,
                    color: "666666",
                  }),
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({ text: "Page ", size: 18 }),
                  new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
                ],
              }),
            ],
          }),
        },
        children: build(),
      },
    ],
  });

  const out = path.join(OUT_DIR, "05-Enterprise-Implementation-Roadmap-Solution-Architecture.docx");
  fs.writeFileSync(out, await Packer.toBuffer(doc));
  console.log(`Created: ${out}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});