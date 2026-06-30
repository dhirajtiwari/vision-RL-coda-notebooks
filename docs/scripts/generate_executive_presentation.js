/**
 * Executive proposal presentation — polished client deck
 * Run: node docs/scripts/generate_executive_presentation.js
 */

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "Enterprise-Warranty-Diagnostics-Executive-Proposal.pptx");

const C = {
  navy: "1A2744",
  deep: "0B4F6C",
  teal: "0E7C86",
  mint: "3CBFA0",
  sky: "D6EEF3",
  cloud: "F4F7FA",
  white: "FFFFFF",
  ink: "1E293B",
  slate: "64748B",
  gold: "C9A227",
};

const FONT = { head: "Georgia", body: "Calibri" };
const SLIDE_H = 5.625;
const FOOTER_Y = 5.18;
const CONTENT_TOP = 1.62;
const CONTENT_MAX_Y = 4.88;
const ML = 0.55;
const CW = 8.9; // content width

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Enterprise Solution Architecture";
pres.title = "Enterprise Warranty Diagnostics — Executive Proposal";

function footer(slide, n) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: FOOTER_Y, w: 10, h: SLIDE_H - FOOTER_Y,
    fill: { color: C.deep },
  });
  slide.addText("Enterprise Warranty Diagnostics  ·  Confidential Proposal", {
    x: ML, y: FOOTER_Y + 0.1, w: 7.5, h: 0.28,
    fontSize: 8, color: C.sky, fontFace: FONT.body, margin: 0,
  });
  slide.addText(String(n), {
    x: 9.0, y: FOOTER_Y + 0.1, w: 0.45, h: 0.28,
    fontSize: 8, color: C.sky, align: "right", fontFace: FONT.body, margin: 0,
  });
}

function header(slide, title, subtitle) {
  slide.background = { color: C.cloud };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.48,
    fill: { color: C.white },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.09, h: 1.48,
    fill: { color: C.mint },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: ML, y: 1.38, w: CW, h: 0.04,
    fill: { color: C.teal },
  });
  slide.addText(title, {
    x: ML, y: 0.28, w: CW, h: 0.55,
    fontSize: 26, bold: true, color: C.navy, fontFace: FONT.head, margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: ML, y: 0.82, w: CW, h: 0.42,
      fontSize: 13, color: C.slate, fontFace: FONT.body, margin: 0,
    });
  }
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: opts.fill || C.white },
    line: { color: opts.border || C.sky, width: 1 },
    shadow: opts.shadow !== false ? {
      type: "outer", color: "000000", blur: 3, offset: 1, angle: 135, opacity: 0.1,
    } : undefined,
  });
  if (opts.accent) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.07, h,
      fill: { color: opts.accent },
    });
  }
}

