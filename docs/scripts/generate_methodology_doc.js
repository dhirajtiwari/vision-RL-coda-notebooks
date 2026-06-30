/**
 * Document 12 — Solution Approach & Delivery Methodology
 * Run: node docs/scripts/generate_methodology_doc.js
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
const OUT_FILE = path.join(OUT_DIR, "12-Solution-Approach-and-Delivery-Methodology.docx");

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
const pn = (ref, t) =>
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
        new TextRun({
          text: "Solution Approach & Delivery Methodology",
          bold: true,
          size: 52,
          color: "1F4E79",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [
        new TextRun({
          text: "Graph-First Warranty Diagnostics — How We Design, Validate, and Deliver",
          size: 32,
          color: "2E75B6",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: "Enterprise Diagnostics GraphRAG Platform",
          size: 24,
          italics: true,
        }),
      ],
    }),
    tbl(
      ["Document", "Version", "Date", "Author Role", "Classification"],
      [
        [
          "12 — Approach & Methodology",
          "1.0",
          "June 25, 2026",
          "Senior Solution Architect",
          "Internal — Program Planning",
        ],
      ],
      [2800, 1000, 1400, 2400, 1760]
    ),
    spacer(),
    p(
      "This document defines the solution approach and end-to-end delivery methodology for an enterprise warranty diagnostics program. It explains what we do, in what order, why we do it that way, and how we measure whether the approach is working. It is written for executive sponsors, enterprise architects, program managers, knowledge engineers, and integration leads."
    ),
    p(
      "Relationship to other documents: Document 11 records assumptions (all hypothesis today). Document 01 describes the target architecture. Document 05 and 10 describe phased scope. This document explains the method that connects them — discovery before commitment, graph-truth before generation, governance before scale."
    ),
    pgBreak(),

    h1("1. Executive Summary"),
    p(
      "Our approach is a hypothesis-driven, graph-first methodology for warranty and support triage. We do not begin by deploying AI chat at scale. We begin by making diagnostic knowledge explicit, traceable, and testable — then automating only what the evidence supports, while keeping humans accountable for safety, policy, and ambiguity."
    ),
    p("The methodology rests on five pillars:"),
    tbl(
      ["Pillar", "What It Means"],
      [
        ["1. Discover before you build", "Validate problem, data, and systems before phase commitment"],
        ["2. Graph-truth before generation", "Structured knowledge and Cypher retrieval are the source of truth; LLM is optional UX"],
        ["3. Governed knowledge engineering", "SME-approved ontology and content — not scraped or hallucinated"],
        ["4. Right automation, not maximum automation", "Escalate on low confidence and critical severity by design"],
        ["5. Phased proof with measured velocity", "POC → MVP → Production only when gates pass on real client data"],
      ],
      [2400, 6960]
    ),
    spacer(),
    p(
      "The reference demo in this repository illustrates the methodology — it does not validate it. Every phase produces evidence that moves assumptions in Document 11 from H (Hypothesis) to V (Validated) or I (Invalidated)."
    ),

    h1("2. Purpose & Scope of This Methodology"),
    h2("2.1 Purpose"),
    pb("bullets", "Provide a single, professional description of how we approach enterprise warranty diagnostics programs"),
    pb("bullets", "Explain the rationale — why graph-first GraphRAG, why phased delivery, why human-in-the-loop"),
    pb("bullets", "Define repeatable activities, roles, artifacts, and gates across the program lifecycle"),
    pb("bullets", "Align technical, knowledge, integration, and operating workstreams under one method"),

    h2("2.2 In Scope"),
    pb("bullets", "End-to-end program method: discovery → knowledge build → integration → runtime diagnosis → escalation → scale"),
    pb("bullets", "Batch knowledge engineering (ETL) and real-time diagnosis (GraphRAG + agent orchestration)"),
    pb("bullets", "Contact center handoff, provenance, and governance models"),
    pb("bullets", "POC, MVP, and production scaling methodology"),

    h2("2.3 Out of Scope"),
    pb("bullets", "Client-specific system names, timelines, or costs (see Document 05 — indicative only)"),
    pb("bullets", "Detailed Cypher, schema, or code walkthrough (see Documents 02, 04)"),
    pb("bullets", "Assumption register and open questions (see Document 11)"),
    pb("bullets", "Presentation scripts and live demo narration (see Documents 08, 09)"),

    pgBreak(),
    h1("3. Problem Framing — What We Are Solving"),
    p(
      "Consumer durables and appliance enterprises receive high volumes of warranty and support contacts. Many are resolvable without agent involvement; some are safety-critical; many fall outside warranty coverage. Treating every contact identically inflates cost, delays urgent cases, and produces inconsistent advice."
    ),
    p("Our methodology targets four outcomes simultaneously:"),
    tbl(
      ["Outcome", "Methodological Response"],
      [
        ["Deflect or resolve eligible cases at automated tier", "Graph-backed diagnosis with self-service diagnostic steps"],
        ["Never miss safety-critical cases", "Severity-based mandatory escalation — independent of confidence score"],
        ["Reduce agent handle time on escalations", "Pre-built diagnostic dossier with provenance before agent speaks to customer"],
        ["Maintain trust, auditability, and policy compliance", "Source-traceable evidence; warranty gate; governed knowledge ingestion"],
      ],
      [3200, 6160]
    ),
    spacer(),

    h1("4. Solution Approach — The Graph-First Model"),
    h2("4.1 Conceptual Model"),
    p(
      "We separate the program into two velocities that must not be conflated:"
    ),
    code(
      "BATCH (Knowledge Engineering)          RUNTIME (Customer Diagnosis)\n" +
        "─────────────────────────────          ────────────────────────────\n" +
        "Enterprise sources                     Customer message + CRM context\n" +
        "  → Extract / Transform                  → LangGraph agent workflow\n" +
        "  → Validate / SME approve               → GraphRAG retrieval (Neo4j)\n" +
        "  → Load staging graph                   → Confidence + severity check\n" +
        "  → Smoke test gate                      → Respond OR escalate with dossier\n" +
        "  → Promote to production graph        → Case management handoff"
    ),
    spacer(),
    p(
      "Knowledge is curated offline with governance. Diagnosis is read-only against the approved graph at runtime. This boundary is deliberate: it prevents customer conversations from mutating authoritative knowledge and makes rollback possible when a bad ETL batch is detected."
    ),

    h2("4.2 Core Design Choices"),
    tbl(
      ["Choice", "Our Approach", "What We Reject as Primary Strategy"],
      [
        ["Knowledge representation", "Property graph ontology in Neo4j", "Unstructured document pile + vector-only search"],
        ["Reasoning mechanism", "Graph traversal + confidence-weighted ranking", "Opaque LLM chain-of-thought"],
        ["Orchestration", "LangGraph typed workflow (detect → diagnose → format → escalate)", "Monolithic prompt or stateless API call"],
        ["Enterprise data", "Connector-based ETL with provenance", "Manual spreadsheet maintenance at scale"],
        ["Customer channel (early phases)", "Demonstration / pilot UI → production channel later", "Production omnichannel before accuracy proven"],
        ["Escalation philosophy", "Selective automation with explicit handoff", "100% automation target for all symptom types"],
      ],
      [2200, 3600, 3560]
    ),
    spacer(),

    pgBreak(),
    h1("5. Rationale — Why This Methodology"),
    p(
      "This section answers the question executives and architects ask first: why not ChatGPT, why not a decision tree, why not buy a CCaaS add-on?"
    ),

    h2("5.1 Why Graph-First GraphRAG (Not LLM-Only)"),
    tbl(
      ["Criterion", "LLM-Only Chat", "Our Graph-First Method", "Rationale"],
      [
        ["Factual grounding", "Model weights + retrieved chunks; hallucination risk", "Explicit graph nodes and relationships with confidence scores", "Warranty and repair advice requires auditable sources — injury and liability exposure"],
        ["Explainability", "Post-hoc citation; inconsistent", "evidence[] and provenance_trail on every diagnosis", "Agents and regulators need to see why a failure mode was ranked"],
        ["Enterprise integration", "Requires custom tool-calling layer", "Native fit: CRM enriches runtime; PIM/FSM feed batch graph", "Diagnostic knowledge spans systems — graph models the join"],
        ["Safety governance", "Prompt engineering only", "Critical severity bypasses automation; SME-approved content", "Safety content cannot be self-certified by automation"],
        ["Cost at scale", "Per-token inference on every turn", "Cypher queries on indexed graph; LLM optional for formatting", "Predictable runtime cost for high-volume tier-1 traffic"],
        ["Improvement loop", "Fine-tuning or prompt iteration — opaque", "Calibrate INDICATES confidence from field outcomes; versioned ETL", "Measurable quality improvement tied to service data"],
      ],
      [1800, 2600, 2800, 2160]
    ),
    spacer(),

    h2("5.2 Why a Knowledge Graph (Not Rules / Decision Trees Alone)"),
    pb("bullets", "Appliance diagnosis is many-to-many: one symptom indicates multiple failure modes with different weights; one failure mode explains multiple symptoms"),
    pb("bullets", "Decision trees become unmaintainable across hundreds of product families and regional variants"),
    pb("bullets", "Historical field evidence (FSM, claims) strengthens links over time — trees do not absorb this naturally"),
    pb("bullets", "Graph queries support 'what else could cause these symptoms together?' — combination reasoning decision trees encode poorly"),

    h2("5.3 Why Governed ETL (Not Ad Hoc Content Authoring)"),
    pb("bullets", "Authoritative sources (PIM, FMEA, service manuals, FSM) must be the system of record — not agent notes or chat logs"),
    pb("bullets", "Provenance (source_system, batch_id, approval_status) is required for compliance and agent trust"),
    pb("bullets", "Smoke validation gates prevent bad knowledge from reaching the production graph"),
    pb("bullets", "Repeatable pipelines scale to hundreds of families; manual JSON does not"),

    h2("5.4 Why Phased Delivery (Not Big-Bang)"),
    pb("bullets", "Client enterprise landscape, data quality, and SME throughput are unknown at engagement start (Document 11)"),
    pb("bullets", "Accuracy and agent acceptance are measurable only on real data with real agents — not on a synthetic demo"),
    pb("bullets", "Integration access and security approvals have lead times that parallel work cannot assume"),
    pb("bullets", "Stopping after POC or MVP with documented evidence is a valid outcome — avoids sunk-cost escalation"),

    h2("5.5 Why Human-in-the-Loop Is a Feature"),
    pb("bullets", "Escalation is success when the case is ambiguous, policy-sensitive, or safety-critical"),
    pb("bullets", "Agents receive a dossier — the methodology optimizes their starting point, not their elimination"),
    pb("bullets", "Override rate is a first-class metric; it feeds knowledge calibration — not a failure to hide"),

    pgBreak(),
    h1("6. Methodology Principles"),
    tbl(
      ["#", "Principle", "Operational Meaning"],
      [
        ["P1", "Evidence over opinion", "No architecture or accuracy claim without a test pack, pilot metric, or signed SME review"],
        ["P2", "Assumption visibility", "Every design choice maps to an ID in Document 11; demo never counts as evidence"],
        ["P3", "Separation of batch and runtime", "ETL writes graph; diagnosis reads graph — no runtime MERGE of diagnostic facts"],
        ["P4", "Fail safe on uncertainty", "Low confidence escalates; critical severity escalates — automation yields to human judgment"],
        ["P5", "Provenance by default", "Every symptom, failure mode, and step shown to an agent cites an authoritative source"],
        ["P6", "Incremental catalog expansion", "Onboard product families in governed increments — not big-bang catalog migration"],
        ["P7", "Integration abstraction", "Connectors implement a contract; OntologyBuilder and populate_graph stay stable"],
        ["P8", "Measure before scale", "MVP velocity (families/month, override rate, ETL reliability) gates production funding"],
      ],
      [600, 2400, 6360]
    ),
    spacer(),

    h1("7. Delivery Lifecycle — Four Phases"),
    p(
      "The methodology defines four sequential phases. Progression requires gate evidence — not elapsed time alone."
    ),
    tbl(
      ["Phase", "Name", "Objective", "Primary Question Answered"],
      [
        ["0", "Frame & Discover", "Align problem, assumptions, dependencies", "Should we pursue this approach at all?"],
        ["1", "Prove (POC)", "Validate approach on limited real scope", "Does graph diagnosis work on our data and products?"],
        ["2", "Pilot (MVP)", "Operate with real agents and integrations", "Do agents trust it and does it improve KPIs?"],
        ["3", "Scale (Production)", "Expand catalog, harden platform, govern at enterprise level", "Can we run this reliably for hundreds of families?"],
      ],
      [800, 1400, 3600, 3560]
    ),
    spacer(),

    h2("7.1 Phase 0 — Frame & Discover"),
    p("Activities:"),
    pn("numbers", "Executive alignment on problem statement and success criteria — not yet committed targets"),
    pn("numbers", "Assumption workshop — populate and challenge Document 11"),
    pn("numbers", "Source system matrix — which systems own product, symptom, field, claim, customer data"),
    pn("numbers", "Reference demo walkthrough — explicitly labeled illustration, not proof"),
    pn("numbers", "Pilot family shortlist and SME commitment"),
    pn("numbers", "Privacy boundary draft — what enters Neo4j vs stays in CRM"),
    p("Exit gate: Section 14 acknowledgment (Document 11); named sponsor; CRM or product data path identified; SME hours committed."),

    h2("7.2 Phase 1 — Prove (POC)"),
    p("Activities:"),
    pn("numbers", "Ontology v1 signed with service engineering"),
    pn("numbers", "First live connector (typically CRM read) plus PIM/FSM/Claims export or API"),
    pn("numbers", "Provenance schema and lineage store implemented"),
    pn("numbers", "Automated populate_graph on staging Neo4j"),
    pn("numbers", "GraphRAG evaluation harness on client-authored scenario pack (not demo scripts alone)"),
    pn("numbers", "Agent dossier UI with source citations — reviewed by CC lead"),
    p("Exit gate: ≥70% top-1 failure mode on agreed scenario pack; 100% provenance on escalations; CRM read demonstrated on sandbox data."),

    h2("7.3 Phase 2 — Pilot (MVP)"),
    p("Activities:"),
    pn("numbers", "Production-appropriate API (FastAPI) with SSO for agents"),
    pn("numbers", "Case management write-back on escalation"),
    pn("numbers", "Scheduled ETL with monitoring and promotion workflow"),
    pn("numbers", "Expand to 10–15 families via knowledge engineering sprints"),
    pn("numbers", "Live agent pilot with override logging"),
    pn("numbers", "KPI dashboard: deflection, AHT, override rate, ETL success"),
    p("Exit gate: Override rate trending down; SSO stable; ETL reliable 4 consecutive weeks; business case for production program."),

    h2("7.4 Phase 3 — Scale (Production)"),
    p("Activities:"),
    pn("numbers", "Full connector suite with incremental sync"),
    pn("numbers", "Governance pipelines: SME approval queue, data quality, catalog retirement, audit export"),
    pn("numbers", "HA Neo4j, security hardening, regional rollout"),
    pn("numbers", "Knowledge onboarding factory for 100+ families"),
    pn("numbers", "Optional hybrid vector retrieval where ROI proven"),
    p("Exit gate: Regional accuracy targets; security sign-off; SRE runbooks; sustained KPI improvement vs baseline."),

    pgBreak(),
    h1("8. Knowledge Engineering Methodology"),
    p(
      "Knowledge engineering is not a one-time data load. It is a continuous discipline with the same rigor as software engineering."
    ),

    h2("8.1 Authoritative Source Hierarchy"),
    pn("numbers", "Safety / regulatory content — engineering FMEA and official service manual (highest precedence)"),
    pn("numbers", "Diagnostic steps — current service manual SOP version"),
    pn("numbers", "Symptom–failure confidence — empirical field and claims data (calibrated, versioned)"),
    pn("numbers", "Customer language variants — call center KB mapped to canonical symptoms"),

    h2("8.2 Ontology-First Content Model"),
    pb("bullets", "Agree entity types and relationships before ingesting client data (Product, Symptom, FailureMode, DiagnosticStep, Part, HistoricalResolution)"),
    pb("bullets", "Extend schema only through governed change — not ad hoc per product"),
    pb("bullets", "Pydantic (or equivalent) validation at transform time — reject malformed records before graph touch"),

    h2("8.3 SME Workflow (Human-in-the-Loop)"),
    tbl(
      ["Step", "Activity", "Approver"],
      [
        ["1", "ETL proposes new or changed entities from source delta", "Automated validation only"],
        ["2", "Changed safety-related failure modes queued for review", "Reliability / service engineering SME"],
        ["3", "Symptom catalog mapping reviewed for pilot families", "Knowledge engineer + SME"],
        ["4", "Confidence change >10% on safety links", "SME mandatory"],
        ["5", "Approved batch promoted to production graph", "Knowledge engineering lead + automated smoke gate"],
      ],
      [800, 5200, 3360]
    ),
    spacer(),

    h2("8.4 Knowledge Onboarding Cadence"),
    p("Expected throughput (hypothesis until measured in POC):"),
    pb("bullets", "2–4 product families per knowledge engineer per month including SME review"),
    pb("bullets", "Parallel sprints during MVP; factory model during production"),
    pb("bullets", "Regression scenario pack grows with each family — never shrink test coverage to match velocity pressure"),

    h1("9. Technical Delivery Methodology"),
    h2("9.1 Runtime Diagnosis Method"),
    p("Every customer message follows the same governed sequence:"),
    tbl(
      ["Step", "Method", "Output"],
      [
        ["1", "CRM / asset enrichment (if session bound)", "product_id, warranty context"],
        ["2", "Warranty eligibility gate", "proceed / deflect / inform customer"],
        ["3", "Product detection (keywords or pre-bound asset)", "product_id"],
        ["4", "GraphRAG: symptom match → failure rank → steps → history", "DiagnosisResult with evidence[]"],
        ["5", "Escalation decision (severity + confidence + unknown product)", "should_escalate, reason"],
        ["6", "Format response (template; optional LLM polish later)", "Customer-facing message"],
        ["7", "Case handoff if escalated", "Structured dossier to CCaaS / CRM Cases"],
      ],
      [800, 4000, 4560]
    ),
    spacer(),

    h2("9.2 Batch ETL Method"),
    pb("numbers", "Extract — connectors fetch delta from PIM, FSM, Claims, CRM (API or governed export)"),
    pb("numbers", "Transform — OntologyBuilder merges sources; attaches provenance metadata"),
    pb("numbers", "Validate — schema validation + business rules + reconciliation checks"),
    pb("numbers", "Load — populate_graph MERGE to staging Neo4j"),
    pb("numbers", "Gate — smoke regression on curated scenarios"),
    pb("numbers", "Promote — approved batch only to production graph"),
    pb("numbers", "Log — lineage batch in immutable audit store"),

    h2("9.3 Integration Method"),
    pb("bullets", "Connector contract pattern: fetch(), health_check(), normalized ConnectorResult"),
    pb("bullets", "Sandbox-first: prove read paths before write-back"),
    pb("bullets", "Contract tests per connector — detect vendor API drift early"),
    pb("bullets", "Runtime integrations (CRM) separate from batch integrations (PIM/FSM) — different SLA and failure modes"),

    h2("9.4 Quality Engineering Method"),
    tbl(
      ["Layer", "Method", "When"],
      [
        ["Unit", "GraphRAG functions, escalation rules, ontology validation", "Every commit"],
        ["Scenario", "Curated symptom messages per product family", "Pre-promotion smoke gate"],
        ["Enterprise", "CRM bind, warranty gate, provenance completeness", "Pre-release"],
        ["Pilot", "Live override logging, agent feedback", "MVP onward"],
        ["Regression", "Expanded pack as catalog grows", "Continuous"],
      ],
      [1600, 4800, 2960]
    ),
    spacer(),

    pgBreak(),
    h1("10. Governance & Decision Methodology"),
    h2("10.1 Decision Rights"),
    tbl(
      ["Decision", "Owner", "Forum"],
      [
        ["Program charter and phase funding", "Executive sponsor", "Steering committee"],
        ["Ontology schema changes", "Knowledge engineering lead + SME", "Architecture board"],
        ["Escalation thresholds and severity taxonomy", "Contact center + safety SME", "Operating policy workshop"],
        ["ETL promotion to production graph", "Knowledge lead + automated smoke pass", "Weekly ops review"],
        ["Integration credentials and network paths", "Client IT security", "Security review"],
        ["Production regional rollout", "Program manager + KPI evidence", "Gate review"],
      ],
      [3200, 2800, 3360]
    ),
    spacer(),

    h2("10.2 Cadence"),
    tbl(
      ["Forum", "Frequency", "Purpose"],
      [
        ["Steering", "Bi-weekly", "Phase progress, blockers, assumption status"],
        ["Architecture / ontology", "Weekly during POC/MVP", "Schema, integration, provenance decisions"],
        ["SME review queue", "Weekly", "Approve changed safety and failure mode content"],
        ["ETL operations", "Daily during pilot", "Batch health, promotion, lineage"],
        ["Agent pilot retrospective", "Weekly during MVP", "Override patterns, dossier usability"],
      ],
      [2400, 2400, 4560]
    ),
    spacer(),

    h1("11. Roles & Responsibilities in the Method"),
    tbl(
      ["Role", "Methodological Responsibility"],
      [
        ["Executive sponsor", "Charter, SME time, sandbox access, phase gate decisions"],
        ["Program manager", "Cadence, RAID log, assumption register maintenance"],
        ["Solution architect", "Approach integrity, assumption traceability, gate definitions"],
        ["Knowledge engineer / ontologist", "Symptom catalog, FMEA mapping, SME session facilitation"],
        ["Graph / data engineer", "Neo4j, ETL load, staging promotion, lineage"],
        ["Integration engineer", "Connectors, contract tests, credential management"],
        ["Backend engineer", "LangGraph, GraphRAG, APIs, escalation payload"],
        ["QA / evaluation lead", "Scenario packs, accuracy metrics, regression harness"],
        ["Contact center lead", "Escalation policy, agent pilot, dossier acceptance"],
        ["Service engineering SME", "Safety content approval, failure mode validation"],
        ["Security architect", "PII boundary, SSO, production sign-off"],
      ],
      [2800, 6560]
    ),
    spacer(),

    h1("12. Artifacts Produced by the Methodology"),
    tbl(
      ["Phase", "Key Artifacts", "Doc Reference"],
      [
        ["0 — Discover", "Assumption register, source matrix, privacy boundary draft", "Doc 11"],
        ["0 — Discover", "Architecture target state", "Doc 01"],
        ["1 — POC", "Ontology spec v1, provenance schema, evaluation report", "Doc 02, 07"],
        ["1 — POC", "Staging graph + automated load", "Doc 07"],
        ["2 — MVP", "Production API, SSO integration, case write-back", "Doc 05"],
        ["2 — MVP", "Pilot KPI dashboard, override analysis", "Doc 05"],
        ["3 — Scale", "Pipeline catalog, governance workflows, regional rollout pack", "Doc 10"],
        ["All", "Architecture diagrams, walkthroughs, presentation materials", "Docs 06, 08, 09"],
      ],
      [1400, 4000, 3960]
    ),
    spacer(),

    pgBreak(),
    h1("13. Metrics & Evidence Method"),
    p("The methodology is evidence-based. Each phase has primary metrics — not vanity counts."),
    tbl(
      ["Phase", "Primary Metrics", "Methodological Use"],
      [
        ["POC", "Top-1 failure mode accuracy on client scenario pack", "Validates A-71, A-79 — approach fit"],
        ["POC", "Provenance completeness on escalations", "Validates agent trust hypothesis (A-75)"],
        ["POC", "Time to load first real family end-to-end", "Calibrates knowledge engineering velocity"],
        ["MVP", "Agent override rate", "Detects knowledge gaps and symptom recall issues"],
        ["MVP", "Escalated AHT vs baseline", "Validates dossier value"],
        ["MVP", "Tier-1 deflection on pilot families", "Validates business case direction"],
        ["MVP", "ETL success rate and promotion cycle time", "Validates operational readiness"],
        ["Production", "Sustained accuracy across regional packs", "Guards against catalog drift"],
        ["Production", "Incident rate, P95 latency, availability", "Validates platform hardening"],
      ],
      [1200, 3600, 4560]
    ),
    spacer(),
    p(
      "Metrics without baselines are directional only. Phase 0 must capture current AHT, tier-1 volume, and escalation rate before targets are negotiated."
    ),

    h1("14. Alternative Approaches Considered"),
    tbl(
      ["Alternative", "Why Not Selected as Primary Method"],
      [
        ["General-purpose LLM chatbot (ChatGPT-style)", "Insufficient explainability and grounding for warranty liability; difficult CRM/claims integration at truth layer"],
        ["Static decision trees / IVR scripts", "Do not scale across product families; cannot absorb field evidence dynamically"],
        ["Buy COTS diagnostic AI module", "May not fit enterprise ontology, provenance, or escalation policy; vendor lock-in on knowledge"],
        ["Vector RAG on PDF manuals only", "Retrieves text chunks without structured failure ranking or confidence model; weak multi-symptom reasoning"],
        ["Full automation — minimize escalation", "Violates safety and policy boundaries; unacceptable for electrical and gas appliance domains"],
        ["Big-bang catalog migration", "Fails when data quality and SME throughput unknown; high risk of ungoverned graph"],
      ],
      [3200, 6160]
    ),
    spacer(),
    p(
      "Hybrid elements may be adopted later where evidence supports them — e.g. vector retrieval for symptom recall (Document 10, Pipeline 6) — without replacing graph-truth as the authoritative reasoning layer."
    ),

    h1("15. Methodology Risks & Mitigations"),
    tbl(
      ["Risk", "Methodological Mitigation"],
      [
        ["Demo mistaken for validated solution", "Phase 0 explicitly labels demo; Document 11 R-00"],
        ["Stakeholders expect ChatGPT UX", "Principle P2 + executive alignment on graph-truth narrative"],
        ["SME bottleneck blocks catalog scale", "Governed queue; parallel engineers; realistic throughput assumptions"],
        ["Integration access delays", "Sandbox request Week 0; fixture bridge only for demo — not for gate sign-off"],
        ["Accuracy plateau on noisy customer language", "Measure in POC; introduce vector pilot only if lexical baseline insufficient"],
        ["Organizational resistance from agents", "MVP pilot with override logging; dossier designed with CC lead input"],
        ["Scope creep into full claims adjudication", "Phase boundaries in Document 05; warranty gate ≠ policy engine"],
      ],
      [3200, 6160]
    ),
    spacer(),

    h1("16. How to Read the Document Set"),
    tbl(
      ["Document", "Role in the Methodology"],
      [
        ["11 — Assumptions Register", "What we do not know; what must be validated before commitment"],
        ["12 — This document", "Approach, rationale, and delivery method"],
        ["01 — Architecture", "Target solution shape (hypothesis until validated)"],
        ["02 — GraphRAG Deep Dive", "Technical method for retrieval and diagnosis"],
        ["05 — Implementation Roadmap", "Phased scope and effort hypotheses"],
        ["07 — Pipelines & Lineage", "Batch knowledge engineering method in detail"],
        ["10 — Production Pipelines", "Scale-stage pipeline and governance method"],
        ["08, 09 — Demo materials", "Illustration only — not methodological evidence"],
      ],
      [3200, 6160]
    ),
    spacer(),

    h1("17. Summary"),
    p(
      "Our methodology is deliberately conservative where risk is high — safety, policy, and explainability — and deliberately iterative where uncertainty is high — data quality, integrations, and catalog scale. We use a property-graph knowledge layer as the system of truth, governed ETL to maintain it, GraphRAG for explainable retrieval, and LangGraph for a testable agent workflow. We automate what the evidence supports; we escalate what it does not; we measure every phase before funding the next."
    ),
    p(
      "The rationale is straightforward: warranty diagnostics is not a general conversation problem. It is a structured evidence problem spanning enterprise systems, requiring audit trails, SME governance, and contact center partnership. This method addresses that reality — and refuses to confuse a working demo with a validated enterprise program."
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
                    text: "Doc 12 — Solution Approach & Delivery Methodology",
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

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT_FILE, buffer);
  console.log(`Written: ${OUT_FILE}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});