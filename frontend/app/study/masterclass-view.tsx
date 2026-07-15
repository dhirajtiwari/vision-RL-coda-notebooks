"use client";

import React, { useEffect, useMemo, useState } from "react";
import { BookOpen, ChevronLeft, Eye, EyeOff, Layers, ListTree, PencilLine } from "lucide-react";
import type { Masterclass, MemoryCard } from "@/lib/study/types";
import { api } from "@/lib/api";
import { FlashcardsDrill, TestDrill } from "./masterclass-drill";

/* ------------------------------------------------------------------ *
 * A small, dependency-free markdown renderer tuned for these verbatim
 * guides: headings, fenced code, tables, blockquotes, lists, inline
 * bold + code. Faithful to the source text (good for memorization).
 * ------------------------------------------------------------------ */

function renderInline(text: string, keyBase: string): React.ReactNode[] {
  // Split on `code` and **bold** while keeping delimiters.
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((p, i) => {
    const key = `${keyBase}-${i}`;
    if (p.startsWith("`") && p.endsWith("`")) {
      return (
        <code
          key={key}
          className="rounded bg-white/10 px-1 py-0.5 font-mono text-[0.85em] text-emerald-200"
        >
          {p.slice(1, -1)}
        </code>
      );
    }
    if (p.startsWith("**") && p.endsWith("**")) {
      return (
        <strong key={key} className="font-semibold text-white">
          {p.slice(2, -2)}
        </strong>
      );
    }
    return <React.Fragment key={key}>{p}</React.Fragment>;
  });
}

interface Block {
  type: "code" | "table" | "heading" | "quote" | "list" | "p" | "hr";
  level?: number;
  lang?: string;
  lines: string[];
}

