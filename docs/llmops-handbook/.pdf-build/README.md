# PDF build for the Enterprise LLMOps Handbook

Renders every `NN-*.md` chapter in `../` to a matching PDF in `../pdf/`, with
Mermaid diagrams rendered as crisp vector SVG (headless Chrome + Mermaid v11)
and KaTeX math, plus cross-document `.md`→`.pdf` link rewriting.

## Regenerate the PDFs

```bash
cd docs/llmops-handbook/.pdf-build
npm install            # first time only (installs markdown-it, mermaid, katex, puppeteer-core)
node render.mjs        # build all chapters -> ../pdf/*.pdf
node render.mjs 14     # build only files whose name contains "14"
```

Chrome for Testing is auto-detected from the puppeteer cache
(`~/.cache/puppeteer/chrome`). Override with `CHROME_PATH=/path/to/chrome`.

Output validation: the script prints a `!!` line if any Mermaid block fails to
produce an SVG. A clean run prints only `rendered …` lines and `DONE`.
