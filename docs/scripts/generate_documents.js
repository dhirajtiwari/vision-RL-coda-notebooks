/**
 * Generates enterprise documentation Word files for the Diagnostics Chatbot.
 * Run: node docs/scripts/generate_documents.js
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
  ImageRun,
} = require("docx");

const DIAGRAMS_DIR = path.join(__dirname, "..", "diagrams");

const OUT_DIR = path.join(__dirname, "..");

const PAGE = {
  size: { width: 12240, height: 15840 },
  margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
};
const CONTENT_WIDTH = 9360;

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text, ...opts })],
  });
}
function bullet(ref, text) {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [new TextRun(text)],
  });
}
function codeBlock(text) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    shading: { fill: "F2F2F2", type: ShadingType.CLEAR },
    children: [new TextRun({ text, font: "Courier New", size: 20 })],
  });
}
function table(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    children: headers.map((h, i) =>
      new TableCell({
        borders,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: "2E75B6", type: ShadingType.CLEAR },
        margins: cellMargins,
        children: [
          new Paragraph({
            children: [new TextRun({ text: h, bold: true, color: "FFFFFF" })],
          }),
        ],
      })
    ),
  });
  const dataRows = rows.map(
    (row) =>
      new TableRow({
        children: row.map(
          (cell, i) =>
            new TableCell({
              borders,
              width: { size: colWidths[i], type: WidthType.DXA },
              shading: { fill: "FFFFFF", type: ShadingType.CLEAR },
              margins: cellMargins,
              children: [new Paragraph({ children: [new TextRun(String(cell))] })],
            })
        ),
      })
  );
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}
function spacer() {
  return new Paragraph({ spacing: { after: 200 }, children: [] });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}
function imageParagraph(filename, width, height, caption) {
  const data = fs.readFileSync(path.join(DIAGRAMS_DIR, filename));
  const children = [
    new ImageRun({
      type: "png",
      data,
      transformation: { width, height },
      altText: { title: caption, description: caption, name: filename },
    }),
  ];
  const paras = [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children }),
  ];
  if (caption) {
    paras.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: caption, italics: true, size: 20, color: "666666" })],
      })
    );
  }
  return paras;
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

const docStyles = {
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

function buildDoc1() {
  const children = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({ text: "Enterprise Diagnostics Chatbot", bold: true, size: 48, color: "1F4E79" }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [
        new TextRun({
          text: "Architecture, Process & Solution Design",
          size: 32,
          italics: true,
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 },
      children: [new TextRun({ text: "Warranty Claims Intelligent Triage Platform", size: 24 })],
    }),
    p("Document Version: 1.0"),
    p("Date: June 25, 2026"),
    p("Classification: Internal / Solution Architecture"),
    pageBreak(),

    h1("1. Executive Summary"),
    p(
      "This document describes the end-to-end architecture, business process, and solution design for an Enterprise Diagnostics Chatbot platform purpose-built for warranty claims triage. The application combines a Neo4j knowledge graph, a GraphRAG retrieval layer, and a LangGraph agent orchestration workflow to deliver explainable, graph-backed appliance diagnosis before a case reaches a human contact center agent."
    ),
    p(
      "The primary business objective is to reduce contact center workload by resolving or deflecting non-genuine, low-complexity, or self-service-eligible warranty inquiries at the automated tier, while ensuring that only genuine, high-risk, or low-confidence cases are escalated—with a complete diagnostic payload including appliance identity, matched symptoms, ranked failure modes, recommended troubleshooting steps, safety notes, and historical resolution precedents."
    ),
    p(
      "A reference demo implementation (diagnostic-chatbot) illustrates this architecture using three synthetic appliance product lines, mock enterprise fixtures, Neo4j, LangGraph, and Streamlit. The demo does not validate this design for any client — it shows one possible end-to-end flow for discussion."
    ),
    p(
      "Nothing is validated: not the client's enterprise landscape, product catalog, data sources, contact center model, or the suitability of this technical approach at scale. See Document 11 (Assumptions Register) and Document 12 (Solution Approach & Delivery Methodology) for the delivery method, rationale, and validation gates."
    ),

    h1("2. Business Context & Use Case"),
    h2("2.1 Warranty Claims Challenge"),
    p(
      "Consumer appliance manufacturers and extended warranty providers face high volumes of inbound warranty claims through web portals, mobile apps, IVR, and contact centers. A significant portion of these contacts are:"
    ),
    bullet("bullets", "User-error or maintenance issues not covered under warranty"),
    bullet("bullets", "Duplicate claims for the same registered product"),
    bullet("bullets", "Claims filed outside warranty period or without proof of purchase"),
    bullet("bullets", "Symptoms resolvable through guided self-troubleshooting"),
    bullet("bullets", "Safety-critical issues requiring immediate human intervention"),
    p(
      "Without intelligent triage, every inquiry is treated equally, inflating average handle time (AHT), increasing agent training burden, and delaying resolution for genuinely urgent cases."
    ),

    h2("2.2 Target Outcomes"),
    table(
      ["Metric", "Target Impact", "Mechanism"],
      [
        ["Contact center deflection", "30–50% reduction in tier-1 escalations", "Automated diagnosis + self-service steps"],
        ["Average handle time", "20–40% reduction on escalated cases", "Pre-populated diagnostic dossier for agents"],
        ["First-contact resolution", "Increase via guided troubleshooting", "Graph-backed step-by-step procedures"],
        ["Warranty fraud / invalid claims", "Early filtering", "CRM + claims system eligibility checks"],
        ["Safety incidents", "Zero missed critical escalations", "Severity-based mandatory escalation rules"],
      ],
      [2800, 2800, 3760]
    ),
    spacer(),

    h2("2.3 Stakeholders"),
    bullet("bullets", "End Customer / Appliance Owner — reports symptoms via chat, receives diagnosis"),
    bullet("bullets", "Contact Center Agent — reviews escalated cases with full graph evidence"),
    bullet("bullets", "Field Service Technician — receives confirmed failure mode and parts list"),
    bullet("bullets", "Warranty Claims Analyst — validates claim eligibility against policy rules"),
    bullet("bullets", "Knowledge Engineering Team — maintains ontology, diagnostic trees, symptom-failure mappings"),
    bullet("bullets", "Integration / Platform Engineering — connects CRM, claims, PIM, and service history systems"),

    h1("3. Solution Overview"),
    h2("3.1 Design Principles"),
    bullet("bullets", "Explainability first: every diagnosis cites graph evidence (symptoms, confidence scores, historical resolutions)"),
    bullet("bullets", "Graph-native reasoning: diagnosis is driven by structured knowledge, not opaque LLM hallucination"),
    bullet("bullets", "Deterministic escalation: critical severity and low confidence trigger mandatory human review"),
    bullet("bullets", "Enterprise integration ready: customer, product, and claim context enriched from external systems"),
    bullet("bullets", "Graceful LLM augmentation: optional LLM layer for natural language formatting without replacing graph truth"),

    h2("3.2 Technology Stack"),
    table(
      ["Layer", "Technology", "Role"],
      [
        ["Presentation", "Streamlit (demo) / React + API (production)", "Customer chat, agent dashboard, KG explorer"],
        ["Orchestration", "LangGraph StateGraph", "Multi-step agent workflow with typed state"],
        ["Reasoning / Retrieval", "GraphRAG (custom Python layer)", "Symptom matching, failure ranking, evidence assembly"],
        ["Knowledge Store", "Neo4j 5.x (property graph)", "Ontology instances, relationships, confidence weights"],
        ["Data Contracts", "Pydantic models + JSON catalog", "Validated knowledge ingestion schema"],
        ["Escalation Store", "JSON file (demo) / Case Management API (prod)", "Human agent work queue"],
        ["Optional LLM", "Grok / OpenAI via API key", "NL generation, query expansion (future)"],
        ["Infrastructure", "Docker (Neo4j), Python 3.12, venv", "Local demo; K8s/cloud in production"],
      ],
      [2200, 2800, 4360]
    ),
    spacer(),

    h1("4. High-Level Architecture"),
    p("The platform follows a layered architecture with clear separation between user interaction, agent orchestration, graph retrieval, and enterprise data sources."),
    codeBlock(
      "┌─────────────────────────────────────────────────────────────────────────┐\n" +
        "│                     CHANNELS & ENTERPRISE SYSTEMS                       │\n" +
        "│  Web Portal │ Mobile App │ IVR │ CRM │ Claims Mgmt │ PIM │ Service DB  │\n" +
        "└───────────────────────────────┬─────────────────────────────────────────┘\n" +
        "                                │ Integration Layer (API Gateway / ESB)\n" +
        "┌───────────────────────────────▼─────────────────────────────────────────┐\n" +
        "│                    DIAGNOSTICS PLATFORM (This Application)              │\n" +
        "│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────────────┐  │\n" +
        "│  │ Streamlit UI │  │ LangGraph Agent │  │ GraphRAG Query Engine    │  │\n" +
        "│  │ - Chat       │──│ detect_product  │──│ match_symptoms           │  │\n" +
        "│  │ - Dashboard  │  │ run_diagnosis   │  │ rank_failure_modes       │  │\n" +
        "│  │ - KG Explorer│  │ format_response │  │ get_diagnostic_steps     │  │\n" +
        "│  │              │  │ handle_escalate │  │ historical_resolutions   │  │\n" +
        "│  └──────────────┘  └─────────────────┘  └────────────┬─────────────┘  │\n" +
        "│                                                       │                 │\n" +
        "│  ┌────────────────────────────────────────────────────▼──────────────┐  │\n" +
        "│  │                    NEO4J KNOWLEDGE GRAPH                          │  │\n" +
        "│  │  Product ──HAS_SYMPTOM──▶ Symptom ──INDICATES──▶ FailureMode      │  │\n" +
        "│  │  Product ──HAS_DIAGNOSTIC_STEP──▶ DiagnosticStep                │  │\n" +
        "│  │  HistoricalResolution ──CONFIRMED──▶ FailureMode                  │  │\n" +
        "│  └───────────────────────────────────────────────────────────────────┘  │\n" +
        "└─────────────────────────────────────────────────────────────────────────┘"
    ),

    h2("4.1 Request Lifecycle"),
    bullet("numbers", "Customer describes appliance problem in natural language (optionally selects product)"),
    bullet("numbers", "LangGraph agent detects product from message keywords or explicit selection"),
    bullet("numbers", "GraphRAG matches customer message to canonical symptoms in the knowledge graph"),
    bullet("numbers", "Cypher query ranks failure modes by aggregated INDICATES confidence across matched symptoms"),
    bullet("numbers", "Diagnostic steps, parts, and historical resolutions are retrieved for the top failure mode"),
    bullet("numbers", "Confidence score and symptom severity evaluated against escalation threshold (default 65%)"),
    bullet("numbers", "If escalation required: case saved with full diagnostic payload for human agent dashboard"),
    bullet("numbers", "Formatted response returned to customer with graph evidence trail"),

    h1("5. Component Architecture"),
    h2("5.1 Project Structure"),
    table(
      ["Module", "Path", "Responsibility"],
      [
        ["Configuration", "config/settings.py", "Neo4j credentials, escalation threshold, data paths"],
        ["Knowledge Ingestion", "graph/synthetic_data_generator.py", "Pydantic-validated ontology instances"],
        ["Graph Loader", "graph/populate_graph.py", "MERGE nodes/relationships into Neo4j with constraints"],
        ["Neo4j Client", "graph/neo4j_client.py", "Driver singleton, connectivity verification"],
        ["GraphRAG Engine", "graph/graph_rag.py", "Core diagnosis: symptom match, failure rank, evidence"],
        ["Agent Tools", "agents/tools.py", "Thin wrappers exposing GraphRAG to LangGraph nodes"],
        ["LangGraph Workflow", "agents/diagnosis_graph.py", "StateGraph: detect → diagnose → format → escalate"],
        ["Escalation Store", "utils/escalation_store.py", "Persist cases for human agent review"],
        ["UI", "ui/app.py", "Customer chat, agent dashboard, knowledge graph browser"],
        ["Evaluation", "tests/test_diagnosis.py", "Regression tests against known symptom messages"],
      ],
      [2400, 3200, 3760]
    ),
    spacer(),

    h2("5.2 LangGraph Agent Workflow"),
    p(
      "The diagnosis agent is implemented as a compiled LangGraph StateGraph with a typed AgentState dictionary. Each node is a pure function that receives state and returns partial state updates."
    ),
    table(
      ["Node", "Function", "Input → Output"],
      [
        ["detect_product", "node_detect_product", "user_message → product_id, product_name"],
        ["run_diagnosis", "node_run_graph_diagnosis", "user_message + product_id → diagnosis dict"],
        ["format_response", "node_format_response", "diagnosis → formatted markdown response"],
        ["handle_escalation", "node_handle_escalation", "diagnosis.should_escalate → case_id, escalated flag"],
      ],
      [2200, 2800, 4360]
    ),
    spacer(),
    p(
      "The graph is linear (no conditional branching at the graph level); escalation logic is embedded in the diagnosis result. Production deployments may add conditional edges—for example, routing to a CRM enrichment node when product_id is unknown but a customer serial number is provided."
    ),

    h2("5.3 GraphRAG Layer (Summary)"),
    p(
      "GraphRAG in this solution is not vector-only retrieval. It is a hybrid graph traversal + lexical similarity approach that queries structured relationships in Neo4j and assembles an explainable DiagnosisResult. See Document 2 (Knowledge Graph & GraphRAG Deep Dive) for full technical detail."
    ),
    bullet("bullets", "Product detection: keyword scoring against appliance vocabulary"),
    bullet("bullets", "Symptom matching: token overlap + synonym expansion against graph symptom descriptions"),
    bullet("bullets", "Failure ranking: Cypher aggregation of INDICATES confidence scores"),
    bullet("bullets", "Evidence assembly: diagnostic steps, parts catalog, historical resolutions"),

    h2("5.4 Escalation Model"),
    p("A case is escalated to the human agent tier when ANY of the following conditions is true:"),
    bullet("bullets", "Product could not be identified from the customer message"),
    bullet("bullets", "Any matched symptom has severity = critical (e.g., microwave arcing, no heating)"),
    bullet("bullets", "Top failure mode aggregate confidence is below ESCALATION_CONFIDENCE_THRESHOLD (default 0.65)"),
    p(
      "Escalated cases are persisted with case_id, timestamp, customer message, and the complete diagnosis payload including ranked failure modes, evidence strings, and escalation reason. The Human Agent Dashboard displays this dossier so agents begin with full context rather than re-interviewing the customer."
    ),

    h1("6. Enterprise Integration Architecture"),
    h2("6.1 Integration Landscape"),
    p(
      "In a production warranty scenario, the diagnostics platform does not operate in isolation. It must interface with multiple enterprise applications to validate claim eligibility, enrich customer context, and push outcomes back to operational systems."
    ),
    codeBlock(
      "Customer ──▶ Diagnostics Chatbot ──▶ Integration Hub ──┬──▶ CRM (Salesforce/SAP C4C)\n" +
        "                                                      ├──▶ Claims System (Guidewire/legacy)\n" +
        "                                                      ├──▶ Product Information Mgmt (PIM/PLM)\n" +
        "                                                      ├──▶ Service History / IoT Telemetry\n" +
        "                                                      ├──▶ Parts & Inventory (SAP/Oracle)\n" +
        "                                                      └──▶ Contact Center (Genesys/Five9)"
    ),

    h2("6.2 CRM System Integration"),
    p("Purpose: Resolve appliance owner identity, registered products, purchase date, and warranty status."),
    table(
      ["Data Element", "Source", "Usage in Diagnosis"],
      [
        ["Customer ID / Account", "CRM", "Link chat session to owner profile"],
        ["Registered Products", "CRM Asset Registry", "Pre-select product_id; skip keyword detection"],
        ["Serial Number / Model", "CRM or Product Registration", "Validate against PIM catalog"],
        ["Purchase Date", "CRM / POS integration", "Warranty eligibility window check"],
        ["Contact Preferences", "CRM", "Escalation routing (callback vs. chat transfer)"],
        ["Prior Cases", "CRM Case History", "Detect duplicate claims; show prior resolutions"],
      ],
      [2800, 2800, 3760]
    ),
    spacer(),
    p(
      "Integration pattern: On session start, the chatbot calls GET /crm/customers/{id}/assets. If the customer has a single registered appliance, product_id is pre-bound. If multiple, the UI presents a disambiguation picker. This eliminates false product detection and enables warranty-aware responses."
    ),

    h2("6.3 Claims Management System Integration"),
    p("Purpose: Create, update, and close warranty claim records based on diagnosis outcome."),
    table(
      ["Event", "Direction", "Claims System Action"],
      [
        ["Diagnosis complete (no escalation)", "Outbound", "Log self-service resolution; no claim opened"],
        ["Diagnosis complete (escalated)", "Outbound", "Create draft claim with diagnostic dossier attached"],
        ["Agent resolves case", "Outbound", "Update claim status; attach confirmed failure mode"],
        ["Claim eligibility check", "Inbound", "Validate warranty coverage before offering repair dispatch"],
        ["Fraud signals", "Bidirectional", "Flag repeat claims, mismatched serial numbers"],
      ],
      [3200, 2000, 4160]
    ),
    spacer(),

    h2("6.4 Product Information Management (PIM)"),
    p(
      "PIM/PLM systems are the authoritative source for product taxonomy, model variants, BOM (bill of materials), and service manuals. In enterprise deployment, the knowledge graph ontology is populated from PIM exports rather than synthetic JSON:"
    ),
    bullet("bullets", "Product nodes: model SKU, brand, category, model year, market region"),
    bullet("bullets", "Part nodes: OEM part numbers, supersession chains, regional availability"),
    bullet("bullets", "FailureMode nodes: FMEA (Failure Mode and Effects Analysis) data from engineering"),
    bullet("bullets", "DiagnosticStep nodes: extracted from service manuals and technician SOPs"),

    h2("6.5 Service History & Field Data"),
    p(
      "HistoricalResolution nodes in the demo represent field service outcomes. In production, these are continuously fed from:"
    ),
    bullet("bullets", "Field service management (FSM) work order closures"),
    bullet("bullets", "Contact center case resolution notes"),
    bullet("bullets", "IoT-connected appliance error logs and telemetry (smart appliances)"),
    bullet("bullets", "Technician mobile app diagnostic confirmations"),
    p(
      "This creates a feedback loop: confirmed resolutions strengthen INDICATES confidence weights and add new symptom-failure links over time."
    ),

    h2("6.6 Contact Center Handoff"),
    p(
      "When escalation occurs, the platform pushes a structured handoff package to the contact center ACD/CRM:"
    ),
    bullet("bullets", "case_id and priority (derived from symptom severity)"),
    bullet("bullets", "Customer profile snapshot from CRM"),
    bullet("bullets", "Appliance: product name, model, serial, warranty status"),
    bullet("bullets", "Customer verbatim message"),
    bullet("bullets", "Matched symptoms with severity labels"),
    bullet("bullets", "Top 3 ranked failure modes with confidence and safety notes"),
    bullet("bullets", "Recommended diagnostic steps already communicated to customer"),
    bullet("bullets", "Similar historical resolutions for agent reference"),
    bullet("bullets", "Escalation reason (critical symptom / low confidence / unknown product)"),
    p(
      "This ensures agents handle only genuine, complex, or safety-critical cases—with full appliance owner details and a head start on diagnosis."
    ),

    h1("7. End-to-End Process Flows"),
    h2("7.1 Happy Path — Automated Resolution"),
    bullet("numbers", "Customer logs into warranty portal (CRM SSO authenticates session)"),
    bullet("numbers", "CRM returns registered Front Load Washing Machine (wm-001) with active warranty"),
    bullet("numbers", "Customer: 'Machine won't spin and water stays in drum'"),
    bullet("numbers", "GraphRAG matches symptoms wm-s01 (no spin) and wm-s03 (water in drum)"),
    bullet("numbers", "Failure modes ranked: Worn Drive Belt (0.92), Failed Drain Pump (0.88)"),
    bullet("numbers", "Top confidence 0.92 > threshold 0.65; no critical severity → no escalation"),
    bullet("numbers", "Customer receives diagnostic steps and self-service guidance"),
    bullet("numbers", "Claims system logs self-service event; no agent involvement"),

    h2("7.2 Escalation Path — Critical Symptom"),
    bullet("numbers", "Customer: 'Microwave runs but food stays cold, arcing inside'"),
    bullet("numbers", "Product detected: mw-001 (Convection Microwave)"),
    bullet("numbers", "Symptoms matched: mw-s01 (critical), mw-s02 (critical)"),
    bullet("numbers", "Failure modes: Magnetron Failure, Damaged Waveguide Cover"),
    bullet("numbers", "Critical severity triggers mandatory escalation regardless of confidence"),
    bullet("numbers", "Case saved to escalation store with full payload"),
    bullet("numbers", "Contact center receives priority case with safety notes (HIGH VOLTAGE warning)"),
    bullet("numbers", "Agent reviews pre-built dossier; schedules certified technician visit"),

    h2("7.3 Invalid Claim Filtering (Enterprise Extension)"),
    bullet("numbers", "Customer files claim for dishwasher heating issue"),
    bullet("numbers", "CRM returns purchase date 4 years ago; standard warranty = 2 years"),
    bullet("numbers", "Claims system returns NOT_ELIGIBLE status before diagnosis begins"),
    bullet("numbers", "Chatbot informs customer of warranty status; offers paid repair options"),
    bullet("numbers", "No escalation to contact center for out-of-warranty cases"),

    h1("8. Security, Compliance & Operations"),
    h2("8.1 Data Security"),
    bullet("bullets", "PII (customer name, address, phone) stored only in CRM; chatbot holds session tokens"),
    bullet("bullets", "Neo4j knowledge graph contains no customer PII—only product/diagnostic knowledge"),
    bullet("bullets", "Escalation payloads reference customer_id, not raw PII, in production"),
    bullet("bullets", "TLS for all API integrations; Neo4j bolt+ssc or mTLS in production"),

    h2("8.2 Audit & Explainability"),
    bullet("bullets", "Every diagnosis includes an evidence[] array citing graph reasoning steps"),
    bullet("bullets", "Escalation reason is explicit and logged"),
    bullet("bullets", "Agent actions (in_progress, resolved, closed) timestamped in escalation store"),
    bullet("bullets", "Future: LangSmith tracing for LLM-augmented responses"),

    h2("8.3 Deployment Topology (Production)"),
    table(
      ["Component", "Deployment", "Scaling"],
      [
        ["Streamlit / Web UI", "Container behind CDN + WAF", "Horizontal auto-scale"],
        ["LangGraph API", "FastAPI/uvicorn containers", "Per-request scaling"],
        ["Neo4j", "Neo4j AuraDB or self-hosted cluster", "Read replicas for GraphRAG queries"],
        ["Integration Hub", "Enterprise Service Bus or API Gateway", "Managed service"],
        ["Escalation Queue", "Case management DB or Salesforce Cases", "Existing CC infrastructure"],
      ],
      [2800, 3600, 2960]
    ),
    spacer(),

    h1("9. Demo vs. Production Roadmap"),
    table(
      ["Capability", "Current Demo", "Production Target"],
      [
        ["Knowledge source", "Synthetic JSON (3 products)", "PIM + FMEA + service manuals + field data"],
        ["Customer context", "Anonymous chat", "CRM-authenticated with asset registry"],
        ["Claims integration", "None", "Bidirectional claims system API"],
        ["Escalation store", "Local JSON file", "Salesforce Cases / ServiceNow"],
        ["LLM", "Optional, not wired", "Grok/OpenAI for NL polish + query expansion"],
        ["Symptom matching", "Lexical token overlap", "Embeddings + graph traversal hybrid"],
        ["Auth", "None", "SSO (OIDC/SAML)"],
      ],
      [2800, 3200, 3360]
    ),
    spacer(),

    h1("10. Prerequisites, Dependencies, Assumptions & Risk Mitigation"),
    h2("10.1 Prerequisites"),
    table(
      ["Requirement", "Minimum", "Notes"],
      [
        ["Python", "3.12+", "venv recommended; all application code"],
        ["Docker", "Running daemon", "Neo4j container neo4j-demo on 7474/7687"],
        ["Network ports", "7474, 7687, 8080, 8090, 8501 free", "Full enterprise demo binds all five"],
        ["Disk space", "~2 GB", "Neo4j image, venv, generated catalog/lineage"],
        ["LLM API key", "Not required", "Graph-native demo mode is default"],
        ["Node.js", "18+ (optional)", "Only for regenerating Word docs in docs/"],
      ],
      [2400, 2000, 4960]
    ),
    spacer(),
    p("First-time setup:"),
    codeBlock(
      "python -m venv venv && source venv/bin/activate\n" +
        "pip install -r requirements.txt\n" +
        "cp .env.example .env"
    ),

    h2("10.2 Dependencies"),
    table(
      ["Category", "Component", "Role", "Required?"],
      [
        ["Runtime", "Neo4j 5.x + neo4j Python driver", "Knowledge graph storage and Cypher queries", "Yes"],
        ["Runtime", "LangGraph + LangChain", "Agent workflow (detect → diagnose → format → escalate)", "Yes"],
        ["Runtime", "Pydantic / pydantic-settings", "Ontology validation and environment config", "Yes"],
        ["Runtime", "FastAPI + uvicorn", "Diagnostics REST API (:8080)", "Enterprise demo"],
        ["Runtime", "Streamlit", "Customer chat, agent dashboard, KG explorer", "Demo UI"],
        ["Runtime", "httpx", "CRM/PIM/Claims/FSM connector HTTP", "Enterprise path"],
        ["Infrastructure", "Docker (neo4j-demo)", "Local graph database", "Local dev"],
        ["Infrastructure", "Mock Enterprise APIs (:8090)", "Simulated CRM, PIM, FSM, Claims", "Default demo"],
        ["Optional", "XAI_API_KEY / OPENAI_API_KEY", "Future LLM-enhanced formatting", "No"],
      ],
      [1600, 2800, 3600, 1360]
    ),
    spacer(),

    h2("10.3 Assumptions"),
    bullet("bullets", "Demo knowledge covers three appliance families (wm-001, dw-001, mw-001) — not hundreds of production SKUs"),
    bullet("bullets", "USE_MOCK_ENTERPRISE_APIS=true by default; real connector URLs require authenticated implementations"),
    bullet("bullets", "Diagnosis is graph-native (Cypher + lexical matching); LLM is optional augmentation only"),
    bullet("bullets", "Single Neo4j instance serves both staging and runtime in the demo"),
    bullet("bullets", "Escalation fires at confidence < 65% or on any critical-severity matched symptom"),
    bullet("bullets", "Customer PII remains in CRM at runtime — not persisted in the knowledge graph"),
    bullet("bullets", "Escalation and case handoff use local JSON persistence in demo mode"),

    h2("10.4 Risk Mitigation"),
    table(
      ["Risk", "Likelihood", "Impact", "Mitigation"],
      [
        ["Unsafe repair guidance", "Medium", "Critical", "Safety notes on failure modes; critical symptoms force escalation"],
        ["Low-confidence misdiagnosis", "Medium", "High", "ESCALATION_CONFIDENCE_THRESHOLD; multi-symptom confidence dilution"],
        ["LLM hallucination (future)", "Medium", "High", "Graph truth layer unchanged; LLM formatting only"],
        ["Stale or corrupt knowledge", "Medium", "High", "ETL smoke validation gate; lineage audit in etl_batches.jsonl"],
        ["Invalid warranty handling", "Medium", "Medium", "CRM asset binding + warranty eligibility gate before diagnosis"],
        ["Integration outage", "Medium", "Medium", "Connector fixture fallback; health endpoints on mock and REST APIs"],
        ["Unexplainable agent output", "Low", "High", "provenance_trail and evidence[] on every DiagnosisResult"],
        ["PII leakage into graph", "Low", "Critical", "Neo4j holds product/diagnostic knowledge only; CRM enriches at runtime"],
      ],
      [2800, 1200, 1200, 4160]
    ),
    spacer(),

    h1("11. Conclusion"),
    p(
      "The Enterprise Diagnostics Chatbot demonstrates a production-viable pattern for warranty claims intelligent triage: structured knowledge in a graph database, explainable GraphRAG retrieval, deterministic agent orchestration, and selective escalation to human agents only when genuinely needed. The architecture is designed from the ground up for enterprise integration with CRM, claims, PIM, and contact center systems—ensuring that automated diagnosis reduces workload while improving outcomes for both customers and agents."
    ),
    p(
      "For detailed coverage of the knowledge graph ontology, Neo4j schema, GraphRAG query execution, and under-the-hood algorithms, refer to the companion document: Knowledge Graph, Ontology & GraphRAG Technical Deep Dive."
    ),
  ];

  return new Document({
    styles: docStyles,
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
                    text: "Enterprise Diagnostics Chatbot — Architecture & Solution Design",
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
        children,
      },
    ],
  });
}

function buildDoc2() {
  const children = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: "Knowledge Graph, Ontology & GraphRAG",
          bold: true,
          size: 48,
          color: "1F4E79",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [
        new TextRun({ text: "Technical Deep Dive — Under the Hood", size: 32, italics: true }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 },
      children: [new TextRun({ text: "Enterprise Diagnostics Chatbot Platform", size: 24 })],
    }),
    p("Document Version: 1.0"),
    p("Date: June 25, 2026"),
    p("Classification: Internal / Technical Architecture"),
    pageBreak(),

    h1("1. Introduction"),
    p(
      "This document provides exhaustive technical detail on how the Enterprise Diagnostics Chatbot builds, stores, queries, and reasons over its knowledge graph. It covers ontology design, Neo4j graph database schema, data ingestion pipelines, GraphRAG execution semantics, Cypher query patterns, confidence scoring, escalation logic, and the path from demo synthetic data to enterprise-scale knowledge base construction."
    ),
    p(
      "GraphRAG (Graph Retrieval-Augmented Generation) in this solution means: retrieve structured diagnostic evidence from a property graph database, assemble it into a typed result object, and optionally present it via natural language. The 'generation' layer is currently template-based (format_diagnosis_response); an LLM can be layered on top without changing the graph truth layer."
    ),

    h2("1.1 Prerequisites"),
    bullet("bullets", "Python 3.12+ with pip install -r requirements.txt"),
    bullet("bullets", "Neo4j 5.x reachable at bolt://localhost:7687 (Docker neo4j-demo container)"),
    bullet("bullets", "Knowledge catalog loaded via populate_graph.py or enterprise ETL orchestrator"),
    bullet("bullets", "Optional: mock enterprise APIs on :8090 for full provenance and CRM enrichment demos"),
    h2("1.2 Dependencies"),
    bullet("bullets", "neo4j driver — Bolt protocol sessions in graph/neo4j_client.py"),
    bullet("bullets", "Pydantic models — ontology contract in synthetic_data_generator.py and enterprise pipeline"),
    bullet("bullets", "LangGraph StateGraph — agents/diagnosis_graph.py workflow"),
    bullet("bullets", "Enterprise connectors — PIM, FSM, Claims, CRM under graph/enterprise_pipeline/connectors/"),
    h2("1.3 Assumptions"),
    bullet("bullets", "Ontology schema is stable; new products are instances, not schema changes"),
    bullet("bullets", "INDICATES confidence weights are SME-calibrated or empirically tuned from field data"),
    bullet("bullets", "Symptom descriptions in the graph are canonical; customer language is mapped via lexical overlap"),
    bullet("bullets", "MERGE keys (product_id, symptom_id, failure_mode_id) are globally unique across sources"),
    h2("1.4 Risk Mitigation"),
    bullet("bullets", "Schema constraints in populate_graph.py prevent orphan nodes on load"),
    bullet("bullets", "Smoke validation pipeline blocks promotion when regression scenarios fail"),
    bullet("bullets", "Provenance fields (source_system, batch_id) enable rollback of bad ETL batches"),
    bullet("bullets", "Escalation rules prevent automated responses on critical-severity symptoms"),

    h1("2. Ontology Design"),
    h2("2.1 What Is the Ontology?"),
    p(
      "The ontology is the formal schema defining what entities exist in the appliance diagnostic domain, what attributes they carry, and how they relate. It is the contract between knowledge engineering (who creates content), the graph database (who stores it), and the GraphRAG engine (who queries it)."
    ),
    p(
      "In the demo, the ontology is expressed as Pydantic models in graph/synthetic_data_generator.py. In enterprise deployment, the same conceptual ontology would be maintained in an OWL/RDF taxonomy or a graph schema registry, with ETL pipelines transforming source documents into graph instances."
    ),

    h2("2.2 Entity Types (Node Labels)"),
    table(
      ["Label", "Purpose", "Key Properties", "Example"],
      [
        ["Product", "Appliance model", "product_id, name, category, brand, model_year", "wm-001 Front Load Washing Machine"],
        ["Symptom", "Observable customer complaint", "symptom_id, description, severity", "wm-s01 Machine does not spin"],
        ["FailureMode", "Root cause hypothesis", "failure_mode_id, name, description, repair_minutes, safety_notes", "wm-fm01 Worn Drive Belt"],
        ["DiagnosticStep", "Troubleshooting procedure", "step_id, description, order, expected_outcome", "wm-d01 Run empty spin cycle"],
        ["Part", "Replacement component", "part_id, name, part_number, estimated_cost_usd", "AH-DB-8842 Drive Belt"],
        ["HistoricalResolution", "Past field service outcome", "resolution_id, description, resolution_date, technician_notes", "Replaced worn drive belt"],
      ],
      [1600, 2200, 2800, 2760]
    ),
    spacer(),

    h2("2.3 Relationship Types (Edge Labels)"),
    table(
      ["Relationship", "From → To", "Properties", "Semantic Meaning"],
      [
        ["HAS_SYMPTOM", "Product → Symptom", "(none)", "This product can exhibit this symptom"],
        ["CAN_HAVE", "Product → FailureMode", "(none)", "This product is susceptible to this failure"],
        ["INDICATES", "Symptom → FailureMode", "confidence (0.0–1.0)", "This symptom suggests this failure with given probability"],
        ["HAS_DIAGNOSTIC_STEP", "Product → DiagnosticStep", "(none)", "Ordered troubleshooting for this product"],
        ["FOR_PRODUCT", "HistoricalResolution → Product", "(none)", "Resolution occurred on this product"],
        ["CONFIRMED", "HistoricalResolution → FailureMode", "(none)", "Field service confirmed this root cause"],
      ],
      [2000, 2200, 1800, 3360]
    ),
    spacer(),

    h2("2.4 Ontology Diagram"),
    codeBlock(
      "                    ┌─────────────────┐\n" +
        "                    │     Product     │\n" +
        "                    └────────┬────────┘\n" +
        "           HAS_SYMPTOM        │        CAN_HAVE\n" +
        "                ┌─────────────┼─────────────┐\n" +
        "                ▼             │             ▼\n" +
        "         ┌──────────┐         │      ┌─────────────┐\n" +
        "         │ Symptom  │         │      │ FailureMode │\n" +
        "         └────┬─────┘         │      └──────▲──────┘\n" +
        "              │ INDICATES     │             │\n" +
        "              │ (confidence)  │      CONFIRMED\n" +
        "              └───────────────┼─────────────┘\n" +
        "                              │\n" +
        "                    HAS_DIAGNOSTIC_STEP\n" +
        "                              │\n" +
        "                              ▼\n" +
        "                    ┌─────────────────┐\n" +
        "                    │ DiagnosticStep  │\n" +
        "                    └─────────────────┘\n" +
        "\n" +
        "         ┌──────────────────────┐\n" +
        "         │ HistoricalResolution │──FOR_PRODUCT──▶ Product\n" +
        "         └──────────────────────┘"
    ),

    h2("2.5 Severity Taxonomy"),
    p("Symptoms carry a severity attribute used in escalation decisions:"),
    table(
      ["Severity", "Meaning", "Escalation Behavior", "Examples in Demo"],
      [
        ["low", "Minor inconvenience", "No automatic escalation", "Detergent dispenser does not open"],
        ["medium", "Functional degradation", "Confidence-based only", "Excessive vibration, grinding noise"],
        ["high", "Significant malfunction", "Confidence-based only", "Water in drum, door latch loose"],
        ["critical", "Safety hazard", "Mandatory escalation", "Microwave arcing, food stays cold (magnetron)"],
      ],
      [1600, 2800, 2800, 2160]
    ),
    spacer(),

    h2("2.6 Enterprise Ontology Extensions"),
    p("Production ontology extends the demo schema with enterprise entities:"),
    bullet("bullets", "Customer node: linked to CRM customer_id (not stored in Neo4j diagnosis graph; referenced via API)"),
    bullet("bullets", "WarrantyPolicy node: coverage terms, exclusions, regional rules"),
    bullet("bullets", "Claim node: claim_id, status, filing date (in claims system; cross-referenced)"),
    bullet("bullets", "Component node: sub-assembly hierarchy from BOM (motor → drive belt → drum)"),
    bullet("bullets", "ErrorCode node: manufacturer diagnostic codes linked to symptoms"),
    bullet("bullets", "TechnicianSkill node: certification requirements for failure mode repair"),
    bullet("bullets", "Region node: market-specific parts and regulatory safety requirements"),
    p(
      "The core diagnostic ontology (Product → Symptom → FailureMode → DiagnosticStep) remains stable; enterprise entities are layered via additional relationships without breaking the GraphRAG query patterns."
    ),

    h1("3. Knowledge Base Content"),
    h2("3.1 Demo Knowledge Catalog"),
    p(
      "The demo knowledge base covers three appliance products with fully interconnected diagnostic knowledge. Data is generated by graph/synthetic_data_generator.py and stored in data/synthetic_diagnosis_data.json before Neo4j ingestion."
    ),

    h3("3.1.1 Washing Machine (wm-001)"),
    p("Front Load Washing Machine 8kg — AquaHome, Laundry, 2023"),
    table(
      ["Entity Type", "Count", "IDs"],
      [
        ["Symptoms", "4", "wm-s01 (no spin), wm-s02 (vibration), wm-s03 (water in drum), wm-s04 (E21 error)"],
        ["Failure Modes", "3", "wm-fm01 (drive belt), wm-fm02 (drain pump), wm-fm03 (load sensor)"],
        ["Diagnostic Steps", "4", "wm-d01 through wm-d04 (spin test, belt inspect, pump test, suspension check)"],
        ["Parts", "3", "Drive belt, drain pump motor, shock absorber kit"],
        ["Historical Resolutions", "2", "Belt replacement (2025-11-12), pump replacement (2026-01-08)"],
        ["Symptom-Failure Links", "5", "Confidence range 0.55–0.92"],
      ],
      [2200, 1200, 5960]
    ),
    spacer(),
    p("Key INDICATES relationships:"),
    bullet("bullets", "wm-s01 → wm-fm01 (Worn Drive Belt) confidence 0.92"),
    bullet("bullets", "wm-s03 → wm-fm02 (Failed Drain Pump) confidence 0.88"),
    bullet("bullets", "wm-s02 → wm-fm03 (Unbalanced Load Sensor) confidence 0.85"),

    h3("3.1.2 Dishwasher (dw-001)"),
    p("Built-in Dishwasher 12 Place Setting — CleanWave, Kitchen, 2022"),
    table(
      ["Entity Type", "Count", "Notable Content"],
      [
        ["Symptoms", "4", "Wet/cold dishes, standing water, grinding noise, dispenser stuck"],
        ["Failure Modes", "3", "Heating element, clogged drain hose, wash impeller obstruction"],
        ["Diagnostic Steps", "4", "Temperature test, hose inspect, impeller check, solenoid test"],
        ["Parts", "3", "Heating element, drain hose kit, circulation pump"],
        ["Symptom-Failure Links", "4", "dw-s01→heating (0.90), dw-s03→impeller (0.91)"],
      ],
      [2200, 1200, 5960]
    ),
    spacer(),

    h3("3.1.3 Microwave (mw-001)"),
    p("Convection Microwave 25L — HeatPro, Kitchen, 2024"),
    table(
      ["Entity Type", "Count", "Notable Content"],
      [
        ["Symptoms", "4", "Food cold (CRITICAL), arcing (CRITICAL), fan failure, loose latch"],
        ["Failure Modes", "3", "Magnetron failure, waveguide cover damage, convection fan motor"],
        ["Safety Notes", "—", "HIGH VOLTAGE warnings on magnetron; arcing damage warnings"],
        ["Symptom-Failure Links", "4", "mw-s01→magnetron (0.94), mw-s02→waveguide (0.89)"],
      ],
      [2200, 1200, 5960]
    ),
    spacer(),

    h2("3.2 Enterprise Knowledge Base Construction"),
    p(
      "In enterprise deployment, the knowledge base is not hand-authored JSON. It is assembled from multiple authoritative sources through an ETL/ELT pipeline:"
    ),
    table(
      ["Source System", "Content Extracted", "Target Graph Entities"],
      [
        ["FMEA / Reliability Engineering", "Failure modes, effects, severity ratings", "FailureMode, INDICATES confidence seeds"],
        ["Service Manuals (PDF/HTML)", "Troubleshooting trees, test procedures", "DiagnosticStep nodes with ordering"],
        ["Call Center Knowledge Base", "Symptom descriptions, customer language variants", "Symptom nodes with synonym mappings"],
        ["Field Service Records", "Confirmed repairs, technician notes", "HistoricalResolution + CONFIRMED edges"],
        ["PIM / PLM", "Product catalog, model hierarchy, parts BOM", "Product, Part nodes"],
        ["IoT Error Code Registry", "Smart appliance fault codes", "ErrorCode → Symptom mappings"],
        ["Warranty Policy Documents", "Coverage rules, exclusions", "WarrantyPolicy (external or graph)"],
      ],
      [2800, 3200, 3360]
    ),
    spacer(),

    h2("3.3 Knowledge Engineering Workflow"),
    bullet("numbers", "SME workshops: reliability engineers + senior technicians define failure modes per product family"),
    bullet("numbers", "Symptom cataloging: contact center logs mined for natural language symptom clusters"),
    bullet("numbers", "Link calibration: symptom→failure confidence scores set from historical case data (Bayesian update)"),
    bullet("numbers", "Diagnostic step authoring: converted from service manual SOPs with expected outcomes"),
    bullet("numbers", "Validation: test cases run against GraphRAG engine (as in tests/test_diagnosis.py)"),
    bullet("numbers", "Publication: validated JSON/XML fed to populate_graph.py or enterprise ETL"),
    bullet("numbers", "Continuous improvement: new HistoricalResolution nodes from every closed field service ticket"),

    h1("4. Neo4j Graph Database"),
    h2("4.1 Why Neo4j?"),
    bullet("bullets", "Native graph traversal matches the diagnostic reasoning model (symptom → failure → step)"),
    bullet("bullets", "Cypher queries express multi-hop patterns concisely"),
    bullet("bullets", "Relationship properties (confidence on INDICATES) enable weighted reasoning"),
    bullet("bullets", "MERGE idempotency supports safe re-ingestion of updated knowledge"),
    bullet("bullets", "Neo4j Browser enables visual exploration (demo Knowledge Graph tab)"),
    bullet("bullets", "Production path: Neo4j AuraDB with read replicas for high query volume"),

    h2("4.2 Schema Constraints"),
    p("On population, unique constraints are created for every entity primary key (graph/populate_graph.py):"),
    codeBlock(
      "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE\n" +
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE\n" +
        "CREATE CONSTRAINT IF NOT EXISTS FOR (fm:FailureMode) REQUIRE fm.failure_mode_id IS UNIQUE\n" +
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ds:DiagnosticStep) REQUIRE ds.step_id IS UNIQUE\n" +
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Part) REQUIRE p.part_id IS UNIQUE\n" +
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:HistoricalResolution) REQUIRE r.resolution_id IS UNIQUE"
    ),

    h2("4.3 Population Algorithm"),
    p("populate_graph.py executes the following MERGE sequence per product in the catalog:"),
    bullet("numbers", "MERGE Product node with properties"),
    bullet("numbers", "For each symptom: MERGE Symptom node, MERGE (Product)-[:HAS_SYMPTOM]->(Symptom)"),
    bullet("numbers", "For each failure mode: MERGE FailureMode node, MERGE (Product)-[:CAN_HAVE]->(FailureMode)"),
    bullet("numbers", "For each diagnostic step: MERGE DiagnosticStep node, MERGE (Product)-[:HAS_DIAGNOSTIC_STEP]->(Step)"),
    bullet("numbers", "For each part: MERGE Part node (parts are product-scoped in JSON but globally merged by part_id)"),
    bullet("numbers", "For each symptom-failure link: MATCH nodes, MERGE (Symptom)-[:INDICATES {confidence}]->(FailureMode)"),
    bullet("numbers", "For each resolution: MERGE HistoricalResolution, link FOR_PRODUCT and CONFIRMED"),
    p(
      "MERGE ensures idempotent re-runs: updating the JSON catalog and re-running populate_graph.py updates properties without duplicating nodes."
    ),

    h2("4.4 Connection Management"),
    p(
      "graph/neo4j_client.py provides a cached driver singleton via @lru_cache on get_driver(). Configuration is loaded from config/settings.py (Pydantic Settings with .env support):"
    ),
    bullet("bullets", "NEO4J_URI: bolt://localhost:7687 (demo)"),
    bullet("bullets", "NEO4J_USER / NEO4J_PASSWORD: authentication credentials"),
    bullet("bullets", "verify_connection(): health check used by Streamlit UI and test suite"),

    h1("5. GraphRAG Engine — Under the Hood"),
    h2("5.1 DiagnosisResult Data Contract"),
    p(
      "The GraphRAG engine returns a typed DiagnosisResult dataclass (graph/graph_rag.py) containing all evidence needed for display, escalation, and enterprise handoff:"
    ),
    table(
      ["Field", "Type", "Description"],
      [
        ["product_id / product_name", "str", "Identified appliance"],
        ["matched_symptoms", "list[dict]", "Symptoms with match_score and severity"],
        ["ranked_failure_modes", "list[dict]", "Top 3 failure modes with confidence aggregates"],
        ["diagnostic_steps", "list[dict]", "Ordered troubleshooting procedures"],
        ["parts", "list[dict]", "Relevant replacement parts from JSON catalog"],
        ["historical_resolutions", "list[dict]", "Past confirmed repairs for top failure mode"],
        ["confidence", "float", "Aggregate confidence of top failure mode (0.0–1.0)"],
        ["should_escalate", "bool", "Escalation decision"],
        ["escalation_reason", "str", "Human-readable escalation justification"],
        ["evidence", "list[str]", "Explainability trail for UI and audit"],
      ],
      [2800, 2000, 4560]
    ),
    spacer(),

    h2("5.2 Full Diagnosis Pipeline (diagnose function)"),
    p("Step-by-step execution trace for diagnose(user_message, product_id=None):"),
    h3("Step 1: Product Resolution"),
    p("If product_id is provided (UI selection or CRM pre-bind), look up in list_products() Cypher query. Otherwise, call detect_product(user_message) which scores keyword hits:"),
    codeBlock(
      "keywords = {\n" +
        "  'wm-001': ['washing', 'washer', 'laundry', 'spin', 'drum'],\n" +
        "  'dw-001': ['dishwasher', 'dish', 'dishes', 'rinse'],\n" +
        "  'mw-001': ['microwave', 'convection', 'magnetron', 'arcing', 'spark']\n" +
        "}\n" +
        "# Highest keyword count wins; score must be > 0"
    ),
    p("If no product resolved: return DiagnosisResult with should_escalate=True, reason='Could not identify appliance type'."),

    h3("Step 2: Symptom Matching (match_symptoms)"),
    p("Cypher retrieves all symptoms for the product:"),
    codeBlock(
      "MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)\n" +
        "RETURN s.symptom_id, s.description, s.severity"
    ),
    p("For each symptom, compute lexical similarity between user_message and symptom description using:"),
    bullet("bullets", "Substring containment check (score 0.85 if either contains the other)"),
    bullet("bullets", "Token overlap: tokenize both strings, expand via SYNONYMS map, compute |A∩B| / |B|"),
    bullet("bullets", "Threshold: score >= 0.15 to qualify as a match"),
    bullet("bullets", "Fallback: if no matches, take top 2 symptoms with score 0.1 (ensures some failure ranking)"),
    bullet("bullets", "Return top 4 matches sorted by score descending"),
    p("Synonym expansion examples: 'spin' expands to {spin, spins, spinning, rotate, rotation}; 'arcing' expands to {arcing, spark, sparking, sparks}."),

    h3("Step 3: Failure Mode Ranking (rank_failure_modes)"),
    p("This is the core graph reasoning step. Given matched symptom_ids, Cypher traverses INDICATES relationships:"),
    codeBlock(
      "MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)\n" +
        "OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\n" +
        "WHERE s.symptom_id IN $symptom_ids\n" +
        "WITH fm,\n" +
        "     collect(DISTINCT {symptom_id: s.symptom_id, confidence: ind.confidence}) AS indications,\n" +
        "     sum(CASE WHEN ind.confidence IS NULL THEN 0 ELSE ind.confidence END) AS total_confidence,\n" +
        "     count(ind) AS link_count\n" +
        "RETURN fm.*, indications, total_confidence, link_count\n" +
        "ORDER BY total_confidence DESC, link_count DESC"
    ),
    p("Post-query, aggregate_confidence = total_confidence / max(len(symptom_ids), 1). This normalizes when multiple symptoms match, preventing inflation from symptom count alone."),

    h3("Step 4: Confidence & Escalation Decision"),
    codeBlock(
      "confidence = top_failure_mode.aggregate_confidence\n" +
        "critical = any(symptom.severity == 'critical' for symptom in matched_symptoms)\n" +
        "should_escalate = critical OR confidence < ESCALATION_CONFIDENCE_THRESHOLD (0.65)"
    ),

    h3("Step 5: Evidence Retrieval"),
    bullet("bullets", "get_diagnostic_steps(product_id): all steps ordered by step.order"),
    bullet("bullets", "get_parts_for_product(product_id): loaded from JSON catalog (enterprise: Cypher or PIM API)"),
    bullet("bullets", "get_historical_resolutions(product_id, top_failure_mode_id): past repairs confirming the hypothesis"),
    bullet("bullets", "evidence[] assembled: top failure mode name + confidence, top 3 symptom matches with severity"),

    h3("Step 6: Response Formatting"),
    p(
      "format_diagnosis_response() generates markdown with sections: Product, Matched Symptoms, Most Likely Failure Mode (with safety notes), Recommended Diagnostic Steps, Similar Past Resolutions, Escalation Status, and Graph Evidence. This is returned to the customer via the LangGraph format_response node."
    ),

    h2("5.3 Example Trace"),
    p("Input: 'My washing machine won't spin and water stays in the drum'"),
    table(
      ["Step", "Result"],
      [
        ["Product detection", "wm-001 (keywords: washing, spin, drum)"],
        ["Symptom matches", "wm-s01 (no spin, score~0.85), wm-s03 (water in drum, score~0.85)"],
        ["Failure ranking", "wm-fm01 Drive Belt (agg conf 0.92), wm-fm02 Drain Pump (0.88)"],
        ["Top confidence", "0.92"],
        ["Critical symptoms", "None"],
        ["Escalation", "No (0.92 > 0.65 threshold)"],
        ["Steps returned", "4 washing machine diagnostic procedures"],
        ["Historical match", "wm-r01: Replaced worn drive belt (2025-11-12)"],
      ],
      [2800, 6560]
    ),
    spacer(),

    h2("5.4 Agent Tool Layer"),
    p("agents/tools.py wraps GraphRAG functions for LangGraph consumption:"),
    bullet("bullets", "tool_detect_product(message) → product dict or None"),
    bullet("bullets", "tool_diagnose(message, product_id) → full diagnosis dict including formatted_response"),
    bullet("bullets", "tool_get_steps(product_id) → diagnostic steps list"),
    bullet("bullets", "tool_rank_failures(product_id, symptom_ids) → ranked failure modes"),
    p(
      "tool_diagnose serializes DiagnosisResult into a JSON-compatible dict that becomes the escalation payload stored by utils/escalation_store.py."
    ),

    h1("6. Escalation & Human Agent Payload"),
    h2("6.1 Escalation Store Schema"),
    p("When should_escalate is true, save_escalation() writes:"),
    codeBlock(
      "{\n" +
        "  'case_id': 'uuid-8chars',\n" +
        "  'created_at': 'ISO-8601 UTC',\n" +
        "  'status': 'open | in_progress | resolved | closed',\n" +
        "  'user_message': 'customer verbatim input',\n" +
        "  'diagnosis': { full tool_diagnose payload }\n" +
        "}"
    ),

    h2("6.2 What the Human Agent Sees"),
    p("The Human Agent Dashboard (ui/app.py tab 2) displays for each escalated case:"),
    bullet("bullets", "Customer message (verbatim)"),
    bullet("bullets", "Product name and identification"),
    bullet("bullets", "Escalation reason (critical symptom or low confidence)"),
    bullet("bullets", "Confidence percentage"),
    bullet("bullets", "Top failure mode with safety notes"),
    bullet("bullets", "Full JSON diagnostic payload (expandable)"),
    bullet("bullets", "Status management buttons: In Progress, Resolve, Close"),
    p(
      "In enterprise deployment, this payload is augmented with CRM customer profile, warranty eligibility, registered serial number, and claim draft ID before presentation to the contact center agent."
    ),

    h1("7. Enterprise Data Integration for Knowledge Graph"),
    h2("7.1 Multi-System Data Flow"),
    codeBlock(
      "┌─────────────┐     ┌──────────────┐     ┌────────────────┐\n" +
        "│ PIM / PLM   │────▶│ Knowledge    │────▶│ Neo4j Graph    │\n" +
        "│ FMEA        │     │ ETL Pipeline │     │ (Ontology      │\n" +
        "│ Svc Manuals │     │              │     │  Instances)    │\n" +
        "│ Field Data  │     └──────────────┘     └───────┬────────┘\n" +
        "└─────────────┘                                   │\n" +
        "                                                    ▼\n" +
        "┌─────────────┐     ┌──────────────┐     ┌────────────────┐\n" +
        "│ CRM         │────▶│ Session      │────▶│ GraphRAG       │\n" +
        "│ Claims      │     │ Context API  │     │ diagnose()     │\n" +
        "│ IoT         │     └──────────────┘     └───────┬────────┘\n" +
        "└─────────────┘                                   │\n" +
        "                                                    ▼\n" +
        "                                          ┌────────────────┐\n" +
        "                                          │ Contact Center │\n" +
        "                                          │ (escalations)  │\n" +
        "                                          └────────────────┘"
    ),

    h2("7.2 CRM Enrichment Points"),
    table(
      ["Integration Point", "When", "GraphRAG Impact"],
      [
        ["Asset lookup", "Session start", "Pre-bind product_id; skip detect_product"],
        ["Warranty check", "Before diagnosis", "Gate ineligible claims before graph query"],
        ["Customer history", "Before diagnosis", "Inject prior resolutions into context"],
        ["Case creation", "On escalation", "Push diagnostic dossier to CRM case"],
      ],
      [2800, 2400, 4160]
    ),
    spacer(),

    h2("7.3 Claims System Integration Points"),
    table(
      ["Integration Point", "When", "Action"],
      [
        ["Eligibility API", "Pre-diagnosis", "Block or route based on warranty status"],
        ["Draft claim", "On escalation", "Create claim with failure mode pre-populated"],
        ["Self-service log", "No escalation", "Record deflected contact for analytics"],
        ["Resolution sync", "Agent closes case", "Update claim; feed HistoricalResolution to graph ETL"],
      ],
      [2800, 2400, 4160]
    ),
    spacer(),

    h2("7.4 Feedback Loop — Closing the Knowledge Graph"),
    p(
      "Every agent-resolved or field-service-confirmed case becomes a new HistoricalResolution node. The confirmed failure mode strengthens the graph:"
    ),
    bullet("numbers", "Agent confirms 'Worn Drive Belt' on wm-001 case"),
    bullet("numbers", "Claims system closes claim with failure_mode_id = wm-fm01"),
    bullet("numbers", "Nightly ETL creates HistoricalResolution node with technician notes"),
    bullet("numbers", "CONFIRMED edge linked to wm-fm01"),
    bullet("numbers", "Optional: INDICATES confidence for matched symptoms incremented via Bayesian update"),
    p(
      "Over time, the knowledge graph becomes a living repository of diagnostic intelligence derived from real warranty claim outcomes."
    ),

    h1("8. Query Reference & Neo4j Browser"),
    h2("8.1 Useful Cypher Queries"),
    p("Explore symptom-failure mappings:"),
    codeBlock(
      "MATCH (s:Symptom)-[r:INDICATES]->(fm:FailureMode)\n" +
        "RETURN s.description, fm.name, r.confidence\n" +
        "ORDER BY r.confidence DESC"
    ),
    p("Full product diagnostic tree:"),
    codeBlock(
      "MATCH (p:Product {product_id: 'wm-001'})-[:HAS_SYMPTOM]->(s:Symptom)\n" +
        "OPTIONAL MATCH (s)-[ind:INDICATES]->(fm:FailureMode)\n" +
        "RETURN p.name, s.description, fm.name, ind.confidence"
    ),
    p("Historical resolutions with confirmed failure modes:"),
    codeBlock(
      "MATCH (r:HistoricalResolution)-[:CONFIRMED]->(fm:FailureMode)\n" +
        "MATCH (r)-[:FOR_PRODUCT]->(p:Product)\n" +
        "RETURN p.name, r.description, fm.name, r.resolution_date\n" +
        "ORDER BY r.resolution_date DESC"
    ),

    h2("8.2 Evaluation Test Suite"),
    p("tests/test_diagnosis.py validates three canonical scenarios against Neo4j:"),
    table(
      ["Test Message", "Expected Product", "Min Confidence"],
      [
        ["Washing machine won't spin, water in drum", "wm-001", "0.30"],
        ["Dishwasher leaves dishes wet and cold", "dw-001", "0.40"],
        ["Microwave cold food with arcing", "mw-001", "0.40"],
      ],
      [4560, 2400, 2400]
    ),
    spacer(),

    h1("9. Future Enhancements"),
    h2("9.1 LLM-Augmented GraphRAG"),
    p("Optional XAI_API_KEY / OPENAI_API_KEY (config/settings.py) enables:"),
    bullet("bullets", "Natural language paraphrasing of graph evidence (not replacing it)"),
    bullet("bullets", "Multi-turn clarification questions when confidence is borderline"),
    bullet("bullets", "Cypher query generation from natural language (GraphCypherQAChain pattern)"),
    bullet("bullets", "Symptom extraction from unstructured customer messages via NER"),

    h2("9.2 Hybrid Vector + Graph Retrieval"),
    bullet("bullets", "Embed symptom descriptions and customer messages in vector space"),
    bullet("bullets", "Use vector similarity for initial symptom candidate retrieval"),
    bullet("bullets", "Use graph traversal for failure mode ranking and evidence assembly"),
    bullet("bullets", "Store embeddings in Neo4j vector index (Neo4j 5.11+) or external vector DB"),

    h2("9.3 Multi-Product Enterprise Scale"),
    bullet("bullets", "Partition graph by product category with shared symptom/failure ontologies"),
    bullet("bullets", "Version knowledge graph snapshots for audit (what diagnosis rules applied on date X)"),
    bullet("bullets", "A/B test confidence thresholds and escalation rules per market segment"),

    h1("10. Summary"),
    p(
      "The Enterprise Diagnostics Chatbot knowledge layer is a carefully designed property graph ontology instantiated in Neo4j, populated through validated ETL pipelines, and queried by a deterministic GraphRAG engine that performs product detection, lexical symptom matching, confidence-weighted failure mode ranking, and evidence assembly. Escalation rules ensure safety-critical and ambiguous cases reach human agents with a complete diagnostic dossier—while self-service-eligible cases are resolved at the automated tier."
    ),
    p(
      "In the enterprise warranty scenario, this knowledge graph is fed by PIM, FMEA, service manuals, and field service data; enriched at query time with CRM and claims context; and continuously improved through a feedback loop from confirmed resolutions. The result is an explainable, auditable, and integration-ready intelligent triage platform that reduces contact center workload while improving customer outcomes."
    ),
  ];

  return new Document({
    styles: docStyles,
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
                    text: "Knowledge Graph, Ontology & GraphRAG — Technical Deep Dive",
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
        children,
      },
    ],
  });
}

function buildDoc3() {
  const children = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: "Complete Beginner's Guide",
          bold: true,
          size: 48,
          color: "1F4E79",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [
        new TextRun({
          text: "GraphRAG, Knowledge Graphs & Enterprise Warranty Diagnosis",
          size: 30,
          italics: true,
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 },
      children: [
        new TextRun({
          text: "Everything Under the Hood — Explained from First Principles",
          size: 24,
        }),
      ],
    }),
    p("Document Version: 1.0"),
    p("Date: June 25, 2026"),
    p("Audience: New to GraphRAG, knowledge graphs, and enterprise AI systems"),
    pageBreak(),

    h1("1. Who This Document Is For"),
    p(
      "If you are completely new to GraphRAG, knowledge graphs, Neo4j, ontologies, or LangGraph — this document is written for you. It assumes no prior background. By the end, you should understand: what problem this application solves, what each technology does and why it exists, how data flows from enterprise systems into a knowledge graph, how a customer message becomes a diagnosis, and how automation scripts can build the entire ontology without manual coding."
    ),
    p("Companion documents (for deeper technical detail):"),
    bullet("bullets", "01-Architecture-and-Solution-Design.docx — solution architecture and enterprise integration"),
    bullet("bullets", "02-Knowledge-Graph-Ontology-and-GraphRAG-Deep-Dive.docx — Cypher queries, schema, algorithms"),

    h2("1.1 Prerequisites"),
    p("You can run and understand this demo with the following in place:"),
    table(
      ["Requirement", "Details"],
      [
        ["Python 3.12+", "Create venv, pip install -r requirements.txt"],
        ["Docker", "Runs Neo4j as neo4j-demo on ports 7474 (Browser) and 7687 (Bolt)"],
        ["Free local ports", "8501 Streamlit, 8080 REST API, 8090 mock enterprise APIs (full demo)"],
        ["Basic terminal skills", "Run ./run_demo.sh or ./run_enterprise_demo.sh"],
        ["LLM API key", "Not required — all diagnosis is graph-native"],
      ],
      [2800, 6560]
    ),
    spacer(),
    h2("1.2 Assumptions"),
    bullet("bullets", "You are evaluating or learning a warranty-triage pattern — not deploying to production from this repo alone"),
    bullet("bullets", "Enterprise data in data/enterprise_sources/ represents realistic CRM, PIM, FSM, and Claims payloads"),
    bullet("bullets", "Three products (washer, dishwasher, microwave) are sufficient to demonstrate the architecture"),
    bullet("bullets", "Escalation to human agents is expected and desirable for safety-critical or ambiguous cases"),
    bullet("bullets", "An LLM may polish language later but must not replace graph-backed reasoning"),

    h1("2. The Problem in Plain English"),
    p(
      "Imagine you run a company that sells washing machines, dishwashers, and microwaves. Thousands of customers call or chat every week saying things like: 'My washer won't spin' or 'My microwave sparks inside.'"
    ),
    p("Today, without this application:"),
    bullet("bullets", "Every customer talks to a human agent — expensive and slow"),
    bullet("bullets", "Agents ask the same basic questions repeatedly"),
    bullet("bullets", "Many calls are not real warranty issues (user error, expired warranty, simple fix)"),
    bullet("bullets", "Dangerous issues (electrical arcing) may not be prioritized correctly"),
    bullet("bullets", "Agents start from zero — no pre-built diagnosis when the call begins"),
    p(
      "This application acts as an intelligent first line: it understands the problem, looks up structured repair knowledge, suggests troubleshooting steps, and only sends genuinely complex or dangerous cases to human agents — with a full diagnostic report already prepared."
    ),

    h1("3. Glossary — Every Term Explained"),
    table(
      ["Term", "Simple Explanation", "In This App"],
      [
        ["Knowledge Graph", "A database of things (nodes) and how they connect (relationships), like a mind map", "Products linked to Symptoms linked to Failure Modes"],
        ["Graph Database (Neo4j)", "A database built specifically to store and query connected data", "Stores all diagnostic knowledge"],
        ["Ontology", "The official dictionary of what types of things exist and how they relate", "Product, Symptom, FailureMode, DiagnosticStep, etc."],
        ["Node", "One thing in the graph (a dot)", "e.g. a Symptom: 'Machine does not spin'"],
        ["Relationship / Edge", "A link between two nodes (an arrow)", "e.g. Symptom —INDICATES→ Failure Mode"],
        ["RAG", "Retrieval-Augmented Generation: fetch facts first, then generate an answer", "General AI pattern"],
        ["GraphRAG", "RAG that retrieves from a knowledge graph (structured connections), not just text chunks", "Our diagnosis engine in graph/graph_rag.py"],
        ["LangGraph", "A framework to chain AI/agent steps in a defined workflow", "detect → diagnose → format → escalate"],
        ["LLM", "Large Language Model (ChatGPT, Grok, etc.) — generates human-like text", "Optional in this demo; not required"],
        ["Confidence Score", "How sure the system is about a diagnosis (0% to 100%)", "Comes from INDICATES link weights in the graph"],
        ["Escalation", "Handing a case to a human agent", "Triggered by critical symptoms or low confidence"],
        ["ETL Pipeline", "Extract, Transform, Load — pull data from sources, reshape it, store it", "graph/enterprise_pipeline/pipeline.py"],
        ["CRM", "Customer Relationship Management — who owns which appliance", "Salesforce, SAP C4C, etc."],
        ["Claims System", "Warranty claim filing and tracking", "Guidewire, legacy mainframe systems"],
        ["PIM / PLM", "Product Information Management — models, parts, manuals", "SAP PLM, Windchill, etc."],
        ["FSM", "Field Service Management — technician visits and repairs", "ServiceMax, Salesforce Field Service"],
      ],
      [2000, 3800, 3560]
    ),
    spacer(),

    h1("4. Why Not Just Use ChatGPT?"),
    p(
      "A common question: why build a knowledge graph and GraphRAG instead of asking an LLM directly? Three reasons:"
    ),
    h2("4.1 Hallucination Risk"),
    p(
      "An LLM might invent a failure mode or recommend unsafe repair steps. In warranty and appliance repair, wrong advice can cause injury, void warranties, or create legal liability. This application grounds every answer in explicit graph data with traceable evidence."
    ),
    h2("4.2 Explainability"),
    p(
      "When a case escalates, the human agent sees exactly why: which symptoms matched, which failure mode ranked highest, what confidence score was computed, and which historical repairs support the conclusion. A black-box LLM cannot provide this audit trail as reliably."
    ),
    h2("4.3 Enterprise Data Integration"),
    p(
      "Real warranty diagnosis requires knowing the customer's registered product, warranty status, and past claims. Structured graphs and APIs integrate cleanly with CRM and claims systems. Pure LLM chat has no native connection to these systems."
    ),
    p(
      "Best practice: use the graph for truth and reasoning; optionally use an LLM only to make the response sound more conversational (future enhancement)."
    ),

    h1("5. The Big Picture — How All Pieces Fit Together"),
    codeBlock(
      "PHASE A: BUILD THE KNOWLEDGE (done once, updated regularly)\n" +
        "  Enterprise Systems (PIM, FSM, Claims, CRM)\n" +
        "       ↓  [enterprise_pipeline.py — automated ETL script]\n" +
        "  Ontology JSON catalog (validated data contract)\n" +
        "       ↓  [populate_graph.py]\n" +
        "  Neo4j Knowledge Graph (living database)\n" +
        "\n" +
        "PHASE B: RUN DIAGNOSIS (every customer message)\n" +
        "  Customer describes problem in chat\n" +
        "       ↓  [LangGraph agent in agents/diagnosis_graph.py]\n" +
        "  GraphRAG queries Neo4j [graph/graph_rag.py]\n" +
        "       ↓\n" +
        "  DiagnosisResult (symptoms, failure modes, steps, confidence)\n" +
        "       ↓\n" +
        "  If safe + confident → customer gets self-service steps\n" +
        "  If critical or uncertain → escalate to human agent with full dossier"
    ),

    h1("6. The Knowledge Graph — Explained with an Analogy"),
    p(
      "Think of the knowledge graph like a subway map for appliance repair:"
    ),
    bullet("bullets", "Stations = nodes (Product, Symptom, FailureMode, DiagnosticStep)"),
    bullet("bullets", "Lines between stations = relationships (HAS_SYMPTOM, INDICATES, CAN_HAVE)"),
    bullet("bullets", "Line thickness or labels = confidence (how strongly a symptom suggests a failure)"),
    bullet("bullets", "Trip planning = GraphRAG (given where you are — customer symptoms — find the best destination — failure mode)"),
    p("Example path for 'washer won't spin':"),
    codeBlock(
      "Product: Front Load Washing Machine\n" +
        "   → HAS_SYMPTOM → 'Machine does not spin' (severity: high)\n" +
        "       → INDICATES (confidence 0.92) → 'Worn Drive Belt'\n" +
        "   → HAS_DIAGNOSTIC_STEP → 'Inspect drive belt through rear panel'\n" +
        "   → HistoricalResolution → 'Replaced belt on 2025-11-12 — spin restored'"
    ),
    p(
      "Neo4j is the software that stores this map and answers questions like: 'Given these symptoms, which failure modes are most likely for this product?'"
    ),

    h1("7. What Is an Ontology?"),
    p(
      "An ontology is the blueprint of your knowledge. Before you store any data, you decide:"
    ),
    bullet("bullets", "What types of things exist? (Product, Symptom, FailureMode...)"),
    bullet("bullets", "What properties does each type have? (severity, confidence, part_number...)"),
    bullet("bullets", "What relationships are allowed? (Symptom can INDICATE FailureMode, but not the reverse)"),
    p(
      "In this demo, the ontology is defined as Pydantic Python models in graph/synthetic_data_generator.py. Knowledge engineers and reliability experts agree on this schema before any data is loaded. The ontology ensures every data source (PIM, FSM, manuals) maps to the same structure."
    ),
    p("Why it matters for enterprise:"),
    bullet("bullets", "Without an ontology, CRM product data and service manual data cannot be merged"),
    bullet("bullets", "The GraphRAG engine only works if data follows the agreed schema"),
    bullet("bullets", "New products are onboarded by adding instances that fit the existing ontology — not by rewriting code"),

    h1("8. What Is GraphRAG? (Step by Step)"),
    p(
      "GraphRAG = Graph Retrieval-Augmented Generation. Break it down:"
    ),
    h2("8.1 Retrieval"),
    p("Pull relevant facts from the knowledge graph using structured queries (Cypher in Neo4j). Not guessing — querying."),
    h2("8.2 Augmented"),
    p("The retrieved facts augment (enrich) the response. The answer is built on real data, not model memory."),
    h2("8.3 Generation"),
    p("Present the facts in human-readable form. In the demo, this is template-based markdown. With an LLM enabled, it could be natural conversational prose — but the facts still come from the graph."),
    h2("8.4 The Six Steps Inside graph/graph_rag.py"),
    bullet("numbers", "detect_product — figure out which appliance (washing machine, dishwasher, microwave)"),
    bullet("numbers", "match_symptoms — compare customer words to known symptom descriptions"),
    bullet("numbers", "rank_failure_modes — query Neo4j: which root causes best explain these symptoms?"),
    bullet("numbers", "get_diagnostic_steps — fetch ordered troubleshooting procedures"),
    bullet("numbers", "get_historical_resolutions — fetch similar past repairs for evidence"),
    bullet("numbers", "decide escalation — critical symptom or confidence below 65%? → human agent"),

    h1("9. Walkthrough: One Customer Message End-to-End"),
    p("Customer types: 'My washing machine won't spin and water stays in the drum'"),
    table(
      ["Step", "Component", "What Happens", "Result"],
      [
        ["1", "Streamlit UI (ui/app.py)", "Message captured, sent to LangGraph", "user_message stored"],
        ["2", "detect_product node", "Keywords 'washing', 'spin', 'drum' matched", "product_id = wm-001"],
        ["3", "match_symptoms", "Token overlap vs graph symptoms", "wm-s01 (no spin), wm-s03 (water in drum)"],
        ["4", "rank_failure_modes", "Cypher sums INDICATES confidence", "Drive Belt 0.92, Drain Pump 0.88"],
        ["5", "Confidence check", "0.92 > 0.65 threshold, no critical severity", "should_escalate = false"],
        ["6", "format_response", "Markdown built with steps + evidence", "Customer sees diagnosis"],
        ["7", "handle_escalation", "No escalation needed", "Case not sent to agent dashboard"],
      ],
      [800, 2200, 3600, 2760]
    ),
    spacer(),
    p(
      "Contrast with microwave arcing: symptoms mw-s01 and mw-s02 have severity=critical → escalation is mandatory even if confidence is high. Safety always wins."
    ),

    h1("10. Every Dependency Explained"),
    table(
      ["Dependency", "What It Is", "Why We Need It", "Required?"],
      [
        ["Python 3.12", "Programming language", "Runs all application code", "Yes"],
        ["Neo4j", "Graph database", "Stores and queries the knowledge graph", "Yes"],
        ["neo4j Python driver", "Database connector", "Python talks to Neo4j via Bolt protocol", "Yes"],
        ["Pydantic", "Data validation library", "Validates ontology JSON structure", "Yes"],
        ["LangGraph", "Agent workflow framework", "Chains diagnosis steps with typed state", "Yes"],
        ["Streamlit", "Web UI framework", "Customer chat + agent dashboard (demo)", "Demo only"],
        ["Docker", "Container runtime", "Runs Neo4j locally (neo4j-demo container)", "Local dev"],
        ["LangChain", "LLM toolkit", "Future LLM integration; listed in requirements", "Optional"],
        ["pandas", "Data analysis", "Future analytics on claims data", "Optional"],
        ["LLM API key", "External AI service", "Natural language polish", "Optional"],
      ],
      [1800, 2200, 3600, 1760]
    ),
    spacer(),

    h1("11. Project Files — What Each One Does"),
    table(
      ["File", "Purpose (Plain English)"],
      [
        ["graph/synthetic_data_generator.py", "Creates demo knowledge data with correct schema (enterprise uses pipeline instead)"],
        ["graph/enterprise_pipeline/pipeline.py", "AUTOMATION SCRIPT: fetches from CRM/Claims/PIM/FSM, builds ontology, loads Neo4j"],
        ["graph/enterprise_pipeline/connectors/*.py", "Adapters that pull data from each enterprise system (fixture or live API)"],
        ["graph/enterprise_pipeline/transformers/ontology_builder.py", "Merges all source data into one validated knowledge catalog"],
        ["graph/populate_graph.py", "Writes ontology JSON into Neo4j as nodes and relationships"],
        ["graph/graph_rag.py", "THE BRAIN: queries graph, matches symptoms, ranks failures, decides escalation"],
        ["graph/neo4j_client.py", "Opens connection to Neo4j database"],
        ["agents/diagnosis_graph.py", "Orchestrates the 4-step agent workflow"],
        ["agents/tools.py", "Bridge between LangGraph and GraphRAG functions"],
        ["ui/app.py", "Web interface: customer chat, agent dashboard, graph explorer"],
        ["utils/escalation_store.py", "Saves escalated cases for human agents to review"],
        ["config/settings.py", "All configuration: Neo4j URL, API endpoints, thresholds"],
        ["data/enterprise_sources/*.json", "Mock enterprise data (stand-in for real CRM/Claims/PIM/FSM APIs)"],
        ["run_demo.sh", "One-command launcher: generate data, start Neo4j, populate graph, run UI"],
      ],
      [3600, 5760]
    ),
    spacer(),

    h1("12. Enterprise Scenario — Why Multiple Systems?"),
    p(
      "No single enterprise system has all the knowledge needed for diagnosis. Each system owns a different slice:"
    ),
    h2("12.1 PIM / PLM — What Products Exist and How They Break"),
    bullet("bullets", "Product catalog: model numbers, brands, categories"),
    bullet("bullets", "FMEA data: engineering analysis of how products fail"),
    bullet("bullets", "Service manuals: official troubleshooting procedures"),
    bullet("bullets", "Parts BOM: which replacement parts exist and their part numbers"),
    p("Feeds into graph: Product, FailureMode, DiagnosticStep, Part, Symptom-Failure links"),

    h2("12.2 FSM — What Technicians Actually Fixed in the Field"),
    bullet("bullets", "Closed work orders with confirmed root cause"),
    bullet("bullets", "Technician notes: real-world repair context"),
    bullet("bullets", "Repair dates and outcomes"),
    p("Feeds into graph: HistoricalResolution nodes, confidence tuning on INDICATES links"),

    h2("12.3 Claims System — Warranty Outcomes and Policy"),
    bullet("bullets", "Which claims were approved or denied and why"),
    bullet("bullets", "Confirmed failure modes from closed claims"),
    bullet("bullets", "Warranty policy rules (coverage period, exclusions)"),
    p("Feeds into graph: HistoricalResolution nodes; runtime: eligibility gating before diagnosis"),

    h2("12.4 CRM — Who Owns What Appliance"),
    bullet("bullets", "Customer identity and contact details"),
    bullet("bullets", "Registered products with serial numbers and purchase dates"),
    bullet("bullets", "Warranty status per asset"),
    bullet("bullets", "Prior case history"),
    p("Used at runtime (not stored in Neo4j): pre-selects product, enriches escalation dossier with owner details"),

    h2("12.5 Contact Center — Where Escalations Land"),
    p(
      "Only genuine cases arrive here. The agent receives: customer name, registered appliance, serial number, warranty status, customer verbatim message, matched symptoms, top failure modes, safety warnings, steps already tried, and similar past resolutions. The agent starts informed — not from scratch."
    ),

    h1("13. The Automation Script — Building the Ontology Automatically"),
    p(
      "Yes — a script can and should automate fetching data from enterprise systems and building the ontology. This is implemented in:"
    ),
    codeBlock("graph/enterprise_pipeline/pipeline.py"),
    h2("13.1 What the Script Does"),
    bullet("numbers", "FETCH: Pull records from PIM, FSM, Claims, and CRM connectors"),
    bullet("numbers", "TRANSFORM: OntologyBuilder merges sources into validated ProductKnowledge objects"),
    bullet("numbers", "VALIDATE: Pydantic models reject malformed data before it enters the graph"),
    bullet("numbers", "WRITE: Save to data/enterprise_knowledge_catalog.json and data/synthetic_diagnosis_data.json"),
    bullet("numbers", "LOAD (optional): populate_graph.py loads nodes and relationships into Neo4j"),

    h2("13.2 How to Run It"),
    codeBlock(
      "# Fetch + transform + write catalog JSON\n" +
        "python -m graph.enterprise_pipeline.pipeline\n" +
        "\n" +
        "# Also load into Neo4j\n" +
        "python -m graph.enterprise_pipeline.pipeline --load-neo4j\n" +
        "\n" +
        "# Preview without writing files\n" +
        "python -m graph.enterprise_pipeline.pipeline --dry-run"
    ),

    h2("13.3 Connector Architecture"),
    p("Each enterprise system has a connector class implementing the same interface:"),
    codeBlock(
      "class EnterpriseConnector:\n" +
        "    def fetch(self) -> ConnectorResult  # returns normalized records\n" +
        "    def health_check(self) -> bool"
    ),
    p("Connectors in this project:"),
    bullet("bullets", "PIMConnector — products, FMEA, SOPs, parts (data/enterprise_sources/pim_catalog.json)"),
    bullet("bullets", "FSMConnector — closed technician work orders (fsm_work_orders.json)"),
    bullet("bullets", "ClaimsConnector — closed warranty claims (claims_history.json)"),
    bullet("bullets", "CRMConnector — registered customer assets (crm_assets.json)"),
    p(
      "In demo mode, connectors read local JSON fixtures that simulate real API responses. In production, you set API URLs in .env and implement the HTTP calls inside each connector's fetch() method."
    ),

    h2("13.4 Connecting Real Enterprise APIs"),
    p("Add to .env:"),
    codeBlock(
      "CRM_API_URL=https://your-org.salesforce.com/services/data/v59.0\n" +
        "CLAIMS_API_URL=https://claims.your-org.com/api/v1\n" +
        "PIM_API_URL=https://pim.your-org.com/api\n" +
        "FSM_API_URL=https://fsm.your-org.com/api/v2"
    ),
    p("Then replace the fixture logic in each connector with authenticated HTTP requests. The OntologyBuilder and populate_graph.py remain unchanged — only the data source changes."),

    h2("13.5 What the OntologyBuilder Merges"),
    bullet("bullets", "PIM provides the base: products, symptoms, failure modes, steps, parts, initial confidence links"),
    bullet("bullets", "FSM adds new HistoricalResolution records from field repairs"),
    bullet("bullets", "Claims adds resolution records and can boost INDICATES confidence for confirmed patterns"),
    bullet("bullets", "CRM is used at chat runtime to bind customer context (not baked into the static graph)"),

    h2("13.6 Scheduling in Production"),
    p("Run the pipeline on a schedule to keep the knowledge graph current:"),
    bullet("bullets", "Nightly full refresh from PIM and FSM"),
    bullet("bullets", "Hourly incremental sync for new closed claims and work orders"),
    bullet("bullets", "On-demand refresh when engineering publishes new FMEA for a product launch"),
    p("Tools: Airflow, cron, GitHub Actions, or cloud ETL (AWS Glue, Azure Data Factory) calling pipeline.py."),

    h1("14. Neo4j — What Happens Inside the Database"),
    h2("14.1 Nodes (Things)"),
    p("Each node is a JSON-like object with a label and properties. Example Symptom node:"),
    codeBlock(
      "(:Symptom { symptom_id: 'wm-s01', description: 'Machine does not spin', severity: 'high' })"
    ),
    h2("14.2 Relationships (Connections)"),
    p("Relationships can carry weights. The INDICATES relationship stores confidence:"),
    codeBlock(
      "(symptom:Symptom)-[:INDICATES { confidence: 0.92 }]->(fm:FailureMode)"
    ),
    h2("14.3 Cypher — The Query Language"),
    p(
      "Cypher is SQL for graphs. The most important query in this app finds the best failure mode for matched symptoms. You can run it in Neo4j Browser at http://localhost:7474:"
    ),
    codeBlock(
      "MATCH (s:Symptom)-[ind:INDICATES]->(fm:FailureMode)\n" +
        "WHERE s.symptom_id IN ['wm-s01', 'wm-s03']\n" +
        "RETURN fm.name, sum(ind.confidence) AS score\n" +
        "ORDER BY score DESC"
    ),

    h1("15. LangGraph — Why a Workflow Engine?"),
    p(
      "Diagnosis is not one function call — it is a sequence of steps with state. LangGraph lets you define this as a graph of nodes:"
    ),
    bullet("bullets", "Each node does one job (detect product, run diagnosis, format, escalate)"),
    bullet("bullets", "State passes between nodes (user message, product_id, diagnosis result, case_id)"),
    bullet("bullets", "Easy to extend: add a 'CRM enrichment' node without rewriting everything"),
    bullet("bullets", "Testable: each node can be unit-tested independently"),
    p(
      "Even without an LLM, LangGraph provides structure. When you add an LLM later, it slots into specific nodes (e.g., format_response) without changing the graph reasoning."
    ),

    h1("16. Escalation Logic — Keeping Humans in the Loop"),
    p("The system escalates to a human agent when:"),
    bullet("bullets", "Product unknown: 'Something in my kitchen is broken' — not enough info"),
    bullet("bullets", "Critical severity: microwave arcing, electrical safety risk"),
    bullet("bullets", "Low confidence: symptoms match weakly; multiple failure modes equally likely"),
    p(
      "Escalation is a feature, not a failure. The goal is not 100% automation — it is right automation. Dangerous or ambiguous cases must reach humans with full context."
    ),

    h1("17. Risk Mitigation"),
    p("The platform is designed to fail safely — preferring human handoff over risky automation:"),
    table(
      ["Risk", "How the platform mitigates it"],
      [
        ["Wrong repair advice", "Every step comes from graph DiagnosticStep nodes with safety_notes; not LLM-invented"],
        ["Missed electrical/safety hazard", "critical severity on symptoms bypasses confidence threshold — always escalates"],
        ["Over-confident multi-symptom diagnosis", "Confidence aggregates across matches; dilution triggers escalation (see washer two-turn demo)"],
        ["Out-of-warranty repair promise", "CRM + claims warranty gate runs before diagnosis when customer/asset bound"],
        ["Stale knowledge", "Enterprise ETL refreshes catalog; smoke tests block bad graph loads"],
        ["Agent cannot explain answer", "provenance_trail cites PIM, FSM, Claims, CRM source records"],
        ["Integration API down", "Connectors fall back to local fixtures in demo; production uses circuit breakers + alerts"],
      ],
      [3200, 6160]
    ),
    spacer(),

    h1("18. Common Questions (FAQ)"),
    h3("Do I need an LLM / API key to run the demo?"),
    p("No. The demo runs in graph-native mode. All reasoning comes from Neo4j queries and lexical symptom matching."),
    h3("Do I need to understand Cypher?"),
    p("Not to use the application. Yes if you want to extend queries or explore the graph in Neo4j Browser."),
    h3("Where does the knowledge graph data come from in the demo?"),
    p("Mock fixtures in data/enterprise_sources/ simulate PIM, FSM, Claims, and CRM. The pipeline script merges them automatically."),
    h3("How is this different from a decision tree?"),
    p("A decision tree is linear. A knowledge graph supports many-to-many relationships (one symptom can indicate multiple failure modes with different confidence; one failure mode can explain multiple symptoms). It also incorporates historical evidence and is queryable at runtime."),
    h3("Can one script really build everything for enterprise?"),
    p("Yes — pipeline.py is the orchestrator. You implement connectors for your specific CRM/Claims/PIM/FSM APIs. The ontology schema and Neo4j loader stay the same. This is standard ETL architecture."),
    h3("What skills do I need to maintain this in production?"),
    p("Knowledge engineering (ontology + symptom catalog), graph database basics (Neo4j/Cypher), Python, API integration, and optionally LLM prompt engineering for the formatting layer."),

    h1("19. Learning Path — What to Study Next"),
    table(
      ["Topic", "Why", "Resource Starting Point"],
      [
        ["Neo4j basics", "Understand nodes, relationships, Cypher", "Neo4j Getting Started guide; localhost:7474 Browser"],
        ["Knowledge graphs in industry", "See how graphs model real domains", "Neo4j customer case studies"],
        ["GraphRAG patterns", "Hybrid retrieval strategies", "Microsoft GraphRAG research; LangChain GraphCypherQA"],
        ["LangGraph", "Agent workflow design", "LangGraph documentation; agents/diagnosis_graph.py"],
        ["Enterprise integration", "CRM/Claims API patterns", "Your org's API docs + connectors in enterprise_pipeline/"],
        ["FMEA / reliability engineering", "Where failure modes originate", "Product engineering team at your company"],
      ],
      [2200, 3200, 3960]
    ),
    spacer(),

    h1("20. Quick Start Checklist"),
    bullet("numbers", "Install dependencies: pip install -r requirements.txt"),
    bullet("numbers", "Start Neo4j: docker start neo4j-demo (or ./run_demo.sh)"),
    bullet("numbers", "Build knowledge from enterprise fixtures: python -m graph.enterprise_pipeline.pipeline --load-neo4j"),
    bullet("numbers", "Run tests: python tests/test_diagnosis.py"),
    bullet("numbers", "Launch UI: streamlit run ui/app.py"),
    bullet("numbers", "Try example: 'Microwave runs but food stays cold, arcing inside' — watch it escalate"),
    bullet("numbers", "Open Human Agent Dashboard tab — see the full diagnostic dossier"),
    bullet("numbers", "Open Neo4j Browser — explore the graph visually"),

    h1("21. Summary"),
    p(
      "This application is a warranty claims intelligent triage system. It uses a knowledge graph (Neo4j) to store structured diagnostic expertise, GraphRAG to query that graph and produce explainable diagnoses, and LangGraph to orchestrate the workflow. Enterprise data from PIM, FSM, Claims, and CRM feeds an automated ETL pipeline that builds and maintains the ontology. Only genuine, complex, or safety-critical cases escalate to contact center agents — with full appliance owner details and a pre-built diagnostic dossier."
    ),
    p(
      "You do not need to be an AI researcher to understand or operate this system. You need to understand: (1) what knowledge it stores, (2) how customer messages flow through it, (3) where enterprise data comes from, and (4) when and why humans take over. This document, the companion architecture docs, and the pipeline script together provide that complete picture."
    ),
  ];

  return new Document({
    styles: docStyles,
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
                    text: "Beginner's Guide — GraphRAG & Enterprise Warranty Diagnosis",
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
        children,
      },
    ],
  });
}

function buildDoc4() {
  const children = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: "Cypher & Query Walkthrough",
          bold: true,
          size: 48,
          color: "1F4E79",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [
        new TextRun({
          text: "From Customer Message to Diagnosis — With Neo4j Diagrams",
          size: 30,
          italics: true,
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 },
      children: [new TextRun({ text: "Enterprise Diagnostics Chatbot", size: 24 })],
    }),
    p("Document Version: 1.0"),
    p("Date: June 25, 2026"),
    pageBreak(),

    h1("1. What This Document Covers"),
    p(
      "This document walks through one real customer message step by step. For each step it shows: which code runs, whether Cypher is used, the exact query sent to Neo4j, what Neo4j returns, and how the final diagnosis and escalation decision are made. Three diagrams are included showing the full knowledge graph, the matched path for this message, and the query execution flow."
    ),

    h2("1.1 Prerequisites"),
    bullet("bullets", "Neo4j running with knowledge graph loaded (./run_demo.sh or enterprise orchestrator)"),
    bullet("bullets", "Familiarity with basic Cypher MATCH/RETURN syntax (examples provided)"),
    bullet("bullets", "Neo4j Browser at http://localhost:7474 for interactive query replay"),
    h2("1.2 Dependencies"),
    bullet("bullets", "graph/graph_rag.py — symptom matching, failure ranking, escalation decision"),
    bullet("bullets", "agents/diagnosis_graph.py — LangGraph node sequence"),
    bullet("bullets", "data/synthetic_diagnosis_data.json or enterprise_knowledge_catalog.json — parts catalog (non-Cypher)"),
    h2("1.3 Assumptions"),
    bullet("bullets", "Product wm-001 is pre-detected or detected via keyword scoring before Cypher runs"),
    bullet("bullets", "Symptom IDs wm-s01 and wm-s03 exist in the graph with INDICATES links to failure modes"),
    bullet("bullets", "Escalation threshold is 0.65 unless overridden in .env"),
    h2("1.4 Risk Mitigation"),
    bullet("bullets", "Low-confidence outcomes escalate even when top failure mode seems plausible"),
    bullet("bullets", "Critical-severity symptoms in other product lines (e.g., microwave arcing) always escalate — see Section 10 contrast"),

    h1("2. The Customer Message"),
    codeBlock(
      "\"My washing machine won't spin and water stays in the drum\""
    ),
    p(
      "This message enters the LangGraph agent via the Streamlit chat UI (ui/app.py), which calls run_diagnosis() in agents/diagnosis_graph.py."
    ),

    h1("3. Agent Workflow Overview"),
    p("Four LangGraph nodes run in sequence:"),
    table(
      ["Order", "Node", "File", "Uses Cypher?"],
      [
        ["1", "detect_product", "agents/diagnosis_graph.py", "Yes — Query #1"],
        ["2", "run_diagnosis", "graph/graph_rag.py → diagnose()", "Yes — Queries #2–#5"],
        ["3", "format_response", "graph/graph_rag.py", "No — Python templates"],
        ["4", "handle_escalation", "utils/escalation_store.py", "No — saves JSON case"],
      ],
      [1200, 2800, 3360, 2000]
    ),
    spacer(),
    ...imageParagraph(
      "cypher-query-flow.png",
      580,
      480,
      "Figure 1: End-to-end Cypher query flow for this customer message"
    ),

    h1("4. Step 1 — detect_product"),
    h2("4.1 Python Keyword Scoring"),
    p("The message is lowercased and scored against appliance keyword lists:"),
    table(
      ["Product ID", "Keywords Checked", "Hits in Message", "Score"],
      [
        ["wm-001", "washing, washer, laundry, spin, drum", "washing, spin, drum", "3"],
        ["dw-001", "dishwasher, dish, dishes, rinse", "none", "0"],
        ["mw-001", "microwave, convection, magnetron, arcing, spark", "none", "0"],
      ],
      [1600, 3600, 2400, 1760]
    ),
    spacer(),
    p("Winner: wm-001 (washing machine). To attach the full product name, the app queries Neo4j."),

    h2("4.2 Cypher Query #1 — list_products()"),
    p("File: graph/graph_rag.py — function list_products()"),
    codeBlock(
      "MATCH (p:Product)\n" +
        "RETURN p.product_id AS product_id, p.name AS name,\n" +
        "       p.category AS category, p.brand AS brand\n" +
        "ORDER BY p.name"
    ),
    p("Plain English: Return every Product node in the database."),
    p("Key result used:"),
    codeBlock("product_id = 'wm-001'\nproduct_name = 'Front Load Washing Machine 8kg'"),

    pageBreak(),
    h1("5. Step 2 — run_diagnosis (GraphRAG Core)"),
    p("The run_diagnosis node calls diagnose() in graph/graph_rag.py. This executes up to five graph lookups plus Python text matching."),

    h2("5.1 Sub-step A — match_symptoms()"),
    h3("Cypher Query #2 — fetch symptoms for product"),
    codeBlock(
      "MATCH (p:Product {product_id: 'wm-001'})-[:HAS_SYMPTOM]->(s:Symptom)\n" +
        "RETURN s.symptom_id AS symptom_id, s.description AS description,\n" +
        "       s.severity AS severity"
    ),
    p("Plain English: Follow HAS_SYMPTOM arrows from the washing machine to all its known symptoms."),
    table(
      ["symptom_id", "description", "severity", "Matched?"],
      [
        ["wm-s01", "Machine does not spin during final cycle", "high", "YES — 'won't spin'"],
        ["wm-s02", "Excessive vibration and banging noise", "medium", "No"],
        ["wm-s03", "Water remains in drum after cycle completes", "high", "YES — 'water...drum'"],
        ["wm-s04", "Error code E21 displayed on panel", "medium", "No"],
      ],
      [1600, 4200, 1600, 1960]
    ),
    spacer(),
    p(
      "After Cypher returns the symptom list, Python (_text_similarity in graph/graph_rag.py) compares the customer message to each description using token overlap and synonyms (spin/spinning, drum/tub, water/drain). Symptoms scoring >= 0.15 are kept."
    ),
    p("Result: symptom_ids = ['wm-s01', 'wm-s03']"),

    h2("5.2 Sub-step B — rank_failure_modes()"),
    h3("Cypher Query #3 — the most important query in the app"),
    codeBlock(
      "MATCH (p:Product {product_id: 'wm-001'})-[:CAN_HAVE]->(fm:FailureMode)\n" +
        "OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\n" +
        "WHERE s.symptom_id IN ['wm-s01', 'wm-s03']\n" +
        "WITH fm,\n" +
        "     collect(DISTINCT {symptom_id: s.symptom_id, confidence: ind.confidence}) AS indications,\n" +
        "     sum(CASE WHEN ind.confidence IS NULL THEN 0 ELSE ind.confidence END) AS total_confidence,\n" +
        "     count(ind) AS link_count\n" +
        "RETURN fm.failure_mode_id, fm.name, fm.description,\n" +
        "       fm.estimated_repair_time_minutes AS repair_minutes,\n" +
        "       fm.safety_notes, indications, total_confidence, link_count\n" +
        "ORDER BY total_confidence DESC, link_count DESC"
    ),
    p("Plain English:"),
    bullet("numbers", "Find all failure modes this product can have (CAN_HAVE)"),
    bullet("numbers", "For each failure mode, check if matched symptoms INDICATES it"),
    bullet("numbers", "Sum the confidence scores on those INDICATES relationships"),
    bullet("numbers", "Return ranked list — highest score first"),
    table(
      ["Failure Mode", "INDICATES From", "total_confidence", "aggregate*"],
      [
        ["Worn Drive Belt (wm-fm01)", "wm-s01 → 0.92", "0.92", "0.46"],
        ["Failed Drain Pump (wm-fm02)", "wm-s03 → 0.88", "0.88", "0.44"],
        ["Unbalanced Load Sensor (wm-fm03)", "none", "0", "0.0"],
      ],
      [2800, 2400, 2080, 2080]
    ),
    spacer(),
    p("*aggregate_confidence = total_confidence ÷ number of matched symptoms (2). Computed in Python after the query returns."),
    p("Top failure mode: Worn Drive Belt. Overall confidence: 46%."),

    ...imageParagraph(
      "wm-001-matched-path.png",
      580,
      340,
      "Figure 2: Matched symptoms and INDICATES paths for this specific message"
    ),

    h2("5.3 Sub-step C — get_diagnostic_steps()"),
    h3("Cypher Query #4"),
    codeBlock(
      "MATCH (p:Product {product_id: 'wm-001'})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)\n" +
        "RETURN ds.step_id, ds.description, ds.order AS step_order,\n" +
        "       ds.expected_outcome AS expected_outcome\n" +
        "ORDER BY ds.order"
    ),
    p("Returns four ordered troubleshooting steps shown to the customer."),

    h2("5.4 Sub-step D — get_historical_resolutions()"),
    h3("Cypher Query #5"),
    codeBlock(
      "MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p:Product {product_id: 'wm-001'})\n" +
        "OPTIONAL MATCH (r)-[:CONFIRMED]->(fm:FailureMode)\n" +
        "WHERE fm.failure_mode_id = 'wm-fm01'\n" +
        "RETURN r.resolution_id, r.description, r.resolution_date,\n" +
        "       r.technician_notes, fm.name AS failure_mode_name\n" +
        "ORDER BY r.resolution_date DESC"
    ),
    p("Returns: 'Replaced worn drive belt; spin restored.' (2025-11-12)"),

    h2("5.5 Parts — JSON file, not Cypher"),
    p("get_parts_for_product() reads from data/synthetic_diagnosis_data.json — Drive Belt, Drain Pump, Shock Absorber Kit."),

    h2("5.6 Escalation Decision — Python logic"),
    codeBlock(
      "confidence = 0.46\n" +
        "critical = any(symptom.severity == 'critical' for symptom in matched)  → False\n" +
        "threshold = 0.65  (from config/settings.py)\n" +
        "should_escalate = (0.46 < 0.65)  → True"
    ),
    p(
      "Important: even though Worn Drive Belt is the clear winner, confidence is only 46% because the formula divides by two matched symptoms that point to different failure modes. This case escalates to a human agent."
    ),

    pageBreak(),
    h1("6. Full Neo4j Knowledge Graph Diagram"),
    p(
      "The diagram below shows the complete wm-001 subgraph stored in Neo4j: all symptoms, failure modes, INDICATES confidence weights, diagnostic steps, and a historical resolution."
    ),
    ...imageParagraph(
      "wm-001-full-knowledge-graph.png",
      580,
      400,
      "Figure 3: Complete washing machine knowledge graph in Neo4j"
    ),

    h1("7. Step 3 — format_response"),
    p("No Cypher. Python builds markdown from the DiagnosisResult:"),
    codeBlock(
      "**Product:** Front Load Washing Machine 8kg\n\n" +
        "**Matched Symptoms:**\n" +
        "- Machine does not spin during final cycle (severity: high)\n" +
        "- Water remains in drum after cycle completes (severity: high)\n\n" +
        "**Most Likely Failure Mode:** Worn Drive Belt\n" +
        "- Confidence: 46%\n\n" +
        "**Recommended Diagnostic Steps:**\n" +
        "1. Run empty spin cycle...\n" +
        "2. Inspect drive belt...\n\n" +
        "**Escalation:** Confidence (46%) below threshold — escalating to human agent."
    ),

    h1("8. Step 4 — handle_escalation"),
    p("No Cypher. Because should_escalate = True, save_escalation() writes a case to data/escalations.json:"),
    codeBlock(
      "{\n" +
        "  \"case_id\": \"<uuid>\",\n" +
        "  \"user_message\": \"My washing machine won't spin and water stays in the drum\",\n" +
        "  \"diagnosis\": { full payload with symptoms, failure modes, steps, evidence }\n" +
        "}"
    ),
    p("The Human Agent Dashboard tab in Streamlit displays this dossier so the agent starts with full context."),

    h1("9. Complete Query Summary"),
    table(
      ["#", "Function", "Cypher Purpose", "When It Runs"],
      [
        ["1", "list_products()", "List all Product nodes", "Product detection"],
        ["2", "match_symptoms()", "HAS_SYMPTOM → get symptom catalog", "Symptom matching"],
        ["3", "rank_failure_modes()", "INDICATES confidence aggregation", "Root cause ranking"],
        ["4", "get_diagnostic_steps()", "HAS_DIAGNOSTIC_STEP → procedures", "Troubleshooting steps"],
        ["5", "get_historical_resolutions()", "HistoricalResolution → CONFIRMED", "Past repair evidence"],
      ],
      [600, 2800, 3600, 2360]
    ),
    spacer(),

    h1("10. Contrast — Microwave Message (Different Escalation Reason)"),
    p("Message: 'Microwave runs but food stays cold, arcing inside'"),
    bullet("bullets", "Same 5 Cypher query pattern, product_id = mw-001"),
    bullet("bullets", "Matches mw-s01 (critical) and mw-s02 (critical)"),
    bullet("bullets", "Query #3 ranks Magnetron Failure and Damaged Waveguide Cover"),
    bullet("bullets", "Escalates because severity = critical — NOT because of low confidence"),
    bullet("bullets", "Safety notes ('HIGH VOLTAGE') come from FailureMode properties in Query #3 results"),

    h1("11. Try It Yourself in Neo4j Browser"),
    p("Open http://localhost:7474 (login: neo4j / password) and run:"),
    codeBlock(
      "// See all symptom-failure links\n" +
        "MATCH (s:Symptom)-[r:INDICATES]->(fm:FailureMode)\n" +
        "RETURN s.description, fm.name, r.confidence\n" +
        "ORDER BY r.confidence DESC\n\n" +
        "// Simulate Query #3 for this message\n" +
        "MATCH (p:Product {product_id: 'wm-001'})-[:CAN_HAVE]->(fm:FailureMode)\n" +
        "OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)\n" +
        "WHERE s.symptom_id IN ['wm-s01', 'wm-s03']\n" +
        "RETURN fm.name, sum(ind.confidence) AS score\n" +
        "ORDER BY score DESC"
    ),

    h1("12. Key Takeaway"),
    p(
      "Cypher is the language for asking Neo4j structured questions. A query is one specific question. This app runs up to five queries per diagnosis to go from a customer complaint → matched symptoms → ranked failure mode → troubleshooting steps → past repairs → escalate or resolve. The diagrams in this document show the graph those queries traverse."
    ),
  ];

  return new Document({
    styles: docStyles,
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
                    text: "Cypher & Query Walkthrough — With Neo4j Diagrams",
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
        children,
      },
    ],
  });
}

async function main() {
  // Generate diagrams first (requires Python matplotlib)
  const { execSync } = require("child_process");
  try {
    execSync("python docs/scripts/generate_diagrams.py", { cwd: path.join(__dirname, "..", ".."), stdio: "inherit" });
  } catch (e) {
    console.warn("Warning: diagram generation failed — doc 4 may lack images.", e.message);
  }

  const doc1 = buildDoc1();
  const doc2 = buildDoc2();
  const doc3 = buildDoc3();
  const doc4 = buildDoc4();

  const buf1 = await Packer.toBuffer(doc1);
  const buf2 = await Packer.toBuffer(doc2);
  const buf3 = await Packer.toBuffer(doc3);
  const buf4 = await Packer.toBuffer(doc4);

  const path1 = path.join(OUT_DIR, "01-Architecture-and-Solution-Design.docx");
  const path2 = path.join(OUT_DIR, "02-Knowledge-Graph-Ontology-and-GraphRAG-Deep-Dive.docx");
  const path3 = path.join(OUT_DIR, "03-Beginners-Guide-Everything-Under-the-Hood.docx");
  const path4 = path.join(OUT_DIR, "04-Cypher-Query-Walkthrough-with-Diagrams.docx");

  fs.writeFileSync(path1, buf1);
  fs.writeFileSync(path2, buf2);
  fs.writeFileSync(path3, buf3);
  fs.writeFileSync(path4, buf4);

  console.log(`Created: ${path1}`);
  console.log(`Created: ${path2}`);
  console.log(`Created: ${path3}`);
  console.log(`Created: ${path4}`);
  console.log("For implementation roadmap (doc 5), run: node docs/scripts/generate_implementation_plan.js");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});