function parseBlocks(md: string): Block[] {
  const rawLines = md.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  while (i < rawLines.length) {
    const line = rawLines[i];

    // Fenced code
    if (line.trimStart().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const body: string[] = [];
      i++;
      while (i < rawLines.length && !rawLines[i].trimStart().startsWith("```")) {
        body.push(rawLines[i]);
        i++;
      }
      i++; // skip closing fence
      blocks.push({ type: "code", lang, lines: body });
      continue;
    }

    // Table (consecutive lines starting with |)
    if (line.trimStart().startsWith("|")) {
      const rows: string[] = [];
      while (i < rawLines.length && rawLines[i].trimStart().startsWith("|")) {
        rows.push(rawLines[i].trim());
        i++;
      }
      blocks.push({ type: "table", lines: rows });
      continue;
    }

    // Heading
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      blocks.push({ type: "heading", level: h[1].length, lines: [h[2]] });
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith(">")) {
      const body: string[] = [];
      while (i < rawLines.length && rawLines[i].startsWith(">")) {
        body.push(rawLines[i].replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({ type: "quote", lines: body });
      continue;
    }

    // List (- or N.)
    if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const body: string[] = [];
      while (i < rawLines.length && /^\s*([-*]|\d+\.)\s+/.test(rawLines[i])) {
        body.push(rawLines[i].replace(/^\s*([-*]|\d+\.)\s+/, ""));
        i++;
      }
      blocks.push({ type: "list", lines: body });
      continue;
    }

    // Blank line
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Paragraph (accumulate until blank/structural)
    const body: string[] = [];
    while (
      i < rawLines.length &&
      rawLines[i].trim() !== "" &&
      !rawLines[i].trimStart().startsWith("```") &&
      !rawLines[i].trimStart().startsWith("|") &&
      !/^(#{1,6})\s+/.test(rawLines[i]) &&
      !rawLines[i].startsWith(">") &&
      !/^\s*([-*]|\d+\.)\s+/.test(rawLines[i])
    ) {
      body.push(rawLines[i]);
      i++;
    }
    blocks.push({ type: "p", lines: body });
  }
  return blocks;
}

function Table({ rows, bk }: Readonly<{ rows: string[]; bk: string }>) {
  const cells = rows
    .filter((r) => !/^\|[\s:|-]+\|?$/.test(r)) // drop the |---|---| separator
    .map((r) =>
      r
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((c) => c.trim()),
    );
  if (cells.length === 0) return null;
  const [head, ...body] = cells;
  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-left text-[13px] border-collapse">
        <thead>
          <tr>
            {head.map((c, ci) => (
              <th
                key={`${bk}-h-${ci}`}
                className="border border-white/10 bg-white/[0.04] px-2 py-1.5 font-semibold text-white/90"
              >
                {renderInline(c, `${bk}-h-${ci}`)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, ri) => (
            <tr key={`${bk}-r-${ri}`}>
              {row.map((c, ci) => (
                <td
                  key={`${bk}-r-${ri}-${ci}`}
                  className="border border-white/10 px-2 py-1.5 text-white/75 align-top"
                >
                  {renderInline(c, `${bk}-r-${ri}-${ci}`)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MiniMarkdown({ text }: Readonly<{ text: string }>) {
  const blocks = useMemo(() => parseBlocks(text), [text]);
  return (
    <div className="space-y-2.5 leading-relaxed text-[14px] text-white/80">
      {blocks.map((b, bi) => {
        const bk = `b-${bi}`;
        if (b.type === "code") {
          return (
            <pre
              key={bk}
              className="rounded-lg bg-[#0a0a0f] border border-white/10 p-3 text-[12px] font-mono text-emerald-100/90 whitespace-pre overflow-x-auto"
            >
              {b.lines.join("\n")}
            </pre>
          );
        }
        if (b.type === "table") return <Table key={bk} rows={b.lines} bk={bk} />;
        if (b.type === "heading") {
          const lvl = b.level || 2;
          const cls =
            lvl <= 1
              ? "text-lg font-bold text-white mt-4"
              : lvl === 2
                ? "text-base font-bold text-emerald-200 mt-4 border-t border-white/10 pt-3"
                : "text-sm font-semibold text-white/90 mt-3";
          return (
            <div key={bk} className={cls}>
              {renderInline(b.lines[0], bk)}
            </div>
          );
        }
        if (b.type === "quote") {
          return (
            <blockquote
              key={bk}
              className="border-l-2 border-emerald-500/50 bg-emerald-500/[0.04] pl-3 py-1.5 italic text-white/75"
            >
              {b.lines.map((l, li) => (
                <p key={`${bk}-${li}`}>{renderInline(l, `${bk}-${li}`)}</p>
              ))}
            </blockquote>
          );
        }
        if (b.type === "list") {
          return (
            <ul key={bk} className="list-disc pl-5 space-y-1">
              {b.lines.map((l, li) => (
                <li key={`${bk}-${li}`}>{renderInline(l, `${bk}-${li}`)}</li>
              ))}
            </ul>
          );
        }
        return (
          <p key={bk}>{renderInline(b.lines.join(" "), bk)}</p>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Reader with a memorize (blur/reveal) mode + section jump-nav.
 * ------------------------------------------------------------------ */
export default function MasterclassReader({
  mc,
  onBack,
}: Readonly<{ mc: Masterclass; onBack: () => void }>) {
  const [blur, setBlur] = useState(false);
  const [showNav, setShowNav] = useState(false);
  const [mode, setMode] = useState<"read" | "cards" | "test">("read");
  const [cards, setCards] = useState<MemoryCard[]>([]);
  const [cardsLoaded, setCardsLoaded] = useState(false);

  useEffect(() => {
    let alive = true;
    setCardsLoaded(false);
    api
      .studyMasterclassCards(mc.id)
      .then((r) => {
        if (alive) {
          setCards(r.cards || []);
          setCardsLoaded(true);
        }
      })
      .catch(() => {
        if (alive) setCardsLoaded(true);
      });
    return () => {
      alive = false;
    };
  }, [mc.id]);

  const sections = useMemo(() => {
    // Split body into ## PART sections for jump-nav + per-section reveal.
    const lines = mc.body.split("\n");
    const out: { title: string; anchor: string; body: string }[] = [];
    let cur: { title: string; anchor: string; body: string } | null = null;
    let inCode = false;
    for (const line of lines) {
      if (line.trimStart().startsWith("```")) inCode = !inCode;
      const m = !inCode ? /^##\s+(.*)$/.exec(line) : null;
      if (m) {
        if (cur) out.push(cur);
        cur = { title: m[1], anchor: `sec-${out.length}`, body: line + "\n" };
      } else if (cur) {
        cur.body += line + "\n";
      } else {
        cur = { title: "Intro", anchor: "sec-0", body: line + "\n" };
      }
    }
    if (cur) out.push(cur);
    return out;
  }, [mc.body]);

  return (
    <div className="max-w-[880px] mx-auto px-4 py-6">
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 text-xs border border-white/15 rounded-lg px-2.5 py-1.5 text-white/70 hover:bg-white/5"
        >
          <ChevronLeft size={14} /> All guides
        </button>
        <div className="flex rounded-lg border border-white/15 overflow-hidden text-xs">
          {(
            [
              ["read", "Read", BookOpen],
              ["cards", "Flashcards", Layers],
              ["test", "Test", PencilLine],
            ] as const
          ).map(([m, label, Icon]) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              aria-pressed={mode === m}
              className={`px-3 py-1.5 inline-flex items-center gap-1 ${
                mode === m ? "bg-emerald-600 text-white" : "bg-white/5 text-white/60"
              }`}
            >
              <Icon size={12} /> {label}
            </button>
          ))}
        </div>
        {mode === "read" && (
          <>
            <button
              type="button"
              onClick={() => setBlur((b) => !b)}
              aria-pressed={blur}
              title="Memorize mode: blur the text, then click to reveal and check yourself"
              className={`inline-flex items-center gap-1 text-xs border rounded-lg px-2.5 py-1.5 ${
                blur
                  ? "border-amber-500/50 bg-amber-600/20 text-amber-200"
                  : "border-white/15 text-white/70 hover:bg-white/5"
              }`}
            >
              {blur ? <EyeOff size={14} /> : <Eye size={14} />} Memorize mode
            </button>
            <button
              type="button"
              onClick={() => setShowNav((s) => !s)}
              className="inline-flex items-center gap-1 text-xs border border-white/15 rounded-lg px-2.5 py-1.5 text-white/70 hover:bg-white/5"
            >
              <ListTree size={14} /> Sections
            </button>
          </>
        )}
      </div>

      <h1 className="text-xl font-bold text-white">{mc.title}</h1>
      {mc.subtitle && <p className="text-sm text-white/55 mt-1">{mc.subtitle}</p>}
      <div className="mt-1 text-[11px] text-white/40">
        ~{mc.estimated_minutes} min · {(mc.char_count ?? mc.body?.length ?? 0).toLocaleString()} chars
        · memorize verbatim
      </div>

      {(mode === "cards" || mode === "test") && !cardsLoaded && (
        <div className="mt-4 text-sm text-white/40">Loading cards…</div>
      )}

      {mode === "cards" && cardsLoaded && (
        <div className="mt-4">
          <FlashcardsDrill cards={cards} mcId={mc.id} />
        </div>
      )}

      {mode === "test" && cardsLoaded && (
        <div className="mt-4">
          <TestDrill cards={cards} />
        </div>
      )}

      {mode === "read" && showNav && (
        <nav className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <ul className="space-y-1 text-[13px]">
            {sections.map((s) => (
              <li key={s.anchor}>
                <a href={`#${s.anchor}`} className="text-sky-300 hover:underline">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}

      {mode === "read" && (
        <div className="mt-4 space-y-6">
          {sections.map((s) => (
            <section key={s.anchor} id={s.anchor}>
              <div
                className={
                  blur
                    ? "blur-sm hover:blur-none focus-within:blur-none transition-all duration-150 cursor-pointer"
                    : ""
                }
                title={blur ? "Recall it, then hover to reveal" : undefined}
              >
                <MiniMarkdown text={s.body} />
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
