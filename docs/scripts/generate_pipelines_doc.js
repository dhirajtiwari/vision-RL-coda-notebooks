/**
 * Enterprise Pipelines & Data Lineage documentation (Doc 07)
 * Run: node docs/scripts/generate_pipelines_doc.js
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
const OUT_FILE = path.join(OUT_DIR, "07-Enterprise-Pipelines-and-Data-Lineage.docx");

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

const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT }] },
    ],
  },
  sections: [
    {
      properties: { page: PAGE },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ text: "Enterprise Pipelines & Data Lineage", italics: true, size: 18 })],
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
      children: [
        h1("Enterprise Pipelines & Data Lineage"),
        p("Diagnostics GraphRAG Platform — Document 07"),
        p(
          "This document describes the enterprise knowledge ETL pipelines, connector architecture, " +
            "provenance model, smoke validation gates, and runtime integration paths used in the demo platform."
        ),
        spacer(),

        h2("Prerequisites"),
        tbl(
          ["Requirement", "Details"],
          [
            ["Python 3.12+ venv", "pip install -r requirements.txt"],
            ["Neo4j on :7687", "docker start neo4j-demo or ./run_enterprise_demo.sh step 1"],
            ["Mock APIs on :8090", "Required for USE_MOCK_ENTERPRISE_APIS=true (default)"],
            [".env", "Copy from .env.example; defaults work locally"],
          ],
          [2800, 6560]
        ),
        spacer(),

        h2("Dependencies"),
        tbl(
          ["Component", "Module / Service", "Role"],
          [
            ["Orchestrator", "graph/enterprise_pipeline/orchestrator.py", "Runs all pipelines in sequence"],
            ["Connectors", "connectors/*.py", "PIM, FSM, Claims, CRM extract"],
            ["OntologyBuilder", "transformers/ontology_builder.py", "Merge sources into catalog JSON"],
            ["Graph loader", "graph/populate_graph.py", "MERGE into Neo4j with provenance"],
            ["Lineage store", "utils/lineage_store.py", "Append-only etl_batches.jsonl audit"],
            ["Smoke tests", "tests/test_enterprise_scenarios.py --smoke", "Promotion gate"],
            ["Mock enterprise", "simulation/mock_enterprise_apps.py", "HTTP APIs on :8090"],
          ],
          [2200, 3600, 3560]
        ),
        spacer(),

        h2("Assumptions"),
        pb("bullets", "USE_MOCK_ENTERPRISE_APIS=true unless production URLs are set in .env"),
        pb("bullets", "Staging and production Neo4j are the same instance in the demo"),
        pb("bullets", "Fixture files in data/enterprise_sources/ are authoritative for local runs"),
        pb("bullets", "ENABLE_PROVENANCE=true attaches source_system and batch_id to loaded entities"),
        pb("bullets", "Failed smoke validation skips staging promotion — graph left at last good batch"),
        spacer(),

        h2("Risk Mitigation"),
        tbl(
          ["Risk", "Mitigation"],
          [
            ["Bad data enters Neo4j", "Smoke validation gate; dry-run mode on orchestrator"],
            ["Silent connector failure", "ConnectorResult error logging; fixture fallback in demo"],
            ["Untraceable diagnosis", "Provenance model on every entity; lineage batches in etl_batches.jsonl"],
            ["Idempotency loss on re-run", "MERGE keys in populate_graph.py; batch_id on each load"],
            ["Production API credential leak", ".env gitignored; use secrets manager in production"],
            ["Stale graph after source update", "Re-run orchestrator; scheduled ETL in production (Airflow/cron)"],
          ],
          [3200, 6160]
        ),
        spacer(),

        h2("1. Pipeline Overview"),
        p(
          "Three pipelines run in sequence via graph/enterprise_pipeline/orchestrator.py. " +
            "This mirrors production patterns: extract from source systems, validate before promotion, " +
            "then load the approved graph to Neo4j."
        ),
        tbl(
          ["Pipeline", "Module", "Purpose"],
          [
            ["Knowledge ETL", "pipelines/knowledge_etl.py", "Extract PIM/FSM/Claims/CRM → build ontology JSON → load Neo4j"],
            ["Smoke Validation", "pipelines/smoke_validation.py", "Run enterprise regression scenarios before promotion"],
            ["Staging Promotion", "pipelines/staging_promotion.py", "Promote validated catalog batch to Neo4j (demo: same instance)"],
          ],
          [2200, 3200, 3960]
        ),
        spacer(),

        h2("2. Source Systems & Connectors"),
        p("Each connector supports HTTP (mock or production API) and local fixture fallback."),
        tbl(
          ["System", "Connector", "Fixture", "Records"],
          [
            ["PIM (Product Catalog)", "pim_connector.py", "data/enterprise_sources/pim_catalog.json", "Products, parts, BOM"],
            ["FSM (Field Service)", "fsm_connector.py", "data/enterprise_sources/fsm_work_orders.json", "Closed work orders, resolutions"],
            ["Claims", "claims_connector.py", "data/enterprise_sources/claims_history.json", "Warranty policies, closed claims"],
            ["CRM (Assets)", "crm_connector.py", "data/enterprise_sources/crm_assets.json", "Customers, registered assets"],
          ],
          [1800, 2400, 2800, 2360]
        ),
        spacer(),
        code("USE_MOCK_ENTERPRISE_APIS=true  →  http://localhost:8090/api/{pim,fsm,claims,crm}"),
        code("python -m simulation.mock_enterprise_apps   # starts mock on :8090"),
        spacer(),

        h2("3. Knowledge ETL Flow"),
        pb("numbers", "Connectors fetch raw records from PIM, FSM, Claims, and CRM."),
        pb("numbers", "OntologyBuilder (transformers/ontology_builder.py) merges records into a unified catalog."),
        pb("numbers", "Provenance metadata is attached per entity (source_system, source_record_id, batch_id)."),
        pb("numbers", "Catalog written to data/enterprise_knowledge_catalog.json."),
        pb("numbers", "populate_graph.py loads catalog into Neo4j with MERGE + provenance fields."),
        pb("numbers", "Lineage batch logged to data/lineage/etl_batches.jsonl via utils/lineage_store.py."),
        spacer(),

        pgBreak(),
        h2("4. Provenance Model"),
        p("graph/provenance.py defines ProvenanceRecord fields used at ETL time and surfaced at diagnosis time."),
        tbl(
          ["Field", "Description"],
          [
            ["source_system", "Origin system: PIM, FSM, Claims, CRM"],
            ["source_record_id", "Primary key in source system"],
            ["entity_type", "Product, Symptom, FailureMode, Part, etc."],
            ["batch_id", "ETL batch identifier (ETL-YYYYMMDD-xxxxxxxx)"],
            ["loaded_at", "UTC timestamp of graph load"],
          ],
          [2800, 6560]
        ),
        p("At runtime, GraphRAG attaches provenance_trail to DiagnosisResult for agent explainability."),
        spacer(),

        h2("5. Smoke Validation Gate"),
        p("Before staging promotion, smoke_validation.py runs tests/enterprise_test_scenarios.py --smoke."),
        p("Scenarios cover:"),
        pb("bullets", "Product detection and failure-mode ranking (wm-001, dw-001, mw-001)"),
        pb("bullets", "Escalation rules (critical symptoms, low confidence)"),
        pb("bullets", "CRM enrichment (CUST-10042 / AST-WM-4421)"),
        pb("bullets", "Warranty eligibility gating"),
        p("If smoke fails, staging promotion is skipped — preventing bad graph loads."),
        spacer(),

        h2("6. Runtime Integration Paths"),
        h3("Streamlit UI (ui/app.py)"),
        pb("bullets", "Customer Chatbot with optional CRM customer/asset binding"),
        pb("bullets", "Warranty eligibility display before diagnosis"),
        pb("bullets", "Provenance trail in diagnosis expanders"),
        pb("bullets", "Enterprise Systems tab: lineage batches + simulated cases"),
        spacer(),
        h3("REST API (api/main.py)"),
        pb("bullets", "POST /diagnose — LangGraph + CRM enrichment + warranty gate"),
        pb("bullets", "GET /lineage/batches — ETL audit log"),
        pb("bullets", "GET /health — Neo4j and provenance status"),
        spacer(),
        h3("Case Management Handoff"),
        pb("bullets", "integrations/case_management.py POSTs escalations to mock CCaaS"),
        pb("bullets", "Cases stored in data/simulated_cases.json"),
        spacer(),

        pgBreak(),
        h2("7. Commands & Demo Scripts"),
        code("./run_enterprise_demo.sh"),
        p("Starts Neo4j, mock enterprise APIs (:8090), runs all pipelines, tests, REST API (:8080), and Streamlit (:8501)."),
        spacer(),
        code("python -m graph.enterprise_pipeline.orchestrator"),
        code("python -m graph.enterprise_pipeline.orchestrator --dry-run"),
        code("USE_ENTERPRISE=true ./run_demo.sh"),
        spacer(),

        h2("8. Test Coverage"),
        tbl(
          ["Test File", "Scope"],
          [
            ["tests/test_diagnosis.py", "Core GraphRAG diagnosis accuracy"],
            ["tests/test_enterprise_scenarios.py", "Enterprise regression + CRM/warranty scenarios"],
            ["tests/test_pipeline_integration.py", "ETL orchestrator integration"],
            ["tests/test_api.py", "REST API health and diagnose endpoint"],
          ],
          [3600, 5760]
        ),
        spacer(),

        h2("9. Production Considerations"),
        pb("bullets", "Separate Neo4j staging and production instances (neo4j_staging_uri in settings)"),
        pb("bullets", "Replace mock APIs with authenticated connector credentials"),
        pb("bullets", "Schedule orchestrator via Airflow/Dagster with lineage alerts"),
        pb("bullets", "Retain etl_batches.jsonl in object storage for audit compliance"),
        pb("bullets", "Add schema validation and idempotent MERGE keys per entity type"),
        p("See Document 05 (Enterprise Implementation Roadmap) for POC/MVP/production timelines."),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUT_FILE, buffer);
  console.log(`Written: ${OUT_FILE}`);
});