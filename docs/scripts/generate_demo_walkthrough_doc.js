/**
 * Live Diagnostic Session — Technical Walkthrough (Doc 09)
 * Stakeholder-ready narrative with swimlane diagrams (current/future state).
 * Run: node docs/scripts/generate_demo_walkthrough_doc.js
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
const OUT_FILE = path.join(OUT_DIR, "09-Live-Diagnostic-Session-Technical-Walkthrough.docx");
const PNG_DIR = path.join(OUT_DIR, "graphviz", "rendered", "png");
const GVIZ_DIR = path.join(OUT_DIR, "graphviz");

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

function figure(filename, caption, width = 600, height = 420) {
  const fp = path.join(PNG_DIR, filename);
  if (!fs.existsSync(fp)) {
    return [p(`[Diagram not rendered: ${filename}]`)];
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 80 },
      children: [
        new ImageRun({
          type: "png",
          data: fs.readFileSync(fp),
          transformation: { width, height },
          altText: { title: caption, description: caption, name: filename },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: caption, italics: true, size: 20, color: "444444" })],
    }),
  ];
}

function dotExcerpt(name) {
  const fp = path.join(GVIZ_DIR, name);
  if (!fs.existsSync(fp)) return [];
  const src = fs.readFileSync(fp, "utf8").trim();
  const excerpt = src.length > 900 ? src.slice(0, 900) + "\n// ..." : src;
  return [h3(`Graphviz: ${name}`), code(excerpt)];
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
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
  },
  sections: [
    {
      properties: { page: PAGE },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({ text: "Live Diagnostic Session — Technical Walkthrough", italics: true, size: 18 }),
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
      children: [
        h1("Live Diagnostic Session — Technical Walkthrough"),
        p("Enterprise Diagnostics GraphRAG Platform — Document 09"),
        p(
          "This document explains a live customer diagnostic session on the pilot platform " +
            "(washer spin failure, two-turn conversation, CRM enrichment, warranty gate, 94% vs 47% confidence, " +
            "escalation, and Service Cloud case handoff) and maps each outcome to the solution architecture, " +
            "Neo4j knowledge graph, LangGraph workflow, and enterprise knowledge-engineering pipelines."
        ),
        spacer(),

        h2("1. Executive Summary"),
        tbl(
          ["Platform indicator", "Value", "Business meaning"],
          [
            ["Neo4j Connected", "Yes", "Authoritative knowledge graph available for GraphRAG queries"],
            ["Mode Enterprise", "Yes", "Full enterprise integration path enabled (CRM · PIM · FSM · Claims)"],
            ["Integration Services Online", "Yes", "Enterprise Integration Layer (sandbox) serving representative APIs"],
            ["Open Escalations", "3", "Cases requiring human agent review with full graph context"],
          ],
          [2200, 1800, 5360]
        ),
        spacer(),
        p(
          "The live session comprised two customer turns on registered asset AST-WM-4421. Turn 1 achieved automated resolution at 94% confidence. " +
            "Turn 2 introduced a second symptom, reducing aggregate confidence to 47% and triggering governed escalation with case-management handoff."
        ),

        pgBreak(),
        h2("2. Current State vs Future State (Swimlanes)"),
        p("Figure 15 shows the POC / pilot architecture with an Enterprise Integration Layer (sandbox) connecting representative enterprise services to the diagnostics platform."),
        ...figure("15-current-state-swimlane.png", "Figure 15: Current state swimlane — POC / pilot platform", 620, 380),
        p("Figure 16 shows the target production architecture with authoritative systems, governed ETL, and production Neo4j."),
        ...figure("16-future-state-swimlane.png", "Figure 16: Future state swimlane — target production", 620, 400),
        p("Figure 17 traces your live washer session across functional swimlanes — customer, CRM, platform, knowledge graph, and agent operations."),
        ...figure("17-live-session-swimlane.png", "Figure 17: Live session swimlane — two customer turns", 620, 420),
        p("Figure 18 separates batch knowledge engineering from runtime diagnosis — the operational boundary stakeholders care about for SLA and governance."),
        ...figure("18-etl-runtime-swimlane.png", "Figure 18: ETL & governance vs runtime diagnosis swimlane", 620, 320),
        spacer(),

        h2("3. System Context & Module Map"),
        p("Figure 1 shows where the diagnostics platform sits relative to enterprise systems and operators."),
        ...figure("01-system-context.png", "Figure 1: Enterprise system context (C4-style)", 620, 480),
        p("Figure 2 maps Python modules to functional responsibilities."),
        ...figure("02-module-block.png", "Figure 2: Module block diagram", 620, 460),

        h3("Technology stack mapping"),
        tbl(
          ["Layer", "Technology", "Module", "Role in live session"],
          [
            ["Presentation", "Streamlit", "ui/app.py", "Self-service channel, CRM binding, agent console"],
            ["Orchestration", "LangGraph", "agents/diagnosis_graph.py", "Governed diagnosis workflow per message"],
            ["GraphRAG", "Neo4j + Python", "graph/graph_rag.py", "Evidence-based Cypher retrieval"],
            ["Knowledge store", "Neo4j 5.x", "graph/neo4j_client.py", "Product wm-001 ontology"],
            ["Integration layer", "FastAPI sandbox", "simulation/mock_enterprise_apps.py", "Representative CRM / Claims / CCaaS APIs"],
            ["Integrations", "Python", "integrations/*.py", "CRM enrichment, warranty gate, case handoff"],
            ["Knowledge engineering", "Python pipelines", "graph/enterprise_pipeline/", "Batch load before runtime"],
            ["Audit", "JSONL lineage", "utils/lineage_store.py", "ETL governance trail"],
          ],
          [1400, 1600, 2800, 3560]
        ),
        spacer(),

        pgBreak(),
        h2("4. Knowledge Engineering — How the Graph Was Built"),
        p("Before your chat session, the orchestrator ran three pipelines to build the Neo4j knowledge graph."),
        ...figure("14-etl-to-runtime.png", "Figure 14: ETL pipelines to runtime diagnosis", 620, 500),
        ...figure("06-etl-pipeline.png", "Figure 6: Knowledge ETL pipeline detail", 620, 440),
        pb("numbers", "Pipeline 1 knowledge_etl — PIM + FSM + Claims + CRM connectors → OntologyBuilder → JSON catalog"),
        pb("numbers", "populate_graph.py — MERGE nodes with source_system, source_record_id provenance"),
        pb("numbers", "Pipeline 2 smoke_validation — regression scenarios gate promotion"),
        pb("numbers", "Pipeline 3 staging_promotion — load validated catalog to Neo4j"),
        pb("numbers", "lineage_store.py — each step logged to data/lineage/etl_batches.jsonl"),
        spacer(),

        h2("5. Neo4j Ontology — Live Session Data Model"),
        ...figure("05-neo4j-ontology.png", "Figure 5: Neo4j ontology (nodes and relationships)", 600, 480),
        ...figure("13-demo-response-field-map.png", "Figure 13: Response fields → graph entities → enterprise sources", 620, 420),
        p("Every field in the diagnostic response maps to a governed graph entity ingested from an authoritative source:"),
        tbl(
          ["Response section", "Neo4j entity", "Source system", "Live session example"],
          [
            ["Product name", "Product wm-001", "PIM", "Front Load Washing Machine 8kg"],
            ["Matched Symptoms", "Symptom wm-s01, wm-s02", "FMEA", "manuals/wm-001/symptoms.pdf"],
            ["Failure Mode", "FailureMode wm-fm01", "FMEA", "fmea/wm-001/wm-fm01.pdf"],
            ["Diagnostic Steps", "DiagnosticStep wm-d01..d04", "ServiceManual", "troubleshooting.pdf#step=N"],
            ["Past Resolutions", "HistoricalResolution", "FSM", "CLM-2026-00481, WO-FSM-88104"],
            ["Parts", "JSON catalog", "PIM", "Drive Belt Assembly AH-DB-8842"],
            ["CRM Context", "Runtime enrichment", "CRM (sandbox)", "Jane Martinez, AST-WM-4421"],
            ["Warranty", "Runtime only", "CRM + Claims", "WP-STANDARD-24M"],
          ],
          [2200, 2000, 1800, 3360]
        ),
        spacer(),

        pgBreak(),
        h2("6. CRM & Warranty — Pre-Diagnosis Enrichment"),
        p("Note: Customer dropdown showed Robert Chen while asset AST-WM-4421 was selected. Asset ID takes priority — the platform correctly resolved Jane Martinez as the registered owner."),
        ...figure("12-streamlit-enterprise-layers.png", "Figure 12: Platform layer stack — self-service channel", 600, 520),
        pb("bullets", "ui/app.py invokes enrich_session_from_crm(asset_id=AST-WM-4421)"),
        pb("bullets", "integrations/crm_enrichment.py queries Enterprise Integration Layer — CRM assets endpoint"),
        pb("bullets", "Returns Jane Martinez (actual asset owner), product wm-001, warranty active until 2027-06-15"),
        pb("bullets", "integrations/warranty_eligibility.py checks status + Claims policies → eligible=true"),
        pb("bullets", "product_id passed to run_diagnosis() — skips keyword auto-detect"),
        code("product_id = CRM asset product OR appliance dropdown OR detect_product(message)"),
        spacer(),

        h2("7. LangGraph Workflow — Per Customer Message"),
        ...figure("03-langgraph-workflow.png", "Figure 3: LangGraph diagnosis workflow", 580, 380),
        ...figure("08-runtime-sequence.png", "Figure 8: Runtime request sequence", 600, 440),
        tbl(
          ["Node", "Module", "Action in live session"],
          [
            ["detect_product", "agents/diagnosis_graph.py", "Kept wm-001 from CRM (message already product-specific)"],
            ["run_diagnosis", "agents/tools.py → graph_rag.py", "Executed full GraphRAG Cypher pipeline"],
            ["format_response", "graph_rag.py format_diagnosis_response()", "Built markdown with evidence + provenance"],
            ["handle_escalation", "utils/escalation_store.py", "Turn 2 only: saved case 231311d2"],
          ],
          [1800, 3200, 4360]
        ),
        spacer(),

        pgBreak(),
        h2("8. GraphRAG — Turn-by-Turn Diagnosis Logic"),
        ...figure("10-demo-session-turn-flow.png", "Figure 10: Live session two-turn diagnosis flow", 620, 560),
        ...figure("04-graphrag-diagnosis.png", "Figure 4: GraphRAG diagnose() internal flow", 600, 520),

        h3("Turn 1: Machine does not spin during the final cycle"),
        pb("bullets", "match_symptoms: 1 match — wm-s01 (Machine does not spin…) score 1.0"),
        pb("bullets", "rank_failure_modes: wm-fm01 Worn Drive Belt, INDICATES confidence 0.94"),
        pb("bullets", "aggregate_confidence = 0.94 ÷ 1 symptom = 94%"),
        pb("bullets", "Escalation gate: 94% ≥ 65% threshold, no critical symptoms → should_escalate=false"),
        pb("bullets", "Status: Resolved at automated tier"),
        pb("bullets", "provenance_trail: 5 entries (Symptom, FailureMode, 2 Steps, 1 Resolution)"),

        h3("Turn 2: It also makes a loud grinding noise when it tries to spin"),
        pb("bullets", "match_symptoms: 2 matches — wm-s02 vibration (0.71) + wm-s01 spin (0.45)"),
        pb("bullets", "rank_failure_modes: wm-fm01 still #1 (total_confidence 0.94 from wm-s01 link only)"),
        pb("bullets", "aggregate_confidence = 0.94 ÷ 2 symptoms = 47%"),
        pb("bullets", "Escalation gate: 47% < 65% → should_escalate=true"),
        pb("bullets", "escalation_store saved case 231311d2 → Open Escalations count increased"),
        pb("bullets", "case_management POST → Service Cloud case CASE-4B881382 (integration sandbox)"),

        spacer(),
        h3("Why confidence dropped from 94% to 47%"),
        ...figure("11-confidence-dilution-model.png", "Figure 11: Confidence dilution model", 620, 360),
        ...figure("07-escalation-decision.png", "Figure 7: Escalation decision logic", 580, 400),
        code("aggregate_confidence = total_confidence / max(len(symptom_ids), 1)  # graph/graph_rag.py"),
        p(
          "The top failure mode did not change — Worn Drive Belt remained #1. What changed was the denominator: " +
            "adding a second matched symptom divides the same graph evidence across more symptoms, lowering aggregate confidence " +
            "below the 0.65 ESCALATION_CONFIDENCE_THRESHOLD in config/settings.py."
        ),
        spacer(),

        pgBreak(),
        h2("9. Response Payload — Field-by-Field Explanation"),
        h3("Matched Symptoms"),
        p("Neo4j query HAS_SYMPTOM + Python _text_similarity() with SYNONYMS expansion. Turn 2 added wm-s02 (medium severity)."),
        h3("Ranked Failure Modes"),
        p("Cypher aggregates INDICATES edge confidence per failure mode. wm-fm03 also linked to wm-s02 (0.85) but ranked lower overall."),
        h3("Diagnostic Steps"),
        p("HAS_DIAGNOSTIC_STEP relationship — ordered troubleshooting from service manual ETL."),
        h3("Historical Resolutions"),
        p("FSM closed work orders and claims merged at ETL. WO-FSM-88104 and wm-r01 confirm past belt replacements."),
        h3("Provenance Trail"),
        p("graph/provenance.py builds audit lines when ENABLE_PROVENANCE=true. Shown in UI expander and Source Traceability section."),
        h3("CRM Context JSON"),
        p("Runtime enrichment only — not stored in Neo4j. Binds session to registered asset and warranty metadata."),
        spacer(),

        h2("10. Escalation & Case Management Outcomes"),
        tbl(
          ["Artifact", "Storage", "Operational value"],
          [
            ["Agent escalation dossier", "data/escalations.json", "231311d2 — Human Agent Dashboard"],
            ["Service Cloud case record", "data/simulated_cases.json", "CASE-4B881382 — Case Management view"],
            ["Open Escalations metric", "ui/app.py", "Real-time agent workload indicator"],
          ],
          [2400, 2800, 4160]
        ),
        p("Escalation triggers (any one fires):"),
        pb("bullets", "Product unknown (not in your session)"),
        pb("bullets", "Any matched symptom severity = critical (not in washer turns)"),
        pb("bullets", "aggregate_confidence < 0.65 (Turn 2 — this fired)"),
        spacer(),

        pgBreak(),
        h2("11. Target Production Architecture"),
        ...figure("09-enterprise-production.png", "Figure 9: Target production deployment pattern", 620, 480),

        h2("12. Platform Endpoint Reference"),
        tbl(
          ["Component", "Endpoint", "Purpose"],
          [
            ["Self-Service Channel", "localhost:8501", "Customer & agent console"],
            ["Diagnostics API", "localhost:8080", "Omnichannel integration surface"],
            ["Enterprise Integration Layer", "localhost:8090", "CRM · Claims · Case Management (sandbox)"],
            ["Neo4j Bolt", "localhost:7687", "All GraphRAG Cypher"],
            ["Neo4j Browser", "localhost:7474", "Visual graph inspection"],
            ["ETL lineage", "data/lineage/etl_batches.jsonl", "Enterprise Systems tab"],
          ],
          [2800, 2400, 4160]
        ),
        spacer(),

        h2("13. Graphviz Source Files"),
        ...dotExcerpt("15-current-state-swimlane.dot"),
        ...dotExcerpt("16-future-state-swimlane.dot"),
        ...dotExcerpt("17-live-session-swimlane.dot"),
        ...dotExcerpt("18-etl-runtime-swimlane.dot"),
        p("All diagrams are version-controlled in docs/graphviz/*.dot. Render with:"),
        code("bash docs/graphviz/render_all.sh"),
        ...dotExcerpt("10-demo-session-turn-flow.dot"),
        ...dotExcerpt("11-confidence-dilution-model.dot"),
        ...dotExcerpt("12-streamlit-enterprise-layers.dot"),
        ...dotExcerpt("13-demo-response-field-map.dot"),
        ...dotExcerpt("14-etl-to-runtime.dot"),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUT_FILE, buffer);
  console.log(`Written: ${OUT_FILE}`);
});