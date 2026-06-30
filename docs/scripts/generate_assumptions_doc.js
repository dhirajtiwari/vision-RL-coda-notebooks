/**
 * Document 11 — Enterprise Delivery Assumptions, Dependencies & Open Questions
 * Senior Solution Architect register for pre-discovery / early-engagement stage.
 * Run: node docs/scripts/generate_assumptions_doc.js
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
const OUT_FILE = path.join(OUT_DIR, "11-Enterprise-Delivery-Assumptions-Dependencies-and-Open-Questions.docx");

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
          text: "Enterprise Delivery Assumptions",
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
          text: "Dependencies, Open Questions & Pre-Discovery Register",
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
          text: "Warranty Diagnostics GraphRAG Platform — Reference Solution",
          size: 24,
          italics: true,
        }),
      ],
    }),
    tbl(
      ["Document", "Version", "Date", "Author Role", "Status", "Classification"],
      [
        [
          "11 — Assumptions & Dependencies Register",
          "1.1",
          "June 25, 2026",
          "Senior Solution Architect",
          "Nothing Validated — All Hypothesis",
          "Internal — Program Planning",
        ],
      ],
      [2000, 800, 1200, 2000, 1600, 1760]
    ),
    spacer(),
    p(
      "CRITICAL: At the time of writing, nothing in this program is validated. Not the client's enterprise landscape. Not the product catalog. Not the data sources. Not the contact center model. And not the reference demo in this repository — the demo is a design illustration built on synthetic data and mock systems. It does not confirm that the proposed architecture will work for this client, at this scale, with real data, or that any timeline or estimate in Documents 01, 05, or 10 is achievable."
    ),
    pgBreak(),

    h1("1. Purpose of This Document"),
    p(
      "The solution architecture, enterprise integration model, knowledge engineering approach, and POC → MVP → Production roadmap were authored before any discovery with the client. A reference demo exists (three synthetic appliance families, mock CRM/PIM/FSM/Claims, Neo4j, LangGraph, Streamlit) to help stakeholders visualize one possible implementation — that is all it is. A working local demo is not evidence of enterprise feasibility, diagnostic accuracy, integration viability, or operational acceptance."
    ),
    p("This register exists to:"),
    pb("bullets", "State clearly that every item — including the demo — is hypothesis until independently validated with the client"),
    pb("bullets", "Prevent the demo from being mistaken for confirmation of architecture, scope, or roadmap"),
    pb("bullets", "List what we do not know and what we are assuming in the absence of facts"),
    pb("bullets", "Define mandatory client and delivery dependencies before any phase commitment"),
    pb("bullets", "Provide a discovery and validation path — starting from zero validated assumptions"),
    p(
      "Documents 01, 05, and 10 are reference designs for discussion. They are not delivery specifications. Section 14 (Acknowledgment) records that stakeholders understand this — it does not mean any assumption has been validated."
    ),

    h1("2. Validation Status — Nothing Confirmed"),
    tbl(
      ["Category", "Status Today", "What Exists Instead"],
      [
        ["Client enterprise architecture", "Not validated", "Illustrative integration diagrams only"],
        ["Client product catalog & knowledge", "Not validated", "3 synthetic families in demo fixtures"],
        ["Client data sources & quality", "Not validated", "Local JSON files pretending to be CRM/PIM/FSM/Claims"],
        ["Solution fit for client problem", "Not validated", "Generic warranty-triage use case hypothesis"],
        ["GraphRAG accuracy on real customer language", "Not validated", "Curated demo messages against synthetic graph"],
        ["Neo4j as approved client platform", "Not validated", "Chosen for reference demo convenience"],
        ["LangGraph / Python stack as approved", "Not validated", "Reference implementation stack"],
        ["ETL / pipeline design at enterprise scale", "Not validated", "3-pipeline demo orchestrator on mock data"],
        ["Escalation rules & thresholds", "Not validated", "Demo defaults (65%, critical severity) — not client policy"],
        ["Provenance / agent dossier acceptance", "Not validated", "UI mockup — no real agent pilot"],
        ["POC / MVP / Production timelines & cost", "Not validated", "Planning estimates in Document 05"],
        ["Reference demo behaviour", "Not validated for client", "Runs locally on synthetic data — proves demo code executes, not client value"],
      ],
      [2800, 2400, 4160]
    ),
    spacer(),
    p(
      "Status key used throughout this register: H = Hypothesis (default for every item), V = Validated (none today), I = Invalidated (requires redesign). No assumption may be marked V without client evidence, SME sign-off, or measured pilot data — a working demo is not sufficient evidence."
    ),

    h1("3. What the Reference Demo Is — and Is Not"),
    h2("3.1 What the Demo Is"),
    pb("bullets", "A clickable illustration of one possible warranty diagnostics architecture"),
    pb("bullets", "A conversation aid for executives, architects, and contact center leaders"),
    pb("bullets", "A strawman codebase to estimate effort — not a production foundation committed to the client"),
    pb("bullets", "Synthetic end-to-end flow: chat → LangGraph → GraphRAG → Neo4j → escalation UI"),

    h2("3.2 What the Demo Does NOT Confirm"),
    pb("bullets", "That graph-native diagnosis is accurate enough for the client's products and customer language"),
    pb("bullets", "That Neo4j, LangGraph, or Python are acceptable in the client's enterprise standards"),
    pb("bullets", "That CRM, Claims, PIM, or FSM integrations will work as designed — connectors are mocks"),
    pb("bullets", "That the ontology, symptom catalog, or confidence model reflect real engineering or field data"),
    pb("bullets", "That agents will trust or use the escalation dossier format"),
    pb("bullets", "That warranty gating rules match client policy"),
    pb("bullets", "That ETL pipelines, smoke gates, or lineage meet client governance or compliance requirements"),
    pb("bullets", "That deflection, AHT, or ROI targets are achievable"),
    pb("bullets", "That the phased roadmap durations, team sizes, or costs are realistic for this client"),

    h2("3.3 Client Enterprise — Entirely Unknown (U-01 – U-15)"),
    tbl(
      ["#", "Unknown Area", "Why It Matters", "Documents Affected"],
      [
        ["U-01", "Actual CRM platform and asset data model", "Product pre-bind, warranty dates, case write-back", "01, 05, 07, 09"],
        ["U-02", "Claims / warranty policy system(s)", "Eligibility rules, adjudication automation scope", "01, 05, 07"],
        ["U-03", "PIM / PLM / FMEA source systems", "Knowledge graph population authority", "02, 05, 07, 10"],
        ["U-04", "FSM and service history systems", "HistoricalResolution evidence, confidence calibration", "02, 07"],
        ["U-05", "Total product families and SKU count", "Catalog scaling timeline and team size", "05, 10"],
        ["U-06", "Regional / brand variation", "Connector multiplication, ontology forks", "05, 10"],
        ["U-07", "Service manual format and accessibility", "Document ingestion pipeline scope", "10"],
        ["U-08", "Contact center platform (CCaaS, CRM Cases)", "Escalation handoff integration", "01, 05, 08, 09"],
        ["U-09", "Customer channels (web, mobile, IVR, agent)", "UI/omnichannel program scope", "01, 05"],
        ["U-10", "Average diagnosis volume and seasonality", "Neo4j sizing, API SLOs, HA requirements", "05, 10"],
        ["U-11", "PII / data residency / regulatory constraints", "Graph boundary, CRM call patterns, retention", "01, 05"],
        ["U-12", "Existing AI / chatbot investments", "Build vs extend vs replace decisions", "01, 05"],
        ["U-13", "SME availability and knowledge governance maturity", "Knowledge engineering throughput", "05, 10"],
        ["U-14", "Integration API maturity (REST, events, batch)", "ETL design, latency, error handling", "07, 10"],
        ["U-15", "Organizational appetite for automation vs human triage", "Escalation threshold tuning, deflection targets", "01, 05, 08"],
      ],
      [600, 2600, 3000, 3160]
    ),
    spacer(),

    pgBreak(),
    h1("4. Reference Architecture Disclaimer"),
    p(
      "Documents 01–10 describe a hypothetical reference solution for a mid-to-large consumer durables / appliance manufacturer. We have not confirmed the client is such an organization, that they have this problem at this priority, or that this shape of solution is appropriate. Named systems (Salesforce CRM, Guidewire Claims, SAP PLM, ServiceMax FSM, Genesys CCaaS) are fiction placeholders for discussion — not discovered facts."
    ),
    p("The following design elements are intentionally generic pending discovery:"),
    pb("bullets", "Connector URLs, authentication schemes, and payload schemas in config/settings.py"),
    pb("bullets", "Ontology entity coverage beyond Product, Symptom, FailureMode, DiagnosticStep, Part, HistoricalResolution"),
    pb("bullets", "Escalation threshold (65%) and severity taxonomy — require client safety policy alignment"),
    pb("bullets", "Phased roadmap durations (8-week POC, 8-week MVP, 12–24 month production) — require velocity calibration"),
    pb("bullets", "Person-month and cost estimates in Document 05 — order-of-magnitude only"),
    p(
      "Replacing any assumption in Section 5 may require revisiting architecture, roadmap scope, or phase gates. This is expected — not a sign of design failure."
    ),

    h1("5. Foundational Assumptions Register"),
    p(
      "Every row below is a hypothesis. Status column shows H for all items at document issue — nothing has been validated. IDs support traceability to architecture (Doc 01), roadmap (Doc 05), and pipelines (Doc 10)."
    ),
    tbl(
      ["Status", "Meaning", "Count Today"],
      [
        ["H", "Hypothesis — assumed for design; no client confirmation", "All assumptions"],
        ["V", "Validated — confirmed with evidence", "Zero"],
        ["I", "Invalidated — disproven; design must change", "Zero"],
      ],
      [1200, 5200, 2960]
    ),
    spacer(),

    h2("5.1 Business & Operating Model"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-01", "H", "Primary value case is contact center workload reduction on warranty/support inquiries", "Program charter may change; KPIs misaligned", "Executive sponsor interview — Week 0"],
        ["A-02", "H", "Automated tier handles first-line symptom triage; humans retain safety/ambiguous cases", "Full automation pressure may conflict with governance design", "CC operations leadership — Week 1"],
        ["A-03", "H", "30–50% tier-1 deflection is aspirational over 18 months — not a POC commitment", "Executive disappointment at POC scale", "Set expectations in sponsor readout — Week 1"],
        ["A-04", "H", "Warranty policy interpretation remains partly human until MVP at earliest", "Scope creep into adjudication automation", "Claims policy owner workshop — Week 2"],
        ["A-05", "H", "Pilot product families are a subset agreed with service engineering — not entire catalog", "Catalog scale estimates invalid", "Product portfolio review — Week 1"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    h2("5.2 Product & Knowledge Scope"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-10", "H", "Hundreds of product families exist across brands/regions in production target state", "Roadmap timeline and team sizing wrong", "PIM portfolio export — Week 1"],
        ["A-11", "H", "FMEA or equivalent reliability data exists for major families (may be incomplete)", "Failure mode coverage gaps; manual curation load", "Engineering data assessment — Week 2"],
        ["A-12", "H", "Service manuals / SOPs exist in retrievable form (PDF, CMS, or PLM-linked)", "Document ingestion pipeline may be major workstream", "Manual inventory sample — Week 2"],
        ["A-13", "H", "Symptom catalog can be normalized to canonical graph symptoms with SME mapping", "Lexical matching insufficient; vector pilot needed earlier", "SME mapping workshop — Week 3"],
        ["A-14", "H", "2–4 families per knowledge engineer per month is achievable with governance", "100-family timeline extends significantly", "POC velocity measurement — Week 8"],
        ["A-15", "H", "Demo ontology (6 node types) is sufficient starting schema — extensions TBD", "Schema migration in POC if IoT codes, error codes, regions needed", "Ontology workshop — Week 1"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    h2("5.3 Enterprise Landscape & Integration"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-20", "H", "Client has CRM with registered asset / product instance records", "Runtime product pre-bind pattern fails; serial lookup needed", "CRM sandbox API review — Week 1"],
        ["A-21", "H", "Claims or warranty system exposes eligibility or policy reference data", "Warranty gate must be redesigned or deferred", "Claims API/export review — Week 2"],
        ["A-22", "H", "PIM or PLM is authoritative for product taxonomy and parts BOM", "Alternate product master must be identified", "Data governance interview — Week 1"],
        ["A-23", "H", "FSM or work order history provides confirmed repair outcomes", "HistoricalResolution evidence thin; confidence tuning weak", "FSM sample extract — Week 2"],
        ["A-24", "H", "Integration is API-first (REST/OData) or schedulable batch — not exclusively real-time event-only", "ETL orchestration redesign; streaming scope added", "Integration architect interview — Week 1"],
        ["A-25", "H", "Sandbox or non-prod environments available within 2 weeks of program start", "POC Week 1–2 slip; fixture bridge extended", "Environment request tracker — Week 0"],
        ["A-26", "H", "No single system holds complete diagnostic knowledge — multi-source merge required", "Simplified pipeline if one golden KB exists", "Source system matrix — Week 1"],
        ["A-27", "H", "Contact center case management can receive structured escalation payloads", "Custom agent desktop integration scope grows", "CCaaS/CRM case API review — Week 3"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    pgBreak(),
    h2("5.4 Data Availability, Quality & Ownership"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-30", "H", "PIM product data has stable identifiers suitable for MERGE keys", "Graph idempotency breaks; reconciliation pipeline needed earlier", "PIM sample + key analysis — Week 2"],
        ["A-31", "H", "Field and claims history covers enough closed cases to tune confidence (not just open pipeline)", "Historical evidence sparse; SME seeding required", "FSM/Claims volume analysis — Week 2"],
        ["A-32", "H", "Data owners exist for each source system with approval authority", "ETL governance blocked", "Data governance RACI — Week 1"],
        ["A-33", "H", "Duplicate and conflicting records across sources are manageable with documented precedence rules", "OntologyBuilder conflict resolution complexity grows", "Reconciliation workshop — Week 3"],
        ["A-34", "H", "Customer PII can remain in CRM — not replicated into Neo4j knowledge graph", "Security architecture revision; graph boundary moves", "Privacy / legal review — Week 2"],
        ["A-35", "H", "English-language symptom descriptions suffice for pilot; localization is production scope", "NLP and symptom catalog multiply by locale", "Market scope confirmation — Week 1"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    h2("5.5 Technology & Platform"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-40", "H", "Neo4j is acceptable as knowledge graph store (Aura or self-hosted)", "Alternate graph DB evaluation — schedule slip", "Enterprise architecture standards — Week 0"],
        ["A-41", "H", "Graph-native retrieval is primary; LLM is optional formatting/UX layer only", "Stakeholders expecting ChatGPT-style answers may be dissatisfied", "AI strategy alignment — Week 1"],
        ["A-42", "H", "Python / FastAPI / LangGraph stack is deployable within client cloud standards", "Language or framework exception process needed", "Platform engineering review — Week 1"],
        ["A-43", "H", "Streamlit is acceptable for POC only — not customer production channel", "UI scope in POC if stakeholder expects production UX", "Channel strategy — Week 1"],
        ["A-44", "H", "Hybrid vector + graph retrieval is deferred until lexical baseline measured", "Earlier embedding investment if symptom recall insufficient", "POC accuracy report — Week 7"],
        ["A-45", "H", "Client permits outbound HTTPS from app tier to enterprise APIs (or ESB mediation)", "Network architecture and latency model change", "Network security review — Week 2"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    h2("5.6 Security, Compliance & Operations"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-50", "H", "SSO (OIDC/SAML) available for agent and internal users by MVP", "Agent pilot delayed; demo auth only in POC", "IAM team engagement — Week 2"],
        ["A-51", "H", "Diagnostic knowledge is not ITAR/export-controlled (consumer appliances context)", "Compliance scope expands significantly", "Legal / compliance — Week 1"],
        ["A-52", "H", "Audit retention for diagnosis and escalation events aligns with case management policy (90 days – 7 years TBD)", "Storage and lineage architecture adjustment", "Records management — Week 3"],
        ["A-53", "H", "Penetration test and SOC2 alignment required before production — not POC", "Production gate criteria unchanged; MVP security track starts Week 9", "Security architect — Week 2"],
        ["A-54", "H", "SRE on-call model for peak season is client-operated or jointly defined in production", "Operations runbook scope in Document 10", "Operations leadership — MVP planning"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    h2("5.7 Program Delivery & Governance"),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-60", "H", "Executive sponsor commits 5.5–6 FTE core team for 8-week POC", "POC scope must shrink or timeline extends", "Resource plan approval — Week 0"],
        ["A-61", "H", "Service engineering SMEs available ≥4 hours/week during POC", "Knowledge validation blocked; accuracy targets at risk", "SME commitment letter — Week 0"],
        ["A-62", "H", "Architecture and ontology decisions made within 3 business days during POC", "Weekly plan slip accumulates", "Governance cadence agreement — Week 0"],
        ["A-63", "H", "Client integration teams respond to API access requests within 5 business days", "Connector work blocked", "Vendor management SLA — Week 0"],
        ["A-64", "H", "POC success is measured on curated scenarios — not live customer traffic", "Accuracy debate without controlled test pack", "Test pack sign-off — Week 3"],
        ["A-65", "H", "Production is a separate funded program after MVP — not implicit in POC/MVP SOW", "Budget surprise at Week 16", "Commercial framing — Week 0"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    h2("5.8 Reference Demo & Solution Design (Not Client-Validated)"),
    p(
      "These assumptions underpin the demo and Documents 01–10. They are design choices for illustration. The demo running successfully on a laptop confirms only that the reference code executes against synthetic fixtures — not that the approach is correct for the client."
    ),
    tbl(
      ["ID", "Status", "Assumption", "If Wrong — Impact", "Validate By"],
      [
        ["A-70", "H", "Property-graph knowledge model fits warranty symptom → failure → step reasoning", "Entire architecture may need re-evaluation (rules engine, case-based reasoning, LLM-only)", "Ontology workshop + SME review — Week 1"],
        ["A-71", "H", "Lexical symptom matching is adequate starting point before vector search", "Earlier ML/NLP investment; different retrieval architecture", "POC accuracy on real customer utterances — Week 7"],
        ["A-72", "H", "65% confidence threshold is reasonable default for escalation", "Over- or under-escalation; client policy may differ entirely", "CC policy + pilot override data — MVP"],
        ["A-73", "H", "Critical / high / medium severity taxonomy maps to client safety policy", "Wrong cases auto-resolved or over-escalated", "Safety SME workshop — Week 2"],
        ["A-74", "H", "Multi-source ETL merge (PIM+FSM+Claims+CRM) is the right ingestion pattern", "Single golden KB or manual curation may be simpler", "Source system matrix — Week 1"],
        ["A-75", "H", "Provenance trail format is useful to contact center agents", "Agent UI redesign; different explainability model", "Agent shadowing + UAT — MVP"],
        ["A-76", "H", "Three-phase roadmap (POC 8w / MVP 8w / Production 12–24mo) is structurally sound", "Phases may need complete rescoping", "Discovery + POC velocity — Week 8"],
        ["A-77", "H", "14 production pipelines (Document 10) are necessary at enterprise scale", "Pipeline count may be over- or under-engineered", "Catalog size + governance maturity — post-MVP"],
        ["A-78", "H", "Reference codebase (diagnostic-chatbot) is a reasonable POC starting point — not throwaway", "Greenfield rewrite may be cheaper if stack rejected", "EA + platform standards — Week 0–1"],
        ["A-79", "H", "Demo test scenarios (wm/dw/mw) represent realistic diagnostic behaviour", "Demo misleads stakeholders about production accuracy", "Replace with client-authored scenarios — Week 3"],
        ["A-80", "H", "GraphRAG without LLM meets stakeholder expectations for 'AI diagnostics'", "Expectation gap; repositioning or LLM layer required", "Executive + CC alignment — Week 1"],
      ],
      [600, 500, 3000, 2600, 2160]
    ),
    spacer(),

    pgBreak(),
    h1("6. Client-Provided Dependencies (Mandatory for Delivery)"),
    p(
      "Any enterprise program delivering graph-backed warranty diagnostics will fail without client-side provision of the following. These are not optional nice-to-haves — they are structural dependencies."
    ),

    h2("6.1 Executive & Governance"),
    tbl(
      ["Dependency", "Required For", "When Needed", "Owner (Client)"],
      [
        ["Executive sponsor with budget authority", "POC charter, SME time, sandbox access", "Week 0", "VP Customer Service / CTO delegate"],
        ["Program decision forum (weekly)", "Ontology, scope, escalation policy decisions", "Week 0 onward", "Sponsor + Architect + PO"],
        ["Signed assumption acknowledgment (Section 12)", "Converting reference design to committed scope", "End of Week 1", "Sponsor"],
        ["Change control for integration credentials", "Production connectors", "MVP onward", "IT Security"],
      ],
      [2800, 2800, 2000, 1760]
    ),
    spacer(),

    h2("6.2 People & Subject Matter Expertise"),
    tbl(
      ["Role", "POC", "MVP", "Production", "Client vs Delivery"],
      [
        ["Service / reliability engineering SME", "4–8 hrs/week", "8–12 hrs/week", "Approval pool", "Client — mandatory"],
        ["Contact center operations lead", "2 hrs/week", "4 hrs/week pilot", "Ongoing", "Client — mandatory"],
        ["Claims / warranty policy owner", "2 hrs/week", "4 hrs/week", "As needed", "Client — mandatory"],
        ["CRM / integration architect", "4 hrs/week", "8 hrs/week", "Part-time", "Client — strongly recommended"],
        ["Data governance / source system owners", "2 hrs/week each", "4 hrs/week", "Standing", "Client — mandatory"],
        ["Security / IAM representative", "2 hrs (POC)", "8 hrs/week", "Reviews", "Client — MVP onward"],
        ["Delivery: architect, engineers, knowledge engineer", "5.5–6 FTE", "6–7 FTE", "15–20 FTE program", "Delivery team"],
      ],
      [2400, 1200, 1200, 1400, 3160]
    ),
    spacer(),

    h2("6.3 System Access & Environments"),
    tbl(
      ["Dependency", "Purpose", "POC Minimum", "Notes"],
      [
        ["CRM sandbox + API credentials", "Asset read, case draft write", "Read on customer/asset objects", "Often slowest dependency — start Week 0"],
        ["PIM / PLM export or API", "Product, parts, FMEA seed", "1 family export acceptable", "Fixture bridge if API delayed"],
        ["FSM closed work order sample", "HistoricalResolution seed", "500+ records or export file", "Anonymized if required"],
        ["Claims closed claim sample", "Resolution + policy reference", "Policy doc + sample claims", "Eligibility API ideal by MVP"],
        ["Non-prod Neo4j or cloud project", "Staging graph", "Single instance", "Aura trial or client K8s namespace"],
        ["CI/CD namespace", "populate_graph automation", "Pipeline run permission", "DevOps Week 1"],
        ["CCaaS / agent desktop sandbox", "Escalation handoff pilot", "Deferred to MVP acceptable", "Required before agent pilot"],
      ],
      [2400, 2800, 2400, 1760]
    ),
    spacer(),

    h2("6.4 Data Artifacts (Discovery Deliverables from Client)"),
    pb("bullets", "Product portfolio summary — family count, regions, brands, EOL policy"),
    pb("bullets", "Integration landscape diagram (even if outdated — accelerates validation)"),
    pb("bullets", "Sample service manual or troubleshooting guide for one pilot family"),
    pb("bullets", "FMEA or failure mode list for one pilot family (if available)"),
    pb("bullets", "Contact center escalation policy and safety-critical symptom definitions"),
    pb("bullets", "Current warranty eligibility business rules (narrative acceptable)"),
    pb("bullets", "Baseline metrics: tier-1 volume, AHT, override rate if any prior automation exists"),
    pb("bullets", "Privacy impact assessment template or PII handling standards"),

    pgBreak(),
    h1("7. Third-Party, Vendor & Licensing Dependencies"),
    tbl(
      ["Dependency", "Phase", "Owner", "Risk if Unavailable"],
      [
        ["Neo4j license (Aura or Enterprise)", "POC optional; MVP required", "Client procurement", "Graph platform blocked"],
        ["CRM vendor API access (Salesforce, SAP, etc.)", "POC read", "Client vendor relationship", "No runtime enrichment"],
        ["Claims system vendor cooperation", "MVP", "Client", "Warranty gate manual only"],
        ["Cloud compute (AWS/Azure/GCP)", "POC non-prod", "Client platform team", "No deployment target"],
        ["Corporate IdP (Okta, Azure AD, etc.)", "MVP SSO", "Client IAM", "Agent pilot blocked"],
        ["Optional LLM provider (xAI, OpenAI)", "Post-POC if desired", "Client AI governance", "NL polish only — not blocking"],
        ["Airflow / orchestrator (if mandated)", "MVP scheduling", "Client data platform", "Cron acceptable for MVP"],
      ],
      [2800, 1600, 2000, 2960]
    ),
    spacer(),

    h1("8. Delivery Team Capability Dependencies"),
    p("The delivery organization must provide or procure:"),
    tbl(
      ["Capability", "Why Required", "POC", "Gap Risk"],
      [
        ["Solution / enterprise architect", "Assumption validation, integration patterns", "0.4 FTE", "Wrong connectors designed"],
        ["Knowledge engineer / ontologist", "Symptom catalog, FMEA mapping", "1.0 FTE", "Accuracy targets missed"],
        ["Graph / Neo4j engineer", "populate_graph, staging promotion", "0.75 FTE", "ETL load failures"],
        ["Integration engineer", "CRM/Claims/PIM connectors", "0.75 FTE", "POC slips on access wait"],
        ["Backend engineer (Python, LangGraph, FastAPI)", "Agent and API hardening", "1.0 FTE", "Reference code is strawman — may be rewritten"],
        ["QA / evaluation engineer", "Curated scenario harness", "0.5 FTE", "No objective accuracy measure"],
        ["UX for agent provenance views", "Agent trust in escalation dossier", "0.5 FTE", "Pilot adoption risk"],
        ["DevOps", "Environments, CI, secrets", "0.25 FTE", "Manual runs only"],
        ["Security architect", "PII boundary, SSO", "0 MVP", "Production gate failure"],
      ],
      [2800, 3200, 1200, 2160]
    ),
    spacer(),

    h1("9. How Assumptions Drive Architecture & Roadmap"),
    h2("9.1 Architecture Decisions Conditional on Assumptions"),
    tbl(
      ["Architecture Decision", "Rests On Assumptions", "If Invalidated — Rework"],
      [
        ["Multi-connector ETL (PIM, FSM, Claims, CRM)", "A-22, A-23, A-26", "Single-source pipeline; reduced provenance"],
        ["CRM runtime enrichment (not in graph)", "A-20, A-34", "Serial lookup service; graph stores more context"],
        ["Neo4j knowledge graph", "A-40", "Re-platform evaluation (6–12 weeks)"],
        ["Graph-native diagnosis without LLM", "A-41", "Hybrid LLM reasoning layer — governance overhaul"],
        ["Escalation on critical + low confidence", "A-02, client safety policy", "Threshold and severity taxonomy redesign"],
        ["Provenance on every evidence line", "A-32, A-52", "Reduced audit scope if client waives"],
        ["Three-phase roadmap (POC/MVP/Production)", "A-60, A-65, A-10", "Compress or extend phases; resize team"],
        ["14 production pipelines (Document 10)", "A-10, A-12, A-13", "Fewer pipelines if catalog small and docs structured"],
      ],
      [2800, 2800, 3760]
    ),
    spacer(),

    h2("9.2 Roadmap Scope Conditional on Assumptions"),
    tbl(
      ["Roadmap Element", "Assumption Dependency", "Sensitivity"],
      [
        ["POC: 2 product families", "A-05, A-11, A-61", "High — SME time is critical path"],
        ["POC: 1 live CRM read", "A-20, A-25", "High — sandbox access often delays"],
        ["MVP: 10–15 families", "A-14, A-10", "High — linear with knowledge engineering throughput"],
        ["MVP: SSO + case write-back", "A-27, A-50", "Medium — standard enterprise patterns"],
        ["Production: 100+ families in 12–24 months", "A-10, A-14, A-13", "Very high — largest estimate uncertainty"],
        ["Production: hourly incremental ETL", "A-24, A-31", "Medium — may remain daily batch"],
        ["Vector index pipeline (optional)", "A-44, A-13", "Medium — triggered by POC recall gaps"],
      ],
      [2800, 3200, 3360]
    ),
    spacer(),

    pgBreak(),
    h1("10. Discovery Workshop Agenda (Week 0–1)"),
    p(
      "No assumption may move from H to V based on the demo or these documents alone. Discovery sessions must produce client evidence. Outcomes below are targets for first validation — not current facts."
    ),
    tbl(
      ["Session", "Duration", "Participants", "Target Outcomes (First Validation)"],
      [
        ["Executive alignment", "2 hrs", "Sponsor, PO, Architect", "Confirm problem statement; acknowledge zero validated assumptions today"],
        ["Enterprise landscape review", "3 hrs", "EA, integration architects", "Draft source matrix; begin U-01–U-04 assessment"],
        ["Product portfolio & pilot family selection", "2 hrs", "Product mgmt, service engineering", "Candidate pilot families — not yet approved"],
        ["Ontology & safety workshop", "4 hrs", "SMEs, knowledge engineer", "Challenge A-70, A-73, A-15; draft symptom seed if domain confirmed"],
        ["Contact center operations", "2 hrs", "CC lead, workforce mgmt", "Assess A-02, A-72, A-75; map U-08, U-15"],
        ["Data governance & privacy", "2 hrs", "Data owners, legal/privacy", "Assess A-32, A-34, A-52 — no sign-off without legal"],
        ["Reference demo walkthrough", "1 hr", "Sponsors + SMEs", "Explicitly label demo as non-validated illustration; capture scepticism"],
        ["Environment & access planning", "1 hr", "DevOps, security, vendors", "A-25 request tracker opened — not fulfilled"],
      ],
      [2400, 1000, 2800, 3160]
    ),
    spacer(),

    h1("11. Validation Plan — From Zero to Committed Scope"),
    p(
      "Today: 0 assumptions validated. The gates below describe when the program may progress — not where we are now."
    ),
    tbl(
      ["Gate", "Timing", "Minimum Validations Required (H → V)", "Proceed If", "Stop / Rework If"],
      [
        ["Engagement start", "Week 0", "None — acknowledgment only", "Section 14 signed; sponsor accepts all-hypothesis state", "Stakeholder treats demo as proof"],
        ["Discovery complete", "End Week 1", "A-01, A-20 or alternate, A-32, A-60, A-61", "Written source matrix; named data owners; SME hours committed", "No authoritative product or customer data path"],
        ["Architecture direction", "Week 2", "A-40, A-42, A-70 (or alternative chosen)", "EA written position on graph stack or documented alternative", "Neo4j/stack rejected without replacement"],
        ["POC mid-point", "Week 4", "A-11, A-30, A-13 on real client data", "First real family loaded — not fixtures", "Client data unusable without major cleansing"],
        ["POC → MVP", "Week 8", "A-64, A-02, A-27, A-71, A-79", "Measured accuracy on client scenarios; agent dossier reviewed", "Accuracy or agent acceptance fails on real data"],
        ["MVP → Production", "Week 16", "A-14, A-10, A-50, A-75", "Pilot KPIs trending; SSO live; real agent pilot", "Override rate flat; ETL unreliable"],
      ],
      [1300, 1100, 2800, 2000, 2160]
    ),
    spacer(),

    h1("12. Assumption Invalidation — Impact & Response"),
    tbl(
      ["Invalidated Assumption", "Likely Trigger", "Response Pattern", "Schedule Impact"],
      [
        ["A-20 — No CRM asset registry", "CRM discovery", "Serial/model lookup via alternate MDM; manual product picker", "+2–4 weeks POC"],
        ["A-11 — No FMEA data", "Engineering assessment", "Manual failure mode authoring; higher SME load", "+4–8 weeks per 10 families"],
        ["A-10 — Catalog <20 families", "Portfolio review", "Compress production program; fewer governance pipelines", "−6–12 months"],
        ["A-41 — LLM-first mandate", "AI strategy conflict", "Reposition LLM as formatter; add RAG guardrails doc", "Governance +4 weeks"],
        ["A-40 — Neo4j not approved", "EA standards", "Evaluate alternate graph; pause Load layer", "+6–12 weeks"],
        ["A-61 — SME time <2 hrs/week", "Resource denial", "Shrink POC to 1 family; defer accuracy targets", "POC outcome at risk"],
        ["A-25 — Sandbox >6 weeks", "Vendor delay", "Extended fixture mode; parallel integration track", "POC slip 4–6 weeks"],
      ],
      [2200, 2000, 3200, 1960]
    ),
    spacer(),

    pgBreak(),
    h1("13. Risk Register (Everything Unvalidated — Including Demo)"),
    tbl(
      ["Risk ID", "Source", "Likelihood", "Impact", "Mitigation", "Owner"],
      [
        ["R-00", "Demo mistaken for proof", "High", "Critical", "Open every readout with Section 3.2; label demo 'illustration only'", "Architect"],
        ["R-01", "U-01, A-25", "High", "High", "Week 0 CRM access request; do not demo mock CRM as client reality", "Integration lead"],
        ["R-02", "A-61", "High", "High", "Sponsor SME mandate before POC; no synthetic SME knowledge in graph", "Program manager"],
        ["R-03", "U-05, A-10", "Medium", "High", "No 100-family commitment until MVP velocity on real data", "Architect"],
        ["R-04", "U-11, A-34", "Medium", "Critical", "Privacy review before any client PII in non-prod", "Security architect"],
        ["R-05", "A-80, A-41", "High", "High", "Set expectations: graph-truth, not ChatGPT; demo is not AI proof", "Architect"],
        ["R-06", "A-79", "High", "High", "Replace demo scenarios with client-authored test pack before accuracy claims", "QA lead"],
        ["R-07", "A-70", "Medium", "Critical", "Ontology workshop may reject graph approach entirely", "Architect"],
        ["R-08", "A-78", "Medium", "High", "Treat reference code as disposable until EA approves stack", "Tech lead"],
        ["R-09", "U-14", "High", "Medium", "No connector design final until API inspection", "Integration lead"],
        ["R-10", "A-65", "Medium", "High", "Commercial framing: POC/MVP ≠ production program", "Sponsor"],
      ],
      [800, 1800, 1000, 1000, 2800, 1760]
    ),
    spacer(),

    h1("14. Stakeholder Acknowledgment — Hypothesis State"),
    p(
      "By signing below, stakeholders confirm they understand the current state: zero validated assumptions; the reference demo is not confirmation of client fit; Documents 01, 05, and 10 are planning hypotheses; Section 6 dependencies are required before any delivery commitment; no timeline or cost figure is binding."
    ),
    tbl(
      ["Role", "Name", "I understand demo ≠ validation", "I understand all A-xx are H today", "Date", "Signature"],
      [
        ["Executive Sponsor", "", "☐", "☐", "", ""],
        ["Enterprise Architect", "", "☐", "☐", "", ""],
        ["Contact Center Lead", "", "☐", "☐", "", ""],
        ["Service Engineering / SME Lead", "", "☐", "☐", "", ""],
        ["Data Governance Owner", "", "☐", "☐", "", ""],
        ["Program Manager", "", "☐", "☐", "", ""],
      ],
      [1800, 1400, 1600, 1600, 1000, 960]
    ),
    spacer(),
    p(
      "Validation log (maintain as appendix): record assumption ID, evidence source, date, and approver when any item moves H → V. Empty at engagement start."
    ),

    h1("15. Document References & Maintenance"),
    pb("bullets", "12 — Solution Approach & Delivery Methodology (how we work; rationale for graph-first phased method)"),
    pb("bullets", "01 — Architecture & Solution Design (hypothetical until assumptions validated)"),
    pb("bullets", "05 — Enterprise Implementation Roadmap (all estimates unvalidated)"),
    pb("bullets", "07 — Enterprise Pipelines & Data Lineage (demo pipelines on mock data only)"),
    pb("bullets", "10 — Production Pipelines & Phased Roadmap (pipeline count is planning fiction until discovery)"),
    pb("bullets", "Repository: diagnostic-chatbot — local reference demo; does not validate any A-xx assumption"),
    spacer(),
    p(
      "Maintenance: Version increment when any assumption moves H → V or H → I. At engagement start all A-01 through A-80 remain H. Demo updates do not change validation status."
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
                    text: "Doc 11 — Assumptions, Dependencies & Open Questions",
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