function calloutBar(slide, y, text, dark = true) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: ML, y, w: CW, h: 0.52,
    fill: { color: dark ? C.navy : C.sky },
  });
  slide.addText(text, {
    x: ML + 0.18, y: y + 0.1, w: CW - 0.36, h: 0.32,
    fontSize: 11, color: dark ? C.mint : C.deep,
    fontFace: FONT.body, margin: 0, valign: "middle",
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 1 — Title
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  // Layered geometry
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.2, y: -0.5, w: 5, h: 4.5,
    fill: { color: C.deep, transparency: 40 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 4.35, w: 10, h: 1.275,
    fill: { color: C.deep },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.14, h: SLIDE_H,
    fill: { color: C.mint },
  });
  s.addText("Enterprise Warranty\nDiagnostics Platform", {
    x: 0.65, y: 1.05, w: 7.5, h: 1.5,
    fontSize: 38, bold: true, color: C.white, fontFace: FONT.head, margin: 0,
  });
  s.addText("Graph-First Intelligent Triage for Warranty & Support Operations", {
    x: 0.65, y: 2.65, w: 7.2, h: 0.55,
    fontSize: 17, color: C.mint, fontFace: FONT.body, margin: 0,
  });
  const tags = ["Explainable AI", "Enterprise Integration", "Governed Delivery"];
  tags.forEach((t, i) => {
    const x = 0.65 + i * 2.35;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.45, w: 2.15, h: 0.42,
      fill: { color: C.teal },
    });
    s.addText(t, {
      x, y: 3.52, w: 2.15, h: 0.3,
      fontSize: 10, bold: true, color: C.white, align: "center",
      fontFace: FONT.body, margin: 0,
    });
  });
  s.addText("Executive Proposal  ·  Solution, Approach & Delivery Methodology", {
    x: 0.65, y: 4.52, w: 7.5, h: 0.35,
    fontSize: 12, color: C.sky, fontFace: FONT.body, margin: 0,
  });
  s.addText("June 2026", {
    x: 8.3, y: 4.52, w: 1.2, h: 0.35,
    fontSize: 11, color: C.sky, align: "right", fontFace: FONT.body, margin: 0,
  });
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 2 — Challenge
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "The Business Challenge", "Warranty and support operations at an inflection point");
  card(s, ML, CONTENT_TOP, 5.35, 3.1, { accent: C.teal });
  s.addText(
    [
      { text: "Enterprises face a structural mismatch: rising contact volume, higher customer expectations for AI-assisted service, and zero tolerance for unsafe or non-compliant repair guidance.", options: { breakLine: true, fontSize: 12, color: C.ink } },
      { text: " ", options: { breakLine: true, fontSize: 6 } },
      { text: "High-volume contacts that could self-resolve with trusted guidance", options: { bullet: true, breakLine: true, fontSize: 11, color: C.ink } },
      { text: "Safety-critical symptoms requiring immediate human intervention", options: { bullet: true, breakLine: true, fontSize: 11, color: C.ink } },
      { text: "Out-of-warranty and invalid claims consuming tier-1 capacity", options: { bullet: true, breakLine: true, fontSize: 11, color: C.ink } },
      { text: "Agents re-interviewing customers without prior diagnostic context", options: { bullet: true, breakLine: true, fontSize: 11, color: C.ink } },
      { text: "Fragmented knowledge across CRM, product, field, and claims systems", options: { bullet: true, fontSize: 11, color: C.ink } },
    ],
    { x: ML + 0.22, y: CONTENT_TOP + 0.18, w: 4.95, h: 2.75, fontFace: FONT.body, paraSpaceAfter: 5 }
  );
  const stats = [
    ["30–50%", "Tier-1 deflection potential", "(post-scale, family-dependent)"],
    ["20–40%", "AHT reduction on escalations", "(pre-built diagnostic dossier)"],
    ["100%", "Provenance on escalated cases", "(source-traceable evidence)"],
  ];
  stats.forEach((st, i) => {
    const y = CONTENT_TOP + i * 1.02;
    card(s, 6.1, y, 3.35, 0.88, { accent: C.mint });
    s.addText(st[0], {
      x: 6.28, y: y + 0.1, w: 1.2, h: 0.45,
      fontSize: 24, bold: true, color: C.deep, fontFace: FONT.head, margin: 0,
    });
    s.addText(st[1], {
      x: 7.45, y: y + 0.08, w: 1.85, h: 0.3,
      fontSize: 10, bold: true, color: C.navy, fontFace: FONT.body, margin: 0,
    });
    s.addText(st[2], {
      x: 7.45, y: y + 0.36, w: 1.85, h: 0.35,
      fontSize: 8, color: C.slate, fontFace: FONT.body, margin: 0,
    });
  });
  footer(s, 2);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 3 — Objective
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Program Objective", "One governed platform — four mutually reinforcing outcomes");
  const objs = [
    { n: "01", t: "Intelligent Resolution", d: "Automate eligible warranty inquiries with graph-backed diagnosis and guided troubleshooting — reducing unnecessary agent load." },
    { n: "02", t: "Safety & Policy Integrity", d: "Mandatory escalation on critical symptoms and low-confidence cases — automation never overrides human accountability." },
    { n: "03", t: "Agent Empowerment", d: "Deliver a complete diagnostic dossier — symptoms, ranked failure modes, steps tried, warranty context — before the agent speaks to the customer." },
    { n: "04", t: "Evidence-Led Operations", d: "Governed knowledge ingestion, lineage audit, and phase-gated metrics — so scale is earned, not assumed." },
  ];
  objs.forEach((o, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = ML + col * 4.55;
    const y = CONTENT_TOP + row * 1.62;
    card(s, x, y, 4.3, 1.45, { accent: C.teal });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.18, y: y + 0.18, w: 0.55, h: 0.55,
      fill: { color: C.sky },
    });
    s.addText(o.n, {
      x: x + 0.18, y: y + 0.26, w: 0.55, h: 0.4,
      fontSize: 14, bold: true, color: C.deep, align: "center", fontFace: FONT.head, margin: 0,
    });
    s.addText(o.t, {
      x: x + 0.88, y: y + 0.18, w: 3.25, h: 0.38,
      fontSize: 13, bold: true, color: C.navy, fontFace: FONT.body, margin: 0,
    });
    s.addText(o.d, {
      x: x + 0.18, y: y + 0.68, w: 3.95, h: 0.65,
      fontSize: 10, color: C.slate, fontFace: FONT.body, margin: 0, valign: "top",
    });
  });
  footer(s, 3);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 4 — Solution architecture
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Solution Architecture", "Layered platform connecting enterprise knowledge to customer outcomes");
  const layers = [
    { label: "Customer & Agent Channels", body: "Web  ·  Mobile  ·  Agent Desktop  ·  REST API  ·  Future IVR", bg: C.sky, h: 0.52 },
    { label: "Diagnostics Platform", body: "Agent Orchestration  →  GraphRAG Engine  →  Warranty Gate  →  Escalation & Case Handoff", bg: C.white, h: 0.56 },
    { label: "Knowledge Graph (Neo4j)", body: "Products  ·  Symptoms  ·  Failure Modes  ·  Diagnostic Steps  ·  Parts  ·  Field Evidence", bg: C.white, h: 0.56 },
    { label: "Knowledge Engineering (Batch)", body: "ETL Pipelines  ·  Ontology Builder  ·  SME Approval  ·  Smoke Validation  ·  Staging Promotion", bg: C.sky, h: 0.52 },
    { label: "Enterprise Systems of Record", body: "CRM  ·  PIM / PLM  ·  Field Service  ·  Claims  ·  Service Knowledge Base", bg: C.deep, h: 0.52, light: true },
  ];
  let y = CONTENT_TOP;
  layers.forEach((l, i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: ML + 0.35, y: y + l.h / 2 - 0.01, w: 0.35, h: 0.02,
      fill: { color: C.mint },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: ML, y, w: CW, h: l.h,
      fill: { color: l.bg },
      line: { color: C.sky, width: 0.75 },
    });
    s.addText(l.label, {
      x: ML + 0.15, y: y + 0.08, w: 2.4, h: l.h - 0.12,
      fontSize: 10, bold: true, color: l.light ? C.mint : C.deep,
      fontFace: FONT.body, margin: 0, valign: "middle",
    });
    s.addText(l.body, {
      x: ML + 2.55, y: y + 0.1, w: 6.2, h: l.h - 0.15,
      fontSize: 10, color: l.light ? C.sky : C.ink,
      fontFace: FONT.body, margin: 0, valign: "middle",
    });
    if (i < layers.length - 1) {
      s.addText("▼", {
        x: ML + 0.38, y: y + l.h - 0.02, w: 0.3, h: 0.2,
        fontSize: 8, color: C.teal, margin: 0,
      });
    }
    y += l.h + 0.09;
  });
  calloutBar(s, 4.58, "Design principle: the knowledge graph is the system of truth — generative AI augments presentation, not diagnosis authority.");
  footer(s, 4);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 5 — Why graph-first (two clean columns)
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Our Approach: Graph-First GraphRAG", "Structured, auditable reasoning for regulated warranty and repair advice");
  card(s, ML, CONTENT_TOP, 4.25, 3.15, { accent: C.teal });
  s.addText("Why this approach", {
    x: ML + 0.2, y: CONTENT_TOP + 0.12, w: 3.8, h: 0.3,
    fontSize: 12, bold: true, color: C.navy, fontFace: FONT.body, margin: 0,
  });
  const pros = [
    ["Grounding", "Symptom → failure relationships with explicit confidence scores"],
    ["Explainability", "Every output cites FMEA, manuals, or field service records"],
    ["Safety", "Critical severity bypasses automation; SME-governed content"],
    ["Integration", "Native alignment with CRM, product, field, and claims data"],
    ["Economics", "Predictable graph query cost at high volume vs. per-token LLM"],
  ];
  pros.forEach((pr, i) => {
    const y = CONTENT_TOP + 0.48 + i * 0.52;
    s.addText(pr[0], {
      x: ML + 0.2, y, w: 1.35, h: 0.42,
      fontSize: 10, bold: true, color: C.teal, fontFace: FONT.body, margin: 0,
    });
    s.addText(pr[1], {
      x: ML + 1.55, y, w: 2.55, h: 0.45,
      fontSize: 10, color: C.ink, fontFace: FONT.body, margin: 0, valign: "top",
    });
  });
  card(s, 5.05, CONTENT_TOP, 3.4, 3.15, { fill: C.navy, border: C.deep, shadow: false });
  s.addText("Alternatives we do not lead with", {
    x: 5.25, y: CONTENT_TOP + 0.15, w: 3.0, h: 0.32,
    fontSize: 11, bold: true, color: C.mint, fontFace: FONT.body, margin: 0,
  });
  s.addText(
    [
      { text: "LLM-only chat without authoritative graph truth", options: { bullet: true, breakLine: true, fontSize: 10, color: C.sky } },
      { text: "Static IVR trees across hundreds of product families", options: { bullet: true, breakLine: true, fontSize: 10, color: C.sky } },
      { text: "Vector search on PDF manuals without structured ranking", options: { bullet: true, breakLine: true, fontSize: 10, color: C.sky } },
      { text: "Maximum automation targets that ignore safety escalation", options: { bullet: true, fontSize: 10, color: C.sky } },
    ],
    { x: 5.2, y: CONTENT_TOP + 0.55, w: 3.1, h: 2.2, fontFace: FONT.body, paraSpaceAfter: 6 }
  );
  s.addText("LLM may enhance language — never replace graph evidence.", {
    x: 5.25, y: CONTENT_TOP + 2.65, w: 3.0, h: 0.35,
    fontSize: 9, italic: true, color: C.mint, fontFace: FONT.body, margin: 0,
  });
  footer(s, 5);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 6 — Operating model
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Operating Model", "Two velocities — governed batch ingestion and real-time diagnosis");
  const cols = [
    { x: ML, title: "Batch · Knowledge Engineering", color: C.deep, steps: ["Extract from PIM, FSM, Claims, CRM", "Transform to governed ontology", "SME review on safety-critical content", "Validate and load staging graph", "Smoke regression gate", "Promote approved batch to production"] },
    { x: 5.05, title: "Runtime · Customer Diagnosis", color: C.teal, steps: ["CRM asset binding & warranty check", "Product detection & symptom matching", "Failure mode ranking with confidence", "Severity and threshold evaluation", "Self-service steps or escalation", "Structured dossier to contact center"] },
  ];
  cols.forEach((c) => {
    card(s, c.x, CONTENT_TOP, 4.25, 2.72, { accent: c.color });
    s.addShape(pres.shapes.RECTANGLE, {
      x: c.x, y: CONTENT_TOP, w: 4.25, h: 0.48,
      fill: { color: c.color },
    });
    s.addText(c.title, {
      x: c.x + 0.15, y: CONTENT_TOP + 0.1, w: 3.95, h: 0.3,
      fontSize: 11, bold: true, color: C.white, fontFace: FONT.body, margin: 0,
    });
    c.steps.forEach((step, i) => {
      const y = CONTENT_TOP + 0.55 + i * 0.35;
      s.addShape(pres.shapes.OVAL, {
        x: c.x + 0.18, y: y + 0.06, w: 0.22, h: 0.22,
        fill: { color: C.sky },
      });
      s.addText(String(i + 1), {
        x: c.x + 0.18, y: y + 0.08, w: 0.22, h: 0.18,
        fontSize: 8, bold: true, color: C.deep, align: "center", fontFace: FONT.body, margin: 0,
      });
      s.addText(step, {
        x: c.x + 0.48, y, w: 3.55, h: 0.34,
        fontSize: 10, color: C.ink, fontFace: FONT.body, margin: 0, valign: "middle",
      });
    });
  });
  calloutBar(s, 4.52, "Runtime diagnosis is read-only against the approved graph — enabling audit, rollback, and compliance.");
  footer(s, 6);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 7 — Delivery methodology (horizontal phase cards)
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Delivery Methodology", "Evidence-gated phases — funding follows proof, not calendar");
  const phases = [
    { phase: "0", name: "Discover", dur: "Weeks 0–2", goal: "Align problem, map systems, register assumptions & client dependencies", gate: "Sponsor charter · SME commitment · data path identified" },
    { phase: "1", name: "Prove", dur: "Weeks 3–10", goal: "POC on limited product scope with real enterprise data & integrations", gate: "≥70% scenario accuracy · provenance complete · CRM read live" },
    { phase: "2", name: "Pilot", dur: "Weeks 11–18", goal: "MVP with live agents, case write-back, scheduled ETL, SSO", gate: "Override trending down · ETL reliable · KPI baseline beat" },
    { phase: "3", name: "Scale", dur: "Month 5+", goal: "Catalog expansion, HA platform, governance pipelines, regional rollout", gate: "Security sign-off · sustained accuracy · ops runbooks" },
  ];
  phases.forEach((ph, i) => {
    const x = ML + i * 2.22;
    card(s, x, CONTENT_TOP, 2.08, 2.55, { accent: i === 0 ? C.mint : C.teal });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.15, y: CONTENT_TOP + 0.15, w: 0.5, h: 0.5,
      fill: { color: C.deep },
    });
    s.addText(ph.phase, {
      x: x + 0.15, y: CONTENT_TOP + 0.22, w: 0.5, h: 0.38,
      fontSize: 16, bold: true, color: C.white, align: "center", fontFace: FONT.head, margin: 0,
    });
    s.addText(ph.name, {
      x: x + 0.72, y: CONTENT_TOP + 0.18, w: 1.25, h: 0.32,
      fontSize: 13, bold: true, color: C.navy, fontFace: FONT.body, margin: 0,
    });
    s.addText(ph.dur, {
      x: x + 0.72, y: CONTENT_TOP + 0.46, w: 1.25, h: 0.22,
      fontSize: 8, color: C.teal, fontFace: FONT.body, margin: 0,
    });
    s.addText(ph.goal, {
      x: x + 0.15, y: CONTENT_TOP + 0.78, w: 1.78, h: 1.0,
      fontSize: 9, color: C.ink, fontFace: FONT.body, margin: 0, valign: "top",
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.12, y: CONTENT_TOP + 1.88, w: 1.84, h: 0.52,
      fill: { color: C.cloud },
    });
    s.addText("Gate: " + ph.gate, {
      x: x + 0.18, y: CONTENT_TOP + 1.94, w: 1.72, h: 0.42,
      fontSize: 7.5, color: C.slate, fontFace: FONT.body, margin: 0, valign: "top",
    });
  });
  calloutBar(s, 4.35, "Each phase produces measurable evidence before the next is funded — protecting both client and delivery investment.");
  footer(s, 7);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 8 — Five pillars (2×2 + banner)
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Methodology Pillars", "Five principles that govern every phase of delivery");
  const pillars = [
    ["1", "Discover before build", "Validate problem, data, and landscape before scope commitment"],
    ["2", "Graph-truth before generation", "Structured retrieval is authoritative; LLM is optional UX only"],
    ["3", "Governed knowledge", "SME-approved ontology — safety content never self-certified"],
    ["4", "Right automation", "Escalate on uncertainty and critical severity by design"],
  ];
  pillars.forEach((pl, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = ML + col * 4.55;
    const y = CONTENT_TOP + row * 1.38;
    card(s, x, y, 4.3, 1.22, { accent: C.teal });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.18, y: y + 0.22, w: 0.42, h: 0.42,
      fill: { color: C.deep },
    });
    s.addText(pl[0], {
      x: x + 0.18, y: y + 0.3, w: 0.42, h: 0.28,
      fontSize: 12, bold: true, color: C.white, align: "center", fontFace: FONT.head, margin: 0,
    });
    s.addText(pl[1], {
      x: x + 0.72, y: y + 0.15, w: 3.4, h: 0.35,
      fontSize: 12, bold: true, color: C.navy, fontFace: FONT.body, margin: 0,
    });
    s.addText(pl[2], {
      x: x + 0.72, y: y + 0.48, w: 3.4, h: 0.6,
      fontSize: 10, color: C.slate, fontFace: FONT.body, margin: 0, valign: "top",
    });
  });
  card(s, ML, 4.38, CW, 0.48, { fill: C.navy, shadow: false });
  s.addText("5  ·  Phased proof", {
    x: ML + 0.2, y: 4.45, w: 2.0, h: 0.35,
    fontSize: 12, bold: true, color: C.mint, fontFace: FONT.body, margin: 0, valign: "middle",
  });
  s.addText("Expand catalog and channels only when phase gates and KPIs support scale — never on assumption alone.", {
    x: ML + 2.2, y: 4.45, w: 6.5, h: 0.35,
    fontSize: 10, color: C.sky, fontFace: FONT.body, margin: 0, valign: "middle",
  });
  footer(s, 8);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 9 — Integration
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Enterprise Integration", "Connected to your systems of record — not a standalone chatbot");
  s.addTable(
    [
      [
        { text: "System", options: { fill: { color: C.deep }, color: C.white, bold: true, fontSize: 10 } },
        { text: "Role in Platform", options: { fill: { color: C.deep }, color: C.white, bold: true, fontSize: 10 } },
        { text: "Integration Mode", options: { fill: { color: C.deep }, color: C.white, bold: true, fontSize: 10 } },
      ],
      ["CRM", "Customer identity, registered assets, warranty dates, case write-back", "Runtime + escalation"],
      ["PIM / PLM", "Product taxonomy, parts BOM, FMEA, service manual metadata", "Batch ETL"],
      ["Field Service (FSM)", "Confirmed repair outcomes, technician resolution notes", "Batch ETL"],
      ["Claims", "Policy rules, closed claim outcomes, eligibility reference", "Runtime gate + batch"],
      ["Contact Center", "Escalation routing, agent desktop, priority case creation", "Runtime handoff"],
    ],
    {
      x: ML, y: CONTENT_TOP, w: CW, colW: [1.35, 4.85, 2.7],
      fontSize: 9, fontFace: FONT.body,
      border: { type: "solid", color: C.sky, pt: 0.5 },
      rowH: [0.38, 0.42, 0.42, 0.42, 0.42, 0.42],
      align: "left", valign: "middle",
    }
  );
  card(s, ML, 4.05, 4.3, 0.58, { fill: C.sky, shadow: false });
  s.addText("Governance", {
    x: ML + 0.15, y: 4.12, w: 1.2, h: 0.4,
    fontSize: 10, bold: true, color: C.deep, fontFace: FONT.body, margin: 0, valign: "middle",
  });
  s.addText("Provenance  ·  SME approval  ·  Smoke gates  ·  PII boundary  ·  Lineage audit", {
    x: ML + 1.35, y: 4.15, w: 2.8, h: 0.38,
    fontSize: 9, color: C.ink, fontFace: FONT.body, margin: 0, valign: "middle",
  });
  card(s, 5.15, 4.05, 3.3, 0.58, { fill: C.navy, shadow: false });
  s.addText("Human-in-the-loop by design — escalation is success, not failure.", {
    x: 5.3, y: 4.15, w: 3.0, h: 0.38,
    fontSize: 10, bold: true, color: C.mint, fontFace: FONT.body, margin: 0, valign: "middle",
  });
  footer(s, 9);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 10 — Success metrics
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Measuring Success", "Evidence-based KPIs tied to phase gates — baselines set in discovery");
  const rows = [
    ["Discover", "Current AHT, tier-1 volume, escalation rate documented", "Assumption register agreed with sponsors"],
    ["Prove (POC)", "Top-1 failure mode accuracy on client scenario pack", "100% provenance on escalated cases"],
    ["Pilot (MVP)", "Agent override rate trending down", "Escalated AHT vs. baseline · tier-1 deflection"],
    ["Scale", "Regional accuracy on governed catalog", "Platform SLOs · ETL reliability ≥99.5%"],
  ];
  s.addTable(
    [
      [
        { text: "Phase", options: { fill: { color: C.teal }, color: C.white, bold: true } },
        { text: "Primary evidence required", options: { fill: { color: C.teal }, color: C.white, bold: true } },
        { text: "Secondary indicators", options: { fill: { color: C.teal }, color: C.white, bold: true } },
      ],
      ...rows,
    ],
    {
      x: ML, y: CONTENT_TOP, w: CW, colW: [1.2, 4.2, 3.5],
      fontSize: 10, fontFace: FONT.body,
      border: { type: "solid", color: C.sky, pt: 0.5 },
      rowH: [0.4, 0.55, 0.55, 0.55, 0.55],
      align: "left", valign: "middle",
    }
  );
  card(s, ML, 3.95, CW, 0.62, { fill: C.cloud, shadow: false });
  s.addText("We do not commit executive ROI targets until pilot data exists — directional ranges are planning hypotheses only.", {
    x: ML + 0.2, y: 4.08, w: CW - 0.4, h: 0.38,
    fontSize: 10, italic: true, color: C.slate, fontFace: FONT.body, margin: 0, valign: "middle",
  });
  footer(s, 10);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 11 — Partnership
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  header(s, "Partnership Model", "A joint program — your organization and ours, with clear accountabilities");
  const partners = [
    { you: "Executive Sponsor", us: "Program charter, phase gates, SME time, sandbox access", them: "Methodology leadership, architecture, delivery management" },
    { you: "Service Engineering SMEs", us: "Symptom catalog, safety approval, failure mode validation", them: "Knowledge engineering, ontology design, evaluation harness" },
    { you: "IT / Integration Teams", us: "CRM, PIM, FSM, Claims connectivity and credentials", them: "Connector development, contract tests, API abstraction" },
    { you: "Contact Center Leadership", us: "Escalation policy, agent pilot, dossier feedback", them: "Agent UI, case handoff, override analytics" },
    { you: "Data Governance & Legal", us: "Source ownership, PII boundary, retention policy", them: "Provenance model, lineage store, compliance alignment" },
  ];
  s.addTable(
    [
      [
        { text: "Domain", options: { fill: { color: C.deep }, color: C.white, bold: true, fontSize: 9 } },
        { text: "Your organization provides", options: { fill: { color: C.deep }, color: C.white, bold: true, fontSize: 9 } },
        { text: "Our team delivers", options: { fill: { color: C.deep }, color: C.white, bold: true, fontSize: 9 } },
      ],
      ...partners.map((p) => [p.you, p.us, p.them]),
    ],
    {
      x: ML, y: CONTENT_TOP, w: CW, colW: [1.5, 3.7, 3.7],
      fontSize: 9, fontFace: FONT.body,
      border: { type: "solid", color: C.sky, pt: 0.5 },
      rowH: [0.36, 0.48, 0.48, 0.48, 0.48, 0.48],
      align: "left", valign: "middle",
    }
  );
  footer(s, 11);
}

