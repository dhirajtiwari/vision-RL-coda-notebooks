/**
 * Document 13 — Graph Visualization, Industry Practices & Architecture Rationale
 * Explains Neo4j tutorial patterns, LangGraph vs Node.js, and what we built.
 * Run: node docs/scripts/generate_graph_visualization_guide_doc.js
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
const OUT_FILE = path.join(
  OUT_DIR,
  "13-Graph-Visualization-Industry-Practices-and-Architecture-Rationale.docx"
);

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
      run: { size: 32, bold: true, color: "1F4E79" },
      paragraph: { spacing: { before: 240, after: 120 } },
    },
    {
      id: "Heading2",
      name: "Heading 2",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 28, bold: true, color: "2E75B6" },
      paragraph: { spacing: { before: 200, after: 100 } },
    },
  ],
};

async function main() {
  const doc = new Document({
    numbering,
    styles,
    sections: [
      {
        properties: { page: PAGE },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: "Diagnostics GraphRAG — Doc 13", italics: true, size: 20 })],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })],
              }),
            ],
          }),
        },
        children: [
          h1("Graph Visualization, Industry Practices & Architecture Rationale"),
          p(
            "This document answers a common question after watching Neo4j tutorials: why do those demos show animated ER diagrams, mind-map style relationship graphs, and live graph updates when Cypher runs — and how does our warranty diagnostics platform compare?"
          ),
          p("Audience: architects, graph developers, and stakeholders reviewing the demo."),

          h2("1. What Neo4j tutorials typically show"),
          p(
            "Most Neo4j learning content emphasizes graph-native exploration, not just query results in tables. The patterns you noticed fall into four categories:"
          ),
          tbl(
            ["Pattern", "Tool / technique", "What the user sees"],
            [
              [
                "ER / data model diagram",
                "Arrows.app, Neo4j Data Modeling, Graphviz",
                "Node labels, relationship types, key properties before data is loaded",
              ],
              [
                "Interactive property graph",
                "Neo4j Browser, Bloom, neovis.js, PyVis",
                "Force-directed nodes you can drag, zoom, and expand",
              ],
              [
                "Query-synchronized graph",
                "RETURN p, r, m or path queries in Browser",
                "Every Cypher result renders as nodes and edges on canvas",
              ],
              [
                "Schema + instance together",
                "Bloom perspectives, Browser styling by label",
                "Color/shape per label (Product, Person, Order, etc.)",
              ],
            ],
            [2200, 2800, 4360]
          ),

          h2("2. Critical review — what our demo had vs. industry practice"),
          h3("Before this alignment (gaps a senior graph developer would flag)"),
          tbl(
            ["Industry practice", "Our demo (prior)", "Risk / impact"],
            [
              ["Live graph render on query", "Text lists + JSON only", "Hard to explain GraphRAG reasoning to business users"],
              ["ER ontology visible in app", "Static Graphviz in docs/", "Schema knowledge buried in Word docs"],
              ["Subgraph API {nodes, edges}", "REST returned nested dicts only", "No embeddable viz for portals"],
              ["Parts linked in graph", ":Part nodes orphaned", "Incomplete ontology; parts from JSON bypass"],
              ["Neo4j Browser deep-link", "Manual URL only", "Analysts re-type Cypher"],
            ],
            [2800, 3200, 3360]
          ),

          h3("What we already did well"),
          pb("bullets", "Correct property-graph ontology for warranty diagnosis (Product → Symptom → FailureMode)."),
          pb("bullets", "Confidence-weighted INDICATES edges — the right pattern for ranked reasoning."),
          pb("bullets", "Idempotent MERGE loader, provenance metadata, enterprise ETL story."),
          pb("bullets", "GraphRAG with explainable evidence[] and provenance_trail on every answer."),
          pb("bullets", "Static architecture diagrams in docs/graphviz/ (20 Graphviz sources)."),

          pgBreak(),
          h2("3. What we built to align with industry practice"),
          p("The platform now includes embedded interactive graph visualization in Streamlit and graph JSON APIs."),
          tbl(
            ["Feature", "Location", "Neo4j tutorial equivalent"],
            [
              ["ER ontology view", "Streamlit → Knowledge Graph → Ontology tab", "Arrows / data modeling diagram"],
              ["Product neighborhood graph", "Knowledge Graph → Product Graph tab", "Browser: MATCH (p)-[*1..2]-(n)"],
              ["Diagnosis reasoning subgraph", "Chat → Diagnosis Graph expander", "Browser: RETURN p,s,ind,fm"],
              ["Cypher Explorer", "Knowledge Graph → Cypher Explorer tab", "Run query → see graph update"],
              ["Neo4j Browser Cypher copy", "Under each diagnosis graph", "Same query in :7474"],
              ["Graph REST APIs", "GET /graph/ontology, /graph/product/{id}, /graph/diagnosis-subgraph", "neovis.js / custom UI"],
            ],
            [2600, 3600, 3160]
          ),
          p("Implementation: graph/graph_visualization.py (PyVis force-directed HTML) + Streamlit components.html embed."),

          h3("Schema fix: REQUIRES_PART"),
          p(
            "Parts were MERGE'd but never connected. We added (:FailureMode)-[:REQUIRES_PART]->(:Part) in populate_graph.py, synthetic data, PIM fixtures, and GraphRAG now queries parts via Cypher (with JSON fallback)."
          ),

          h2("4. Why LangGraph — and why not Node.js?"),
          p(
            "These are two different questions. LangGraph is not an alternative to Node.js; they solve different problems."
          ),
          tbl(
            ["Technology", "Role in this project", "Why chosen"],
            [
              [
                "Python + FastAPI + Streamlit",
                "Runtime application",
                "Neo4j official driver, LangGraph/LangChain ecosystem, GraphRAG in one process",
              ],
              [
                "LangGraph",
                "Agent workflow orchestration",
                "Multi-step diagnosis pipeline with typed shared state; future LLM node insertion",
              ],
              [
                "Node.js",
                "docs/scripts only (docx, pptx)",
                "Not used for graph or API — optional doc generation tooling",
              ],
            ],
            [2200, 3600, 3560]
          ),

          h3("LangGraph workflow (agents/diagnosis_graph.py)"),
          p("detect_product → run_diagnosis → format_response → handle_escalation → END"),
          pb("bullets", "Each step is a testable node with AgentState — auditable for enterprise governance."),
          pb("bullets", "format_response can swap template text for an LLM without changing GraphRAG."),
          pb("bullets", "Escalation persistence is a distinct node — mirrors case-management handoff."),
          pb("bullets", "run_diagnosis_simple() bypasses LangGraph for unit tests — graph logic is not locked inside the framework."),

          p(
            "Honest assessment: for this demo, LangGraph is structural scaffolding over ~4 function calls. The value is production-shaped boundaries, not graph algorithms. Neo4j stores knowledge; LangGraph orchestrates the agent pipeline."
          ),

          pgBreak(),
          h2("5. Python vs Node.js for graph applications — decision record"),
          tbl(
            ["Criterion", "Python (our choice)", "Node.js alternative"],
            [
              ["Neo4j driver maturity", "Official neo4j Python driver 5.x", "neo4j-driver npm package — equally mature"],
              ["GraphRAG / LangGraph", "Native LangChain ecosystem", "Would need custom orchestration or TS ports"],
              ["Streamlit demo UI", "Same language as graph layer", "Would need React + separate API"],
              ["Enterprise ML teams", "Common for data/ML pipelines", "Common for web frontends"],
              ["When Node.js wins", "—", "React SPA + neovis.js + Express API shop standard"],
            ],
            [2800, 3280, 3280]
          ),
          p(
            "A Node.js + neovis.js stack is a valid production pattern for customer-facing portals. We chose Python because this demo bundles ETL, GraphRAG, agent orchestration, and Streamlit in one repo — minimizing integration surface for an enterprise proof-of-concept."
          ),

          h2("6. How to use the new visualization features"),
          pb("bullets", "Start demo: ./run_enterprise_demo.sh — open http://localhost:8501"),
          pb("bullets", "Customer Chatbot tab → ask a question → expand 'Diagnosis Graph (interactive)'"),
          pb("bullets", "Knowledge Graph tab → Ontology / Product Graph / Cypher Explorer"),
          pb("bullets", "Neo4j Browser: http://localhost:7474 — paste Cypher from diagnosis expander"),
          pb("bullets", "API: GET http://localhost:8080/graph/ontology and /graph/product/wm-001"),

          h2("7. Remaining gaps vs. full Neo4j product suite"),
          tbl(
            ["Capability", "Status", "Production path"],
            [
              ["Neo4j Bloom", "Not bundled (commercial)", "Bloom for business-user exploration"],
              ["Real-time graph sync on every keystroke", "On diagnosis / explicit query", "WebSocket subgraph stream"],
              ["APOC subgraph export", "APOC enabled in Docker, unused", "apoc.path.subgraphNodes for large graphs"],
              ["Formal OWL/RDF ontology", "Pydantic schema only", "Add if semantic interoperability required"],
            ],
            [2800, 3280, 3280]
          ),

          h2("8. Key source files"),
          pb("bullets", "graph/graph_visualization.py — subgraph payloads + PyVis renderer"),
          pb("bullets", "graph/graph_rag.py — Cypher diagnosis + parts via REQUIRES_PART"),
          pb("bullets", "ui/app.py — embedded interactive graphs in chat and explorer"),
          pb("bullets", "api/main.py — /graph/* REST endpoints"),
          pb("bullets", "agents/diagnosis_graph.py — LangGraph orchestration"),
          pb("bullets", "docs/graphviz/05-neo4j-ontology.dot — static ER reference"),
        ],
      },
    ],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT_FILE, buffer);
  console.log(`✅ Wrote ${OUT_FILE}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});