// LLMOps Handbook -> PDF renderer
// - Markdown -> HTML (markdown-it) with tables, heading anchors, KaTeX math
// - ```mermaid fences rendered to vector SVG in headless Chrome (Mermaid v11)
// - cross-document .md links rewritten to .pdf
// - high-fidelity, human-readable diagrams scaled to page width
import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import MarkdownIt from 'markdown-it';
import anchor from 'markdown-it-anchor';
import katexPlugin from '@vscode/markdown-it-katex';
import puppeteer from 'puppeteer-core';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC_DIR = join(__dirname, '..');
const OUT_DIR = join(__dirname, '..', 'pdf');
const NM = join(__dirname, 'node_modules');

// Auto-detect a Chrome for Testing binary from the puppeteer cache.
function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = `${process.env.HOME}/.cache/puppeteer/chrome`;
  if (!existsSync(base)) throw new Error('No Chrome for Testing found; set CHROME_PATH.');
  const dirs = readdirSync(base).filter(d => d.startsWith('mac') || d.startsWith('linux') || d.startsWith('win')).sort().reverse();
  for (const d of dirs) {
    for (const rel of [
      'chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
      'chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
      'chrome-linux64/chrome', 'chrome-win64/chrome.exe',
    ]) {
      const p = join(base, d, rel);
      if (existsSync(p)) return p;
    }
  }
  throw new Error('No Chrome for Testing binary located; set CHROME_PATH.');
}
const CHROME = findChrome();

const katexCssUrl = pathToFileURL(join(NM, 'katex', 'dist', 'katex.min.css')).href;
const mermaidJsUrl = pathToFileURL(join(NM, 'mermaid', 'dist', 'mermaid.min.js')).href;

const md = new MarkdownIt({ html: true, linkify: true, typographer: false, breaks: false });
md.use(anchor, { permalink: false, tabIndex: false });
md.use(katexPlugin.default || katexPlugin);

// Render ```mermaid fences as <pre class="mermaid"> with escaped text content.
const escapeHtml = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const defaultFence = md.renderer.rules.fence.bind(md.renderer.rules);
md.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const info = (token.info || '').trim().toLowerCase();
  if (info === 'mermaid') {
    return `<div class="mermaid-wrap"><pre class="mermaid">${escapeHtml(token.content)}</pre></div>\n`;
  }
  return defaultFence(tokens, idx, options, env, self);
};