// ═══════════════════════════════════════════════════════════════
// SLIDE 12 — World-class close
// ═══════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Right accent panel
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.85, y: 0, w: 4.15, h: SLIDE_H,
    fill: { color: C.deep },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.12, h: SLIDE_H,
    fill: { color: C.mint },
  });

  s.addText("Recommended\nPath Forward", {
    x: 0.55, y: 0.45, w: 5.0, h: 1.0,
    fontSize: 30, bold: true, color: C.white, fontFace: FONT.head, margin: 0,
  });
  s.addText("A structured 90-day engagement to validate the approach on your data — before scale commitment.", {
    x: 0.55, y: 1.42, w: 5.1, h: 0.55,
    fontSize: 12, color: C.sky, fontFace: FONT.body, margin: 0,
  });

  const milestones = [
    { wk: "30 days", title: "Discover & Align", items: "Executive workshop · Source system mapping · Assumption register · Privacy boundary" },
    { wk: "60 days", title: "Prove Value", items: "Ontology v1 · Live CRM read · First product families on graph · Accuracy benchmark" },
    { wk: "90 days", title: "Decision Point", items: "POC readout · Agent dossier review · Pilot charter · Go / refine / pause recommendation" },
  ];
  milestones.forEach((m, i) => {
    const y = 2.15 + i * 0.95;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.55, y, w: 5.15, h: 0.82,
      fill: { color: C.teal, transparency: 15 },
      line: { color: C.mint, width: 0.5 },
    });
    s.addText(m.wk, {
      x: 0.7, y: y + 0.1, w: 0.85, h: 0.6,
      fontSize: 9, bold: true, color: C.mint, fontFace: FONT.body, margin: 0, valign: "top",
    });
    s.addText(m.title, {
      x: 1.55, y: y + 0.08, w: 1.6, h: 0.3,
      fontSize: 12, bold: true, color: C.white, fontFace: FONT.body, margin: 0,
    });
    s.addText(m.items, {
      x: 1.55, y: y + 0.36, w: 3.95, h: 0.4,
      fontSize: 9, color: C.sky, fontFace: FONT.body, margin: 0, valign: "top",
    });
  });

  // Right panel — decision ask
  s.addText("Decision we seek", {
    x: 6.1, y: 0.55, w: 3.5, h: 0.35,
    fontSize: 14, bold: true, color: C.mint, fontFace: FONT.body, margin: 0,
  });
  s.addText(
    [
      { text: "Sponsor nomination and steering cadence", options: { bullet: true, breakLine: true, fontSize: 11, color: C.white } },
      { text: "CRM sandbox access within 10 business days", options: { bullet: true, breakLine: true, fontSize: 11, color: C.white } },
      { text: "Service engineering SME — 4 hrs/week during Prove phase", options: { bullet: true, breakLine: true, fontSize: 11, color: C.white } },
      { text: "Agreement to evidence-gated phases — not fixed big-bang scope", options: { bullet: true, fontSize: 11, color: C.white } },
    ],
    { x: 6.05, y: 1.0, w: 3.65, h: 1.85, fontFace: FONT.body, paraSpaceAfter: 8 }
  );

  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.05, y: 3.05, w: 3.65, h: 1.35,
    fill: { color: C.navy },
    line: { color: C.mint, width: 1.5 },
  });
  s.addText("What you receive at 90 days", {
    x: 6.2, y: 3.15, w: 3.35, h: 0.3,
    fontSize: 11, bold: true, color: C.mint, fontFace: FONT.body, margin: 0,
  });
  s.addText("Validated accuracy report · Working integration path · Agent-ready dossier · Pilot business case with measured velocity — not slides.", {
    x: 6.2, y: 3.48, w: 3.35, h: 0.8,
    fontSize: 10, color: C.sky, fontFace: FONT.body, margin: 0, valign: "top",
  });

  // Bottom CTA bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 4.85, w: 10, h: 0.775,
    fill: { color: C.mint },
  });
  s.addText("Let's begin with discovery.", {
    x: 0.55, y: 5.0, w: 4.5, h: 0.45,
    fontSize: 20, bold: true, color: C.navy, fontFace: FONT.head, margin: 0,
  });
  s.addText("Proposed next session: Executive alignment workshop (90 minutes)", {
    x: 5.2, y: 5.08, w: 4.5, h: 0.35,
    fontSize: 11, color: C.navy, align: "right", fontFace: FONT.body, margin: 0,
  });
}

pres.writeFile({ fileName: OUT }).then(() => console.log(`Written: ${OUT}`));