/**
 * Production Pipelines & Phased Roadmap — Granular POC / Pilot / Production (Doc 10)
 * Run: node docs/scripts/generate_phased_roadmap_doc.js
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

const OUT_DIR = path.join(__dirname, "..");
const OUT_FILE = path.join(OUT_DIR, "10-Production-Pipelines-and-Phased-Roadmap.docx");
const PNG_DIR = path.join(OUT_DIR, "graphviz", "rendered", "png");

const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } };
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const p = (t) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun(t)] });
const pb = (ref, t) => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80 }, children: [new TextRun(t)] });
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
            borders, width: { size: colWidths[i], type: WidthType.DXA },
            shading: { fill: "1F4E79", type: ShadingType.CLEAR }, margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: "FFFFFF" })] })],
          })
        ),
      }),
      ...rows.map((row) => new TableRow({
        children: row.map((c, i) =>
          new TableCell({
            borders, width: { size: colWidths[i], type: WidthType.DXA }, margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun(String(c))] })],
          })
        ),
      })),
    ],
  });
}

function figure(filename, caption, w = 600, h = 400) {
  const fp = path.join(PNG_DIR, filename);
  if (!fs.existsSync(fp)) return [p(`[Render: bash docs/graphviz/render_all.sh — ${filename}]`)];
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 80 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(fp), transformation: { width: w, height: h },
        altText: { title: caption, description: caption, name: filename } })],
    }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: caption, italics: true, size: 20, color: "444444" })] }),
  ];
}

const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: PAGE },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Production Pipelines & Phased Roadmap", italics: true, size: 18 })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Page ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children: [
      h1("Production Pipelines & Phased Roadmap"),
      p("Enterprise Diagnostics GraphRAG Platform — Document 10"),
      p("Granular definition of production pipeline types, their purpose, and a sliced POC → Pilot → Production program with features, tasks, deliverables, and proof points."),
      p(
        "Nothing in this document is validated. Scope, timelines, pipeline counts, and the claim that 14 production pipelines are required are planning hypotheses only. The reference demo does not confirm any pipeline design. See Document 11 — zero assumptions validated at engagement start; demo is illustration, not proof."
      ),
      spacer(),

      h2("Prerequisites"),
      pb("bullets", "POC complete with ≥70% top-1 accuracy on curated scenarios (Document 05)"),
      pb("bullets", "Pilot platform codebase (this repository) with 3 ETL pipelines operational"),
      pb("bullets", "Executive charter for multi-quarter production program — not a single MVP extension"),
      pb("bullets", "SME governance model defined before scaling past 15 product families"),
      spacer(),

      h2("Dependencies"),
      tbl(
        ["Dependency", "POC", "Pilot", "Production"],
        [
          ["Knowledge ETL pipeline", "Fixture + 1 live read", "Nightly scheduled", "Full + incremental"],
          ["Smoke validation gate", "Manual trigger", "CI/CD gate", "Mandatory promotion gate"],
          ["SME approval workflow", "Ad hoc review", "Queue tool MVP", "Governance pipeline #8"],
          ["Neo4j", "Docker staging", "Aura Professional", "Aura Enterprise cluster"],
          ["Vector index pipeline", "Out", "Optional pilot", "Pipeline #6 where ROI proven"],
          ["Document ingestion", "Manual", "Pilot on 2 families", "Pipeline #2 at scale"],
        ],
        [2400, 2000, 2000, 2960]
      ),
      spacer(),

      h2("Assumptions"),
      pb("bullets", "14 batch/governance pipelines are required for enterprise scale — 3 alone are insufficient"),
      pb("bullets", "Knowledge engineering throughput (~2–4 families/engineer/month) is the scaling bottleneck"),
      pb("bullets", "Pilot proves operational model; production is 12–24 months for 100+ families"),
      pb("bullets", "Each phase has explicit 'does NOT prove' boundaries to prevent scope creep"),
      spacer(),

      h2("Risk Mitigation"),
      tbl(
        ["Risk", "Phase gate mitigation"],
        [
          ["Scaling catalog before pilot KPIs stable", "Phase 3 charter blocked until MVP override rate trends down"],
          ["Automated knowledge without SME sign-off", "Pipeline #8 SME Review & Approval — non-negotiable"],
          ["Silent graph corruption", "Pipeline #3 Data Quality & Reconciliation + Pipeline #4 smoke gate"],
          ["EOL product misdiagnosis", "Pipeline #7 Catalog Retirement"],
          ["Regulatory audit failure", "Pipeline #9 Lineage Audit Export + Pipeline #10 Compliance Snapshot"],
        ],
        [3600, 5760]
      ),
      spacer(),

      h2("1. Executive Answer — How Many Pipelines?"),
      p("In production you need **14 batch/governance/operations pipelines** plus **3 runtime integration services** (not batch). Your pilot platform already implements the first 3 batch pipelines — the remainder are required to scale, govern, and sustain accuracy across hundreds of product families."),
      ...figure("19-production-pipelines.png", "Figure 19: Production pipeline landscape", 620, 520),
      spacer(),

      h2("2. Production Pipeline Catalog"),
      tbl(
        ["#", "Pipeline", "Type", "Purpose", "Why required"],
        [
          ["1", "Knowledge ETL (full + incremental)", "Batch", "Ingest PIM, FSM, Claims, CRM into ontology catalog", "Keeps graph aligned with authoritative systems of record"],
          ["2", "Document Ingestion", "Batch", "Extract structured entities from FMEA PDFs, service manuals", "Diagnostic steps and symptoms originate in unstructured docs"],
          ["3", "Data Quality & Reconciliation", "Batch", "Cross-check counts, orphan nodes, duplicate keys across sources", "Prevents silent graph corruption at scale"],
          ["4", "Smoke / Regression Validation", "Gate", "Run curated scenarios before any promotion", "Blocks bad knowledge from reaching production graph"],
          ["5", "Staging Promotion", "Gate", "MERGE approved catalog batch to production Neo4j", "Separates experimentation from customer-facing truth"],
          ["6", "Vector Index Build", "Batch (optional)", "Embed symptom phrases for hybrid retrieval", "Improves recall on noisy customer language — only where ROI proven"],
          ["7", "Catalog Retirement", "Batch", "Remove or archive EOL product subgraphs", "Compliance and accuracy for discontinued models"],
          ["8", "SME Review & Approval", "Governance", "Human sign-off on new/changed failure modes and steps", "Regulatory and brand risk — automation cannot self-certify all knowledge"],
          ["9", "Ontology Version Migration", "Governance", "Schema upgrades with backward-compatible transforms", "Enables ontology evolution without full reload"],
          ["10", "Lineage & Audit Export", "Governance", "Export etl_batches + provenance for compliance", "Answers 'why did the system say that on date X?'"],
          ["11", "Graph Backup & DR Snapshot", "Operations", "Scheduled Neo4j backups, restore drills", "Production SLA and disaster recovery"],
          ["12", "Connector Health & Credential Rotation", "Operations", "Monitor API availability, rotate secrets", "Enterprise integrations fail silently without this"],
          ["13", "Agent Override & Feedback Ingestion", "Continuous improvement", "Capture agent corrections → curation queue", "Closes the loop — overrides become graph improvements"],
          ["14", "KPI / Telemetry Aggregation", "Continuous improvement", "Deflection, override rate, confidence distribution", "Proves business value and guides catalog prioritization"],
        ],
        [400, 2000, 1000, 2800, 3160]
      ),
      spacer(),
      h3("Runtime services (not batch pipelines)"),
      tbl(
        ["Service", "Purpose", "Why separate from batch"],
        [
          ["Diagnosis API (LangGraph + GraphRAG)", "Live customer/agent diagnosis", "Sub-second latency; reads production graph only"],
          ["CRM & Warranty Enrichment", "Bind session to asset, validate warranty", "Per-session context; cannot be pre-computed in batch"],
          ["Case Management Handoff", "Create Service Cloud case on escalation", "Transactional write at moment of escalation"],
        ],
        [2800, 3200, 3360]
      ),
      spacer(),
      p("Pilot platform mapping: pipelines 1, 4, 5 exist today (knowledge_etl, smoke_validation, staging_promotion). Pipelines 2, 3, 6–14 are production program scope."),
      pgBreak(),

      h2("3. Phased Roadmap Overview"),
      ...figure("20-phased-roadmap-swimlane.png", "Figure 20: POC → Pilot → Production phased swimlane", 620, 280),
      tbl(
        ["Phase", "Duration", "Primary question answered", "Go/No-Go gate"],
        [
          ["POC", "Weeks 1–8", "Does graph-backed diagnosis work and do agents trust the dossier?", "Week 8: accuracy ≥70%, SME accepts ontology, 1 live CRM read"],
          ["Pilot", "Weeks 9–16", "Can contact center operate this daily with real cases?", "Week 16: 4 weeks stable ETL, override rate trending down, SSO stable"],
          ["Production", "Month 5–24+", "Can we scale catalog, govern knowledge, and meet enterprise NFRs?", "Per region: security sign-off, 80% test-pack accuracy, SRE ready"],
        ],
        [1200, 1400, 4000, 3160]
      ),
      spacer(),

      pgBreak(),
      h2("4. Phase 1 — POC (Weeks 1–8)"),
      h3("4.1 What this phase proves"),
      pb("bullets", "GraphRAG diagnosis is more explainable and consistent than keyword scripts or generic LLM-only chat"),
      pb("bullets", "Provenance trail is sufficient for compliance and agent trust"),
      pb("bullets", "Escalation policy (confidence + critical symptoms) reduces false automation on ambiguous cases"),
      pb("bullets", "Enterprise ETL pattern can merge PIM + FSM + Claims + CRM into one ontology"),
      pb("bullets", "Team velocity is measurable for honest Pilot estimate"),
      spacer(),

      h3("4.2 Features in scope"),
      tbl(
        ["Feature area", "POC capability", "Out of scope"],
        [
          ["Knowledge graph", "2 product families (e.g. washer + dishwasher), full ontology per family", "100+ families"],
          ["GraphRAG", "Lexical symptom match + INDICATES ranking + provenance", "Vector hybrid retrieval"],
          ["LangGraph agent", "4-node workflow, escalation to agent store", "Multi-turn memory, LLM rewrite"],
          ["CRM integration", "Read-only asset + warranty (1 system)", "Write-back, multi-CRM"],
          ["Case management", "Representative API handoff on escalation", "Production Service Cloud routing rules"],
          ["UI", "Streamlit self-service + agent dashboard (internal URL)", "Customer production channel, SSO"],
          ["Pipelines", "ETL + smoke validation + staging promotion", "Incremental ETL, SME workflow, DR"],
          ["Security", "Non-prod Neo4j, secrets in vault pattern", "Pen test, SOC2, WAF"],
        ],
        [1800, 3800, 3760]
      ),
      spacer(),

      h3("4.3 Tasks by week"),
      tbl(
        ["Week", "Tasks", "Owner"],
        [
          ["1", "Source system assessment; ontology spec v1; integration matrix; non-prod Neo4j", "Architect + Knowledge Engineer"],
          ["2", "PIM + FSM connectors; provenance schema; lineage store design", "Data Engineer"],
          ["3", "Claims + CRM connectors; OntologyBuilder; first ETL run", "Integration Engineer"],
          ["4", "populate_graph staging automation; smoke scenario pack v1", "Graph Engineer + QA"],
          ["5", "GraphRAG tuning; escalation threshold calibration; evaluation harness", "Tech Lead"],
          ["6", "LangGraph agent; agent dashboard with provenance UI", "Backend + UX"],
          ["7", "SME validation session; accuracy report; override simulation", "Knowledge Engineer + CC lead"],
          ["8", "POC readout; Pilot business case; refined estimate from velocity", "Program Manager + Architect"],
        ],
        [800, 5760, 2800]
      ),
      spacer(),

      h3("4.4 Deliverables"),
      tbl(
        ["ID", "Deliverable", "Proves"],
        [
          ["POC-D1", "Ontology specification v1", "Knowledge model is agreed by engineering and SME"],
          ["POC-D2", "Enterprise ETL pipeline (4 connectors + OntologyBuilder)", "Multi-source merge is automatable"],
          ["POC-D3", "Smoke validation gate + scenario pack", "Bad graph loads are preventable"],
          ["POC-D4", "GraphRAG evaluation report (≥70% top-1 on POC families)", "Diagnosis accuracy hypothesis validated"],
          ["POC-D5", "Agent dossier UI with provenance citations", "Agents accept explainability format"],
          ["POC-D6", "Lineage audit log (etl_batches.jsonl pattern)", "Governance foundation exists"],
          ["POC-D7", "POC executive readout + Pilot charter", "Funding decision for Pilot is informed"],
        ],
        [1000, 4200, 4160]
      ),
      spacer(),

      h3("4.5 Exit criteria (Week 8 Go/No-Go)"),
      pb("bullets", "≥70% top-1 failure mode accuracy on agreed POC test pack"),
      pb("bullets", "≥3 SME-approved failure mode paths with provenance documented"),
      pb("bullets", "Contact center lead confirms agent dossier is usable without re-interviewing customer"),
      pb("bullets", "At least 1 live CRM read integration demonstrated (not fixture-only)"),
      pb("bullets", "ETL + smoke + promotion ran successfully for 2 consecutive weeks"),

      pgBreak(),
      h2("5. Phase 2 — Pilot (Weeks 9–16)"),
      h3("5.1 What this phase proves"),
      pb("bullets", "Real agents can use the platform daily without workflow disruption"),
      pb("bullets", "Scheduled ETL is reliable enough for operational dependency"),
      pb("bullets", "Case write-back and CRM enrichment work under pilot load"),
      pb("bullets", "Override rate and deflection can be measured against baseline"),
      pb("bullets", "Production program cost and timeline can be forecast from real velocity"),
      spacer(),

      h3("5.2 Features in scope"),
      tbl(
        ["Feature area", "Pilot capability", "Deferred to production"],
        [
          ["Catalog breadth", "10–15 product families", "100+ families"],
          ["Channel", "Pilot web chat + agent desktop embed; Streamlit retired", "Mobile, IVR, full omnichannel"],
          ["Auth", "Corporate SSO for agents", "Customer identity federation"],
          ["Integrations", "CRM read + Claims read + CCaaS case create (production APIs)", "IoT error codes, parts ordering"],
          ["Pipelines", "Scheduled ETL (nightly); smoke gate; promotion with approval flag", "Incremental ETL, document ingestion at scale, vector index"],
          ["Governance", "Manual SME approval via ticket; lineage export", "Dedicated curation tool"],
          ["Observability", "Override logging; basic KPI dashboard", "Full telemetry pipeline, alerting"],
        ],
        [1800, 3800, 3760]
      ),
      spacer(),

      h3("5.3 Tasks by week"),
      tbl(
        ["Week", "Tasks"],
        [
          ["9–10", "FastAPI diagnosis service hardened; SSO; retire Streamlit for pilot channel"],
          ["11", "Production CRM + Claims connectors; credential management"],
          ["12", "CCaaS case write-back; escalation routing rules"],
          ["13", "Airflow/Dagster scheduled ETL; connector health checks"],
          ["14", "Expand catalog to 10–15 families; expand smoke scenario pack"],
          ["15", "Agent pilot UAT; override logging; provenance UI polish"],
          ["16", "Pilot metrics review; production program charter; go/no-go"],
        ],
        [1200, 8160]
      ),
      spacer(),

      h3("5.4 Deliverables"),
      tbl(
        ["ID", "Deliverable", "Proves"],
        [
          ["PIL-D1", "Production-grade Diagnosis API + SSO", "Enterprise integration readiness"],
          ["PIL-D2", "Scheduled ETL with monitoring", "Operational knowledge refresh"],
          ["PIL-D3", "CRM + Claims + CCaaS production connectors", "End-to-end warranty workflow"],
          ["PIL-D4", "Agent desktop embed", "Contact center adoption path"],
          ["PIL-D5", "Pilot operations runbook", "Supportability"],
          ["PIL-D6", "4-week KPI report (deflection, override, AHT proxy)", "Business case for production funding"],
          ["PIL-D7", "Production scale program plan with measured velocity", "Honest 12–24 month forecast"],
        ],
        [1000, 4200, 4160]
      ),
      spacer(),

      h3("5.5 Exit criteria (Week 16 Go/No-Go)"),
      pb("bullets", "≥75% top-1 accuracy on pilot family test pack"),
      pb("bullets", "ETL succeeded 4 consecutive scheduled runs without manual intervention"),
      pb("bullets", "Agent override rate stable or declining over final 2 pilot weeks"),
      pb("bullets", "No P1 security findings open from pilot SSO review"),
      pb("bullets", "Case write-back success rate ≥95% on escalations"),

      pgBreak(),
      h2("6. Phase 3 — Production Program (Month 5–24+)"),
      h3("6.1 What this phase proves"),
      pb("bullets", "Platform sustains enterprise NFRs (availability, latency, security) at peak season volume"),
      pb("bullets", "Knowledge engineering throughput scales to 100+ families without accuracy collapse"),
      pb("bullets", "Governance workflow keeps graph trustworthy as sources change"),
      pb("bullets", "Measurable contact center KPI improvement vs. pre-program baseline"),
      spacer(),

      h3("6.2 Production workstreams (parallel tracks)"),
      tbl(
        ["Workstream", "Key tasks", "Deliverables", "Proves"],
        [
          ["Catalog scaling", "Family onboarding playbook; SME network; 5–10 families/month", "D-16 Catalog playbook", "Throughput model works"],
          ["Pipeline maturity", "All 14 pipelines; incremental ETL; document ingestion", "Pipeline ops runbooks", "Sustainable knowledge ops"],
          ["Platform hardening", "HA Neo4j Aura; API autoscaling; DR drills", "D-15 HA deployment", "Production SLA met"],
          ["Security & compliance", "Pen test; PII boundary; SOC2 alignment", "D-17 Security pack", "Enterprise risk acceptance"],
          ["Retrieval quality", "Hybrid RAG pilot → production where ROI proven", "Retrieval evaluation reports", "Accuracy on noisy language"],
          ["Omnichannel", "Web, mobile, IVR API consumers", "Channel integration guides", "Customer reach"],
          ["Continuous improvement", "Override ingestion; KPI dashboard", "D-18 KPI dashboard", "Ongoing value measurement"],
        ],
        [1600, 2800, 2400, 2560]
      ),
      spacer(),

      h3("6.3 Production pipeline rollout sequence"),
      pb("numbers", "Month 5–6: Incremental ETL + data quality reconciliation + connector health"),
      pb("numbers", "Month 6–8: SME approval workflow + lineage audit export"),
      pb("numbers", "Month 8–10: Document ingestion assist (manual QA gate)"),
      pb("numbers", "Month 10–12: Agent override feedback loop + KPI aggregation"),
      pb("numbers", "Month 12+: Vector index (if pilot ROI positive); catalog retirement; DR automation"),
      spacer(),

      h3("6.4 Production exit criteria (per regional rollout)"),
      pb("bullets", "≥80% top-1 accuracy on regional test pack"),
      pb("bullets", "Security and pen test sign-off complete"),
      pb("bullets", "Neo4j HA failover drill passed within RTO target"),
      pb("bullets", "All 14 pipelines operational with on-call runbooks"),
      pb("bullets", "SME approval SLA defined and met for 2 consecutive release cycles"),

      pgBreak(),
      h2("7. Pipeline × Phase Matrix"),
      tbl(
        ["Pipeline", "POC", "Pilot", "Production"],
        [
          ["1 Knowledge ETL", "Manual + on-demand", "Scheduled nightly", "Incremental + full weekly"],
          ["2 Document ingestion", "Manual PDF curation", "Semi-automated pilot", "Automated with SME gate"],
          ["3 Data quality", "Basic counts", "Orphan detection", "Full reconciliation"],
          ["4 Smoke validation", "Yes", "Yes + expanded pack", "Yes + regional packs"],
          ["5 Staging promotion", "Yes (same instance)", "Staging → prod Neo4j", "Approved batches only"],
          ["6 Vector index", "—", "Pilot on 2 families", "Production if ROI proven"],
          ["7 Catalog retirement", "—", "—", "Yes"],
          ["8 SME approval", "Manual ticket", "Ticket + SLA", "Curation tool"],
          ["9 Ontology migration", "—", "—", "Yes"],
          ["10 Lineage export", "JSONL file", "Scheduled export", "Compliance integration"],
          ["11 Backup / DR", "—", "Weekly backup", "HA + drill"],
          ["12 Connector health", "Manual", "Automated checks", "Alerting + rotation"],
          ["13 Override feedback", "—", "Logging only", "Curation queue"],
          ["14 KPI aggregation", "—", "Basic dashboard", "Full analytics"],
        ],
        [2400, 1400, 2000, 3560]
      ),
      spacer(),

      h2("8. What Each Phase Does NOT Try to Prove"),
      tbl(
        ["Phase", "Explicitly not a goal (avoid scope creep)"],
        [
          ["POC", "100-family catalog; production SSO; omnichannel; vector search; IoT integration"],
          ["Pilot", "Full catalog scale; multi-region HA; automated document ingestion at scale; SOC2 certification"],
          ["Production (early)", "Every product globally on day 1; zero agent overrides; LLM-only diagnosis without graph"],
        ],
        [2000, 7360]
      ),
      spacer(),

      h2("9. Relationship to Pilot Platform Codebase"),
      p("The repository already implements the diagnosis pattern and the first 3 batch pipelines. Production investment concentrates on:"),
      pb("bullets", "Connector maturity (auth, pagination, idempotency, error handling)"),
      pb("bullets", "Governance pipelines 8–10 (SME approval, ontology migration, audit export)"),
      pb("bullets", "Operations pipelines 11–12 (backup, connector health)"),
      pb("bullets", "Continuous improvement pipelines 13–14 (override feedback, KPIs)"),
      pb("bullets", "Runtime hardening (API SLA, SSO, omnichannel consumers)"),
      p("populate_graph.py and graph_rag.py remain stable primitives across all phases — the program scales knowledge breadth and operational maturity around them."),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUT_FILE, buffer);
  console.log(`Written: ${OUT_FILE}`);
});