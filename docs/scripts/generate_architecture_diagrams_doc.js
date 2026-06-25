/**
 * Architecture Diagrams Document — Graphviz sources + rendered figures
 * Run: node docs/scripts/generate_architecture_diagrams_doc.js
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
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

const ROOT = path.join(__dirname, "..", "..");
const OUT_DIR = path.join(__dirname, "..");
const GVIZ_DIR = path.join(OUT_DIR, "graphviz");
const PNG_DIR = path.join(GVIZ_DIR, "rendered", "png");

const PAGE = {
  size: { width: 12240, height: 15840 },
  margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
};

const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const p = (t) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun(t)] });
const pb = (t) =>
  new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun(t)],
  });
const code = (t) =>
  new Paragraph({
    spacing: { before: 60, after: 60 },
    shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
    children: [new TextRun({ text: t, font: "Courier New", size: 18 })],
  });
const pgBreak = () => new Paragraph({ children: [new PageBreak()] });

function figure(filename, caption, width = 620, height = 460) {
  const fp = path.join(PNG_DIR, filename);
  if (!fs.existsSync(fp)) {
    return [p(`[Diagram not rendered: ${filename}. Run docs/graphviz/render_all.sh]`)];
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

function dotSource(name) {
  const fp = path.join(GVIZ_DIR, name);
  if (!fs.existsSync(fp)) return [];
  const src = fs.readFileSync(fp, "utf8").trim();
  const excerpt = src.length > 1200 ? src.slice(0, 1200) + "\n// ... (see docs/graphviz/" + name + ")" : src;
  return [
    h3(`Graphviz Source: ${name}`),
    code(excerpt),
  ];
}

const diagrams = [
  {
    id: "01",
    file: "01-system-context.png",
    dot: "01-system-context.dot",
    title: "Figure 1: Enterprise System Context",
    desc: "C4-style context diagram showing appliance owners, contact center agents, the diagnostics platform modules (ui/app.py, LangGraph, GraphRAG, ETL, populate_graph, Neo4j), and upstream enterprise systems (PIM, FSM, Claims, CRM). Dashed lines indicate production targets not fully wired in the demo.",
    height: 520,
  },
  {
    id: "02",
    file: "02-module-block.png",
    dot: "02-module-block.dot",
    title: "Figure 2: Repository Module Block Diagram",
    desc: "Block diagram of all major Python modules and data files in diagnostic-chatbot, grouped by presentation, orchestration, GraphRAG, knowledge, and infrastructure layers. Arrows show compile-time/runtime dependencies.",
    height: 380,
  },
  {
    id: "03",
    file: "03-langgraph-workflow.png",
    dot: "03-langgraph-workflow.dot",
    title: "Figure 3: LangGraph Agent Workflow",
    desc: "Exact workflow from agents/diagnosis_graph.py: linear StateGraph with four nodes (detect_product → run_diagnosis → format_response → handle_escalation) and AgentState fields passed between nodes.",
    height: 480,
  },
  {
    id: "04",
    file: "04-graphrag-diagnosis.png",
    dot: "04-graphrag-diagnosis.dot",
    title: "Figure 4: GraphRAG diagnose() Flow",
    desc: "Internal flow of graph/graph_rag.py diagnose() function showing all five Cypher queries, Python-only steps (symptom matching, escalation decision, parts from JSON), and DiagnosisResult output.",
    height: 520,
  },
  {
    id: "05",
    file: "05-neo4j-ontology.png",
    dot: "05-neo4j-ontology.dot",
    title: "Figure 5: Neo4j Ontology & wm-001 Instance",
    desc: "Knowledge graph schema (node labels, relationship types, unique constraints from populate_graph.py) plus concrete wm-001 instance with INDICATES confidence weights from data/synthetic_diagnosis_data.json.",
    height: 500,
  },
  {
    id: "06",
    file: "06-etl-pipeline.png",
    dot: "06-etl-pipeline.dot",
    title: "Figure 6: Enterprise ETL Pipeline",
    desc: "Extract-Transform-Load flow from graph/enterprise_pipeline/pipeline.py: four connectors → OntologyBuilder → validated JSON → populate_graph.py → Neo4j.",
    height: 320,
  },
  {
    id: "07",
    file: "07-escalation-decision.png",
    dot: "07-escalation-decision.dot",
    title: "Figure 7: Escalation Decision Logic",
    desc: "Decision diamond flow from graph/graph_rag.py: escalate if product unknown, any critical symptom, or confidence below 0.65 (config/settings.py). Escalated cases saved via utils/escalation_store.py to Human Agent Dashboard.",
    height: 480,
  },
  {
    id: "08",
    file: "08-runtime-sequence.png",
    dot: "08-runtime-sequence.dot",
    title: "Figure 8: Runtime Request Sequence",
    desc: "Thirteen-step runtime sequence from customer chat message through Streamlit, LangGraph, tools, GraphRAG, Neo4j, optional escalation, and agent dashboard review.",
    height: 400,
  },
  {
    id: "09",
    file: "09-enterprise-production.png",
    dot: "09-enterprise-production.dot",
    title: "Figure 9: Enterprise Production Target",
    desc: "Target-state architecture from implementation roadmap: scheduled ETL with provenance, staging/production Neo4j promotion, FastAPI runtime, CRM enrichment, and CCaaS case handoff. Not fully implemented in demo.",
    height: 480,
  },
];

async function main() {
  console.log("Rendering Graphviz diagrams...");
  execSync("bash docs/graphviz/render_all.sh", { cwd: ROOT, stdio: "inherit" });

  const children = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 300 },
      children: [
        new TextRun({ text: "Architecture Diagrams", bold: true, size: 52, color: "1F4E79" }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [
        new TextRun({
          text: "Graphviz & Block Diagrams — Enterprise Diagnostics Chatbot",
          size: 28,
          color: "2E75B6",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [new TextRun({ text: "Accurate diagrams grounded in diagnostic-chatbot codebase", size: 22, italics: true })],
    }),
    p("Document Version: 1.0 | Date: June 25, 2026"),
    p(
      "This document contains nine architecture diagrams rendered from Graphviz DOT source files in docs/graphviz/. Each diagram maps to actual modules, functions, and data flows in the repository. SVG and PNG renders are in docs/graphviz/rendered/."
    ),
    h2("How to Regenerate"),
    code(
      "bash docs/graphviz/render_all.sh\nnode docs/scripts/generate_architecture_diagrams_doc.js"
    ),
    h2("Diagram Index"),
    ...diagrams.flatMap((d) => [pb(`${d.title} — ${d.dot}`)]),
    pgBreak(),

    h1("1. Diagram Gallery"),
  ];

  for (const d of diagrams) {
    children.push(h2(d.title));
    children.push(p(d.desc));
    children.push(...figure(d.file, d.title, 620, d.height));
    children.push(...dotSource(d.dot));
    children.push(pgBreak());
  }

  children.push(h1("2. Graphviz DOT File Reference"));
  p("All source files live in docs/graphviz/. Edit any .dot file and re-run render_all.sh to update figures.");
  for (const d of diagrams) {
    children.push(pb(`${d.dot} → rendered/png/${d.file.replace(".png", ".png")} + rendered/svg/`));
  }

  children.push(pgBreak());
  children.push(h1("3. Module-to-Diagram Mapping"));
  p("Quick reference: which codebase file each diagram documents.");
  const mapping = [
    ["01-system-context", "Full platform + enterprise boundary"],
    ["02-module-block", "All packages under config/, graph/, agents/, ui/, utils/, data/"],
    ["03-langgraph-workflow", "agents/diagnosis_graph.py — build_diagnosis_graph()"],
    ["04-graphrag-diagnosis", "graph/graph_rag.py — diagnose(), list_products(), match_symptoms(), rank_failure_modes()"],
    ["05-neo4j-ontology", "graph/populate_graph.py + data/synthetic_diagnosis_data.json"],
    ["06-etl-pipeline", "graph/enterprise_pipeline/pipeline.py + transformers/ontology_builder.py"],
    ["07-escalation-decision", "graph/graph_rag.py lines 239–245 + utils/escalation_store.py"],
    ["08-runtime-sequence", "ui/app.py → run_diagnosis() end-to-end"],
    ["09-enterprise-production", "Target architecture per docs/05-Enterprise-Implementation-Roadmap"],
  ];
  for (const [file, desc] of mapping) {
    children.push(pb(`${file}: ${desc}`));
  }

  const doc = new Document({
    styles: {
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
    },
    numbering: {
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
    },
    sections: [
      {
        properties: { page: PAGE },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                children: [
                  new TextRun({ text: "Architecture Diagrams — Graphviz & Block Diagrams", size: 18, color: "666666" }),
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

  const out = path.join(OUT_DIR, "06-Architecture-Diagrams-Graphviz-and-Block-Diagrams.docx");
  fs.writeFileSync(out, await Packer.toBuffer(doc));
  console.log(`Created: ${out}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});