function buildHtml(mdText, title) {
  let body = md.render(mdText);
  // cross-doc links: .md -> .pdf (preserve anchors)
  body = body.replace(/href="([^"]+?)\.md(#[^"]*)?"/g, (m, p, hash) => `href="${p}.pdf${hash || ''}"`);
  // task-list checkboxes -> unicode (tight lists)
  body = body.replace(/<li>\[ \] /g, '<li class="task">\u2610 ')
             .replace(/<li>\[[xX]\] /g, '<li class="task">\u2611 ');
  return `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>${title}</title>
<link rel="stylesheet" href="${katexCssUrl}">
<style>
  @page { size: A4; margin: 16mm 14mm 18mm 14mm; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  html { font-size: 10.5pt; }
  body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
         color: #1a1f26; line-height: 1.5; margin: 0; }
  h1, h2, h3, h4 { color: #0b3d5c; line-height: 1.25; margin: 1.1em 0 0.5em; }
  h1 { font-size: 1.9rem; border-bottom: 3px solid #0b3d5c; padding-bottom: .25em; }
  h2 { font-size: 1.4rem; border-bottom: 1px solid #d0d7de; padding-bottom: .2em; margin-top: 1.5em; }
  h3 { font-size: 1.15rem; }
  h2, h3, h4 { break-after: avoid; }
  p, li { orphans: 3; widows: 3; }
  a { color: #0969da; text-decoration: none; }
  blockquote { border-left: 4px solid #0b3d5c33; background: #f3f7fa;
               margin: 1em 0; padding: .5em 1em; border-radius: 4px; break-inside: avoid; }
  code { font-family: "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
         font-size: .84em; background: #eef1f4; padding: .12em .35em; border-radius: 4px; }
  pre { background: #0f172a; color: #e2e8f0; padding: 12px 14px; border-radius: 8px;
        overflow: hidden; white-space: pre-wrap; word-break: break-word;
        font-size: .78rem; line-height: 1.45; break-inside: avoid; }
  pre code { background: none; color: inherit; padding: 0; font-size: 1em; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .82rem; break-inside: auto; }
  th, td { border: 1px solid #cdd5df; padding: 6px 9px; text-align: left; vertical-align: top; }
  thead th { background: #0b3d5c; color: #fff; }
  tbody tr:nth-child(even) { background: #f5f8fa; }
  tr { break-inside: avoid; }
  ul, ol { padding-left: 1.4em; }
  li.task { list-style: none; margin-left: -1.1em; }
  hr { border: none; border-top: 1px solid #d0d7de; margin: 1.5em 0; }
  .mermaid-wrap { text-align: center; margin: 1.2em 0; break-inside: avoid; }
  .mermaid { background: transparent; color: #1a1f26; }
  .mermaid svg { max-width: 100%; height: auto; }
  .katex { font-size: 1.02em; }
</style></head>
<body>
${body}
<script src="${mermaidJsUrl}"></script>
<script>
  window.__renderDone = false;
  (async () => {
    try {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'neutral',
        securityLevel: 'loose',
        flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
        themeVariables: { fontFamily: 'Helvetica, Arial, sans-serif', fontSize: '15px' }
      });
      await mermaid.run({ querySelector: '.mermaid' });
    } catch (e) {
      document.body.setAttribute('data-mmd-error', (e && e.message) || '1');
    } finally {
      window.__renderDone = true;
    }
  })();
</script>
</body></html>`;
}

async function main() {
  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });
  const files = readdirSync(SRC_DIR).filter(f => /^\d\d-.*\.md$/.test(f)).sort();
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
  });
  const only = process.argv[2]; // optional single-file filter
  for (const f of files) {
    if (only && !f.includes(only)) continue;
    const mdText = readFileSync(join(SRC_DIR, f), 'utf8');
    const html = buildHtml(mdText, f.replace(/\.md$/, ''));
    // Write to a real file so file:// subresources (mermaid.js, katex.css) load
    // with a proper file origin (setContent's about:blank origin blocks them).
    const tmpPath = join(__dirname, `.tmp-${f}.html`);
    writeFileSync(tmpPath, html);
    const page = await browser.newPage();
    await page.goto(pathToFileURL(tmpPath).href, { waitUntil: 'networkidle0', timeout: 120000 });
    await page.waitForFunction('window.__renderDone === true', { timeout: 120000 });
    // settle fonts/layout
    await new Promise(r => setTimeout(r, 350));
    // validate every mermaid block produced an SVG
    const diag = await page.evaluate(() => ({
      blocks: document.querySelectorAll('.mermaid').length,
      svgs: document.querySelectorAll('.mermaid svg').length,
      err: document.body.getAttribute('data-mmd-error') || ''
    }));
    if (diag.err || diag.blocks !== diag.svgs) {
      console.error(`  !! ${f}: mermaid blocks=${diag.blocks} svgs=${diag.svgs} err=${diag.err}`);
    }
    const outPath = join(OUT_DIR, f.replace(/\.md$/, '.pdf'));
    await page.pdf({
      path: outPath, format: 'A4', printBackground: true,
      margin: { top: '16mm', bottom: '18mm', left: '14mm', right: '14mm' },
      displayHeaderFooter: true,
      headerTemplate: '<span></span>',
      footerTemplate:
        '<div style="width:100%;font-size:8px;color:#8a94a6;padding:0 14mm;display:flex;justify-content:space-between;">' +
        '<span>The Enterprise LLMOps Handbook</span>' +
        '<span class="pageNumber"></span>/<span class="totalPages"></span></div>'
    });
    await page.close();
    unlinkSync(tmpPath);
    console.log('rendered', basename(outPath));
  }
  await browser.close();
  console.log('DONE');
}
main().catch(e => { console.error(e); process.exit(1); });
