/**
 * Customer Interaction Scripts & Presentation Runbook (Doc 08)
 * Stakeholder-ready presenter scripts — avoids demo/mock terminology.
 * Run: node docs/scripts/generate_demo_scripts_doc.js
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
const OUT_FILE = path.join(OUT_DIR, "08-Customer-Interaction-Scripts-and-Presentation-Runbook.docx");

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
const quote = (t) =>
  new Paragraph({
    spacing: { before: 80, after: 80 },
    indent: { left: 720 },
    children: [new TextRun({ text: t, italics: true, font: "Courier New", size: 22 })],
  });
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

function turnBlock(turnNum, uiSetup, customerMsg, presenterPoints) {
  return [
    h3(`Turn ${turnNum}`),
    p("UI setup:"),
    ...uiSetup.map((line) => pb("bullets", line)),
    p("Customer types:"),
    quote(customerMsg),
    p("Presenter highlights:"),
    ...presenterPoints.map((line) => pb("bullets", line)),
    spacer(),
  ];
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
                new TextRun({ text: "Customer Interaction Scripts & Presentation Runbook", italics: true, size: 18 }),
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
        h1("Customer Interaction Scripts & Presentation Runbook"),
        p("Enterprise Diagnostics GraphRAG Platform — Document 08"),
        p(
          "Turn-by-turn presenter scripts for stakeholder presentations on the pilot platform. Covers Neo4j GraphRAG, " +
            "enterprise CRM integration, warranty governance, provenance traceability, and governed human-agent escalation."
        ),
        spacer(),

        h2("Before You Begin (30 seconds)"),
        p("Open the self-service channel: http://localhost:8501 — Customer Chatbot tab"),
        p("Recommended opening statement:"),
        quote(
          "This is our enterprise warranty diagnostics platform. Customer interactions flow through a governed LangGraph workflow, " +
            "query an authoritative Neo4j knowledge graph via GraphRAG, enrich from CRM, validate warranty eligibility, " +
            "and escalate to human agents when policy requires — every answer carries a provenance trail to PIM, FSM, Claims, and CRM."
        ),
        p("Confirm platform health indicators:"),
        pb("bullets", "Neo4j: Connected — knowledge graph operational"),
        pb("bullets", "Mode: Enterprise — full integration path active"),
        pb("bullets", "Integration Services: Online — CRM, Claims, and Case Management available"),
        spacer(),

        h2("Registered Customer Quick Reference"),
        tbl(
          ["Customer", "Asset", "Product", "Recommended scenario message"],
          [
            ["Jane Martinez (CUST-10042)", "AST-WM-4421", "Washer wm-001", "Machine does not spin"],
            ["Robert Chen (CUST-10087)", "AST-DW-1180", "Dishwasher dw-001", "Dishes wet and cold after cycle"],
            ["Jane Martinez (CUST-10042)", "AST-MW-7702", "Microwave mw-001", "Arcing inside, food stays cold"],
          ],
          [2200, 1600, 1600, 3960]
        ),
        spacer(),

        pgBreak(),
        h2("Script A — Full Platform Presentation (~12–15 min)"),
        p("Recommended for executive and architecture audiences. Covers CRM integration, warranty governance, escalation policy, agent operations, and knowledge-engineering lineage."),

        h3("Act 1 — CRM-bound, in-warranty diagnosis"),
        ...turnBlock(
          1,
          [
            "Expand CRM Customer Context",
            "Customer: Jane Martinez (CUST-10042)",
            "Asset: AST-WM-4421 — wm-001",
            "Appliance: Auto-detect (CRM supplies product)",
          ],
          "Machine does not spin during the final cycle",
          [
            "Green CRM banner: customer, asset, product wm-001",
            "Warranty: Eligible",
            "Response names Front Load Washing Machine 8kg",
            "Top failure mode: Worn Drive Belt",
            "Open Diagnosis Details → provenance_trail (PIM/FSM sources)",
            "If escalated: note low-confidence rule (65% threshold)",
          ]
        ),
        ...turnBlock(
          2,
          ["Keep same CRM context from Turn 1"],
          "It also makes a loud grinding noise when it tries to spin",
          [
            "Graph adds symptoms and may adjust failure ranking",
            "Evidence list grows in expander",
            "Multi-symptom cases often escalate — expected behavior",
          ]
        ),

        h3("Act 2 — Safety-critical microwave (mandatory escalation)"),
        ...turnBlock(
          3,
          [
            "CRM: Jane Martinez (CUST-10042)",
            "Asset: AST-MW-7702 — mw-001",
            "Appliance: Auto-detect",
          ],
          "Microwave runs but food stays cold, and I see arcing inside",
          [
            "Product: Convection Microwave 25L",
            "Critical severity symptom matched",
            "Escalation: critical symptom — human review required",
            "Case ID appears in response",
            "Service Cloud case created via Enterprise Integration Layer",
            "Open Provenance Trail in diagnosis expander",
          ]
        ),
        p("Presenter line:"),
        quote("Safety-critical symptoms bypass automated resolution — a hard enterprise rule, not LLM judgment."),
        spacer(),

        h3("Act 3 — Dishwasher with second customer"),
        ...turnBlock(
          4,
          [
            "CRM: Robert Chen (CUST-10087)",
            "Asset: AST-DW-1180 — dw-001",
            "Appliance: Auto-detect",
          ],
          "Dishwasher leaves dishes wet and cold after the cycle",
          [
            "CRM binds Robert's registered dishwasher",
            "Warranty eligible",
            "Top failure: Heating Element Failure",
            "Confidence ~45% → escalates (below 65% threshold)",
            "Shows: clear top failure can still trigger human review",
          ]
        ),

        pgBreak(),
        h3("Act 4 — Unknown appliance"),
        ...turnBlock(
          5,
          ["CRM: None", "Appliance: Auto-detect"],
          "Something in my kitchen is broken, I'm not sure what it is",
          [
            "Product not identified",
            "Escalation: Could not identify appliance type",
            "Demonstrates guardrail when graph cannot anchor diagnosis",
          ]
        ),

        h3("Act 5 — Human Agent Dashboard"),
        p("Tab: Human Agent Dashboard"),
        p("Presenter line:"),
        quote(
          "Every escalated case lands here with the full graph payload — symptoms, failure modes, confidence, " +
            "provenance — so agents don't start from zero."
        ),
        pb("numbers", "Open the washer or microwave case from Turns 1–3"),
        pb("numbers", "Show Provenance Trail"),
        pb("numbers", "Click Mark In Progress on one case"),
        pb("numbers", "Show raw JSON for audit/compliance story"),
        spacer(),

        h3("Act 6 — Knowledge Graph"),
        p("Tab: Knowledge Graph"),
        p("Presenter line:"),
        quote(
          "This is what's in Neo4j after enterprise ETL — products, failure modes, and diagnostic steps merged " +
            "from PIM, field service, and claims history."
        ),
        pb("bullets", "wm-001 — drive belt, drain pump failures"),
        pb("bullets", "dw-001 — heating element, wash motor"),
        pb("bullets", "mw-001 — magnetron, door switch"),
        spacer(),

        h3("Act 7 — Enterprise Systems"),
        p("Tab: Enterprise Systems"),
        pb("bullets", "Summary banner — latest successful pipeline steps"),
        pb("bullets", "knowledge_etl → smoke_validation → staging_promotion chain"),
        pb("bullets", "Optional: Show full pipeline history for earlier failed runs"),
        pb("bullets", "Case Management — Service Cloud handoff records from CRM-bound escalations"),
        pb("bullets", "Pipeline Commands block for operators"),
        spacer(),

        h3("Act 8 — REST API (optional)"),
        p("Presenter line:"),
        quote("The same logic is exposed as an enterprise API for IVR, mobile app, or Salesforce integration."),
        code(
          'curl -X POST http://localhost:8080/diagnose \\\n' +
            '  -H "Content-Type: application/json" \\\n' +
            '  -d \'{"message":"washer won\'"\'"\'t spin","customer_id":"CUST-10042","asset_id":"AST-WM-4421"}\''
        ),
        pb("bullets", "Point out in JSON: crm_context, warranty, provenance_trail, escalated"),
        spacer(),

        pgBreak(),
        h2("Script B — Executive Briefing (~5 min)"),
        tbl(
          ["Step", "UI setup", "Customer message", "Highlight"],
          [
            ["1", "Jane + AST-WM-4421", "Machine does not spin", "CRM + warranty + provenance"],
            ["2", "Jane + AST-MW-7702", "Microwave arcing, food stays cold", "Critical escalation"],
            ["3", "Human Agent Dashboard tab", "—", "Open latest case"],
            ["4", "Enterprise Systems tab", "—", "Lineage + CCaaS cases"],
          ],
          [800, 2400, 3160, 3000]
        ),
        spacer(),

        h2("Script C — Feature-Specific Mini Scripts"),
        h3("C1 — Provenance only"),
        pb("bullets", "UI: No CRM · Appliance: Convection Microwave 25L"),
        quote("Microwave convection fan not running"),
        pb("bullets", "Open Diagnosis Details → Provenance Trail"),
        spacer(),

        h3("C2 — Graph evidence + diagnostic steps"),
        pb("bullets", "UI: No CRM · Auto-detect"),
        quote("Dishwasher grinding noise during wash"),
        pb("bullets", "Show failure modes and diagnostic steps in expander"),
        spacer(),

        h3("C3 — Pre-selected product"),
        pb("bullets", "UI: No CRM · Appliance: Front Load Washing Machine 8kg"),
        quote("Drum does not spin during final cycle"),
        pb("bullets", "Shows explicit product binding without CRM"),
        spacer(),

        h2("Presenter Cheat Sheet"),
        tbl(
          ["Presentation moment", "Recommended narrative"],
          [
            ["CRM banner", "Runtime enrichment from Salesforce — no manual product lookup."],
            ["Warranty metric", "Claims policy gate before we run diagnosis."],
            ["Provenance trail", "Every answer is traceable to source systems for compliance."],
            ["Escalation", "Three triggers: unknown product, critical symptom, confidence < 65%."],
            ["Dashboard", "Human-in-the-loop with full graph context, not a chat transcript."],
            ["Enterprise tab", "Same pipelines you'd run in POC → MVP → production."],
          ],
          [2800, 6560]
        ),
        spacer(),

        h2("Recommended Presentation Sequence"),
        pb("numbers", "CRM + warranty (Jane / washer) — enterprise integration"),
        pb("numbers", "Critical microwave — safety escalation + CCaaS"),
        pb("numbers", "Human Agent Dashboard — agent experience"),
        pb("numbers", "Enterprise Systems — pipelines + lineage"),
        pb("numbers", "Knowledge Graph — ontology depth"),
        pb("numbers", "API curl — integration story"),
        spacer(),

        h2("Escalation Rules Reference"),
        pb("bullets", "Escalate when product cannot be detected"),
        pb("bullets", "Escalate when any matched symptom has critical severity"),
        pb("bullets", "Escalate when diagnosis confidence is below 65% (ESCALATION_CONFIDENCE_THRESHOLD)"),
        p("Example: washer multi-symptom query may rank the correct failure mode but still escalate at ~47% confidence."),
        spacer(),

        h2("Service URLs"),
        tbl(
          ["Service", "URL"],
          [
            ["Streamlit UI", "http://localhost:8501"],
            ["Diagnostics REST API", "http://localhost:8080/docs"],
            ["Enterprise Integration Layer (sandbox)", "http://localhost:8090/docs"],
            ["Neo4j Browser", "http://localhost:7474 (neo4j / password)"],
          ],
          [3200, 6160]
        ),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUT_FILE, buffer);
  console.log(`Written: ${OUT_FILE}`);
});