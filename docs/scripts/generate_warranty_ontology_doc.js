/**
 * Document 14 — Enterprise Warranty Diagnosis Ontology & Industry Alignment
 * Run: node docs/scripts/generate_warranty_ontology_doc.js
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require("docx");

const OUT_FILE = path.join(__dirname, "..", "14-Enterprise-Warranty-Diagnosis-Ontology-and-Industry-Alignment.docx");
const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } };
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const p = (t) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun(t)] });
const pb = (ref, t) => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80 }, children: [new TextRun(t)] });
const pgBreak = () => new Paragraph({ children: [new PageBreak()] });

function tbl(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        children: headers.map((h, i) => new TableCell({
          borders, width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: "1F4E79", type: ShadingType.CLEAR }, margins: cellMargins,
          children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: "FFFFFF" })] })],
        })),
      }),
      ...rows.map((row) => new TableRow({
        children: row.map((c, i) => new TableCell({
          borders, width: { size: colWidths[i], type: WidthType.DXA }, margins: cellMargins,
          children: [new Paragraph({ children: [new TextRun(String(c))] })],
        })),
      })),
    ],
  });
}

const numbering = {
  config: [{
    reference: "bullets",
    levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
  }],
};

async function main() {
  const doc = new Document({
    numbering,
    styles: { default: { document: { run: { font: "Arial", size: 24 } } } },
    sections: [{
      properties: { page: PAGE },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "Doc 14 — Warranty Diagnosis Ontology", italics: true, size: 20 })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] }) },
      children: [
        h1("Enterprise Warranty Diagnosis Ontology & Industry Alignment"),
        p("This document maps the full warranty-claims reasoning chain — product/model → symptoms → diagnosis → impacted components → parts prediction — to industry practice and research."),

        h2("1. The chain you need (and what we now model)"),
        p("Enterprise warranty diagnosis is not a single hop Symptom → FailureMode. The operational chain is:"),
        p("Asset/Serial → Product/Model/SKU → Customer symptoms + error codes → Ranked failure modes (diagnosis) → Targeted troubleshooting steps → Impacted BOM components → Predicted parts → Warranty/claim precedent."),
        tbl(
          ["Step", "Neo4j entities", "Relationship path", "Status in platform"],
          [
            ["Identify unit", "Asset, SKU, Model, Product", "Asset-[:INSTANCE_OF]->Product, Asset-[:BOUND_TO_SKU]->SKU", "Implemented"],
            ["Capture issue", "Symptom, ErrorCode", "Product-[:HAS_SYMPTOM|HAS_ERROR_CODE]->…", "Implemented"],
            ["Diagnose", "FailureMode", "Symptom-[:INDICATES]->FM, ErrorCode-[:INDICATES]->FM", "Implemented"],
            ["Troubleshoot", "DiagnosticStep", "Step-[:CONFIRMS]->FailureMode", "Implemented (FM-filtered steps)"],
            ["Locate impact", "Component", "FM-[:IMPACTS_COMPONENT]->Component-[:REALIZED_BY]->Part", "Implemented"],
            ["Predict parts", "Part", "FM-[:REQUIRES_PART {qty, probability}]->Part, SKU-[:COMPATIBLE_WITH]->Part", "Implemented (parts_predictor.py)"],
            ["Warranty context", "Claim, WarrantyPolicy", "Claim-[:USED_PART]->Part, Asset-[:COVERED_BY]->Policy", "Implemented"],
          ],
          [1800, 2200, 3200, 2160]
        ),

        h2("2. What we had before (the gap you identified)"),
        p("The original ontology stopped at Product → Symptom → FailureMode. Parts existed as orphan nodes loaded from JSON. CRM assets and claims lived outside Neo4j. Troubleshooting steps were product-flat with no link to diagnosis. There was no parts predictor chain through BOM components or SKU fit."),
        pb("bullets", "No model/SKU hierarchy — serial numbers unused in graph reasoning"),
        pb("bullets", "No Component/BOM — could not answer 'which subsystem is impacted?'"),
        pb("bullets", "No DiagnosticStep → FailureMode links — troubleshooting did not narrow diagnosis"),
        pb("bullets", "No ErrorCode entities — E21 was text inside a symptom description"),
        pb("bullets", "No Claim nodes — warranty precedent invisible to GraphRAG"),

        pgBreak(),
        h2("3. How industry does this"),
        tbl(
          ["Source / practice", "What they model", "Relevance to warranty diagnosis"],
          [
            ["FMEA / ISO 14224", "Failure mode, effect, detection, severity", "Symptom-FM confidence weights, safety notes, escalation"],
            ["SAP PLM / OpenBOM KG", "Product → BOM → Part hierarchy", "Component-[:REALIZED_BY]->Part, SKU compatibility"],
            ["Salesforce Asset + Service Cloud", "Asset serial → product model → entitlement", "Asset-[:INSTANCE_OF]->Product, warranty gate"],
            ["Guidewire ClaimCenter", "Claim → failure → parts used", "Claim-[:CONFIRMED|USED_PART] for precedent"],
            ["Bruviti Parts Prediction", "Symptom + product + history → ranked parts", "parts_predictor.py multi-source ranking"],
            ["Home Appliance Fault KG (MDPI 2025)", "Dual-strategy KG for fault domain", "Symptom/error-code/FM triangle"],
            ["Equipment Fault Diagnosis KG", "KG-driven fault diagnosis in manufacturing", "GraphRAG multi-hop ranking pattern"],
            ["Warranty data mining (Loughborough)", "Ontology + warranty returns for design", "HistoricalResolution + Claim precedent"],
          ],
          [2800, 3280, 3280]
        ),

        h2("4. Parts predictor design"),
        p("graph/parts_predictor.py ranks parts from four graph evidence sources, merged by part_id:"),
        pb("bullets", "REQUIRES_PART — primary repair part with probability and quantity on the edge"),
        pb("bullets", "BOM_COMPONENT — FailureMode impacts Component realized by Part"),
        pb("bullets", "SKU_FIT — asset-bound SKU compatibility filter"),
        pb("bullets", "CLAIM_PRECEDENT — prior approved claims boost confidence"),
        p("When a CRM asset is selected, diagnose() passes asset_id → resolves SKU → enables SKU-aware prediction."),

        h2("5. Key files"),
        pb("bullets", "graph/warranty_catalog_extensions.py — model, SKU, BOM, assets, claims"),
        pb("bullets", "graph/populate_graph.py — enterprise MERGE loader"),
        pb("bullets", "graph/graph_rag.py — full diagnosis chain with asset_id"),
        pb("bullets", "graph/parts_predictor.py — ranked parts prediction"),
        pb("bullets", "integrations/warranty_eligibility.py — parts cost vs policy cap"),

        h2("6. Remaining production gaps"),
        pb("bullets", "Part supersession chains (SUPERSEDES) — not yet modeled"),
        pb("bullets", "Full diagnostic decision trees (NEXT_STEP with branch conditions)"),
        pb("bullets", "LLM-assisted symptom normalization (canonical symptom ontology)"),
        pb("bullets", "Real-time learning from closed claims back into INDICATES weights"),
        pb("bullets", "Multi-language service manual ingestion at scale"),
      ],
    }],
  });
  fs.writeFileSync(OUT_FILE, await Packer.toBuffer(doc));
  console.log(`✅ Wrote ${OUT_FILE}`);
}

main().catch((e) => { console.error(e); process.exit(1); });