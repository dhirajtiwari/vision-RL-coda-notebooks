"use client";

import React, { useMemo, useState } from "react";
import {
  Check,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Eye,
  RotateCcw,
  Shuffle,
  X,
} from "lucide-react";
import type { MemoryCard } from "@/lib/study/types";

const W_FIELDS: { key: keyof MemoryCard; label: string }[] = [
  { key: "what", label: "What" },
  { key: "how", label: "How" },
  { key: "where", label: "Where" },
  { key: "when", label: "When" },
  { key: "who", label: "Who" },
  { key: "why", label: "Why" },
];

/* ---------------- grading helpers (mirror the backend) ---------------- */
function norm(s: string): string {
  return (s || "")
    .toLowerCase()
    .replace(/[`'"();,.]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
function blankMatch(given: string, expected: string): boolean {
  const g = norm(given);
  const e = norm(expected);
  if (!e) return !g;
  if (g === e) return true;
  const gt = new Set(g.split(" ").filter(Boolean));
  const et = e.split(" ").filter(Boolean);
  return et.length > 1 && et.every((t) => gt.has(t)) && gt.size === et.length;
}
/** line-aware similarity 0..1 for write-it tests */
function codeScore(given: string, expected: string): number {
  const gLines = given.split("\n").map(norm).filter(Boolean);
  const eLines = expected.split("\n").map(norm).filter(Boolean);
  if (eLines.length === 0) return given.trim() ? 0 : 1;
  const gset = gLines.slice();
  let hit = 0;
  for (const el of eLines) {
    const idx = gset.findIndex((gl) => gl === el || (el.length > 6 && gl.includes(el)));
    if (idx >= 0) {
      hit++;
      gset.splice(idx, 1);
    }
  }
  return Math.round((hit / eLines.length) * 100) / 100;
}

const KIND_COLOR: Record<string, string> = {
  concept: "text-sky-300 bg-sky-500/15",
  line: "text-emerald-300 bg-emerald-500/15",
  block: "text-amber-300 bg-amber-500/15",
  pattern: "text-fuchsia-300 bg-fuchsia-500/15",
};

/* ============================ FLASHCARDS ============================ */
export function FlashcardsDrill({ cards, mcId }: Readonly<{ cards: MemoryCard[]; mcId: string }>) {
  const sections = useMemo(() => Array.from(new Set(cards.map((c) => c.section))), [cards]);
  const [section, setSection] = useState<string>("all");
  const [order, setOrder] = useState<number[]>([]);
  const [pos, setPos] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState<Record<string, boolean>>(() => {
    if (typeof window === "undefined") return {};
    try {
      return JSON.parse(localStorage.getItem(`mc-known-${mcId}`) || "{}");
    } catch {
      return {};
    }
  });

  const pool = useMemo(
    () => cards.filter((c) => section === "all" || c.section === section),
    [cards, section],
  );

  // keep order in sync with pool
  const effectiveOrder = order.length === pool.length ? order : pool.map((_, i) => i);
  const card = pool[effectiveOrder[pos] ?? 0];

  const setKnownFor = (id: string, val: boolean) => {
    const next = { ...known, [id]: val };
    setKnown(next);
    try {
      localStorage.setItem(`mc-known-${mcId}`, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  };

  const go = (d: number) => {
    setFlipped(false);
    setPos((p) => Math.max(0, Math.min(pool.length - 1, p + d)));
  };
  const shuffle = () => {
    const idx = pool.map((_, i) => i);
    for (let i = idx.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [idx[i], idx[j]] = [idx[j], idx[i]];
    }
    setOrder(idx);
    setPos(0);
    setFlipped(false);
  };

  if (!card) return <div className="text-sm text-white/50">No cards.</div>;
  const knownCount = pool.filter((c) => known[c.id]).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap text-xs">
        <select
          value={section}
          onChange={(e) => {
            setSection(e.target.value);
            setPos(0);
            setOrder([]);
            setFlipped(false);
          }}
          className="rounded-lg border border-white/15 bg-white/5 px-2 py-1.5"
        >
          <option value="all">All sections ({cards.length})</option>
          {sections.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={shuffle}
          className="inline-flex items-center gap-1 rounded-lg border border-white/15 px-2 py-1.5 text-white/70 hover:bg-white/5"
        >
          <Shuffle size={12} /> Shuffle
        </button>
        <span className="text-white/45">
          {pos + 1}/{pool.length} · known {knownCount}/{pool.length}
        </span>
      </div>

      <button
        type="button"
        onClick={() => setFlipped((f) => !f)}
        className="w-full text-left rounded-2xl border border-white/12 bg-gradient-to-br from-emerald-500/[0.07] to-transparent p-5 min-h-[220px]"
      >
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`text-[10px] uppercase tracking-wide rounded px-1.5 py-0.5 ${KIND_COLOR[card.kind] || ""}`}
          >
            {card.kind}
          </span>
          <span className="text-[11px] text-white/40">{card.section}</span>
        </div>
        <div className="text-[15px] font-medium text-white">{card.front}</div>

        {!flipped ? (
          <div className="mt-6 text-xs text-white/40">
            Click to reveal code, 5W+H, pitfalls & sources ↵
          </div>
        ) : (
          <div className="mt-3 space-y-3">
            {card.code && (
              <pre className="rounded-lg bg-[#0a0a0f] border border-white/10 p-3 text-[12px] font-mono text-emerald-100/90 whitespace-pre overflow-x-auto">
                {card.code}
              </pre>
            )}
            {card.explain && <p className="text-[13px] text-white/75">{card.explain}</p>}
            {card.mental_model && (
              <p className="text-[13px] text-sky-200/90">🧠 Mental model: {card.mental_model}</p>
            )}
            {card.memory_hook && (
              <p className="text-[13px] text-amber-200/90">🔑 Memory hook: {card.memory_hook}</p>
            )}
            {W_FIELDS.some(({ key }) => {
              const v = card[key];
              return typeof v === "string" && v.length > 0;
            }) && (
              <div className="space-y-2 pt-1 border-t border-white/10">
                <div className="text-[11px] uppercase tracking-wide text-emerald-300/80">
                  5W + H
                </div>
                {W_FIELDS.map(({ key, label }) => {
                  const val = card[key];
                  if (!val || typeof val !== "string") return null;
                  return (
                    <div key={key}>
                      <div className="text-[11px] font-semibold text-emerald-300/90 uppercase tracking-wide">
                        {label}
                      </div>
                      <div className="text-[13px] text-white/80 leading-relaxed">{val}</div>
                    </div>
                  );
                })}
              </div>
            )}
            {!!card.pitfalls?.length && (
              <div>
                <div className="text-[11px] font-semibold text-rose-300/90 uppercase">Pitfalls</div>
                <ul className="list-disc pl-5 text-[13px] text-white/70">
                  {card.pitfalls.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </div>
            )}
            {card.run_hint && (
              <div className="text-[13px] border border-amber-500/20 bg-amber-500/5 rounded-lg px-3 py-2 text-amber-100/90">
                <strong className="text-amber-200">Run it:</strong> {card.run_hint}
              </div>
            )}
            {!!card.sources?.length && (
              <div>
                <div className="text-[11px] font-semibold text-sky-300/90 uppercase mb-1">
                  Authoritative sources
                </div>
                <ul className="space-y-1">
                  {card.sources.map((s) => (
                    <li key={s.title} className="text-xs text-white/65 flex items-start gap-1">
                      <span className="text-white/35 shrink-0">[{s.kind || "ref"}]</span>
                      {s.url ? (
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-300/90 hover:underline inline-flex items-center gap-0.5"
                        >
                          {s.title} <ExternalLink size={10} />
                        </a>
                      ) : (
                        <span>{s.title}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(card.python || card.cypher || card.shacl) && (
              <div className="space-y-2 pt-1 border-t border-white/10">
                <div className="text-[11px] uppercase tracking-wide text-white/40">
                  Same idea in other languages
                </div>
                {(
                  [
                    ["Python (rdflib)", card.python, "text-emerald-300"],
                    ["Cypher (Neo4j)", card.cypher, "text-sky-300"],
                    ["SHACL", card.shacl, "text-fuchsia-300"],
                  ] as const
                )
                  .filter(([, v]) => v)
                  .map(([lbl, v, col]) => (
                    <div key={lbl}>
                      <div className={`text-[10px] uppercase tracking-wide ${col}`}>{lbl}</div>
                      <pre className="rounded-lg bg-[#0a0a0f] border border-white/10 p-2.5 text-[11.5px] font-mono text-white/85 whitespace-pre overflow-x-auto">
                        {v}
                      </pre>
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}
      </button>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => go(-1)}
          disabled={pos === 0}
          className="inline-flex items-center gap-1 rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5 disabled:opacity-30"
        >
          <ChevronLeft size={14} /> Prev
        </button>
        <button
          type="button"
          onClick={() => {
            setKnownFor(card.id, !known[card.id]);
          }}
          className={`inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-sm ${
            known[card.id]
              ? "border-emerald-500/50 bg-emerald-600/20 text-emerald-200"
              : "border-white/15 text-white/70 hover:bg-white/5"
          }`}
        >
          <Check size={14} /> {known[card.id] ? "Known" : "Mark known"}
        </button>
        <button
          type="button"
          onClick={() => go(1)}
          disabled={pos >= pool.length - 1}
          className="inline-flex items-center gap-1 rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5 disabled:opacity-30 ml-auto"
        >
          Next <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

/* ======================= FILL IN THE BLANKS ======================= */
function FillBlanks({ cards }: Readonly<{ cards: MemoryCard[] }>) {
  const pool = useMemo(() => cards.filter((c) => c.blank && (c.answers?.length ?? 0) > 0), [cards]);
  const [i, setI] = useState(0);
  const [vals, setVals] = useState<string[]>([]);
  const [checked, setChecked] = useState(false);
  const card = pool[i];

  const segments = useMemo(() => (card ? card.blank!.split(/_{2,}/) : []), [card]);
  const answers = card?.answers ?? [];

  const reset = (d: number) => {
    setI((p) => Math.max(0, Math.min(pool.length - 1, p + d)));
    setVals([]);
    setChecked(false);
  };
  if (!card) return <div className="text-sm text-white/50">No fill-in cards.</div>;
  const correct = answers.filter((a, k) => blankMatch(vals[k] || "", a)).length;

  return (
    <div className="space-y-3">
      <div className="text-[11px] text-white/40">
        {i + 1}/{pool.length} · {card.section}
      </div>
      <div className="text-[14px] font-medium text-white">{card.front}</div>
      <div className="rounded-lg bg-[#0a0a0f] border border-white/10 p-3 font-mono text-[12.5px] text-white/80 whitespace-pre-wrap leading-7">
        {segments.map((seg, si) => (
          <React.Fragment key={`seg-${card.id}-${si}`}>
            {seg}
            {si < segments.length - 1 && (
              <input
                value={vals[si] || ""}
                onChange={(e) => {
                  const nv = [...vals];
                  nv[si] = e.target.value;
                  setVals(nv);
                }}
                placeholder="___"
                className={`inline-block min-w-[90px] rounded border px-1.5 py-0.5 mx-0.5 bg-white/5 ${
                  checked
                    ? blankMatch(vals[si] || "", answers[si] || "")
                      ? "border-emerald-500/60 text-emerald-200"
                      : "border-rose-500/60 text-rose-200"
                    : "border-white/20"
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {checked && (
        <div className="text-[13px] space-y-2">
          <div className={correct === answers.length ? "text-emerald-300" : "text-amber-300"}>
            {correct}/{answers.length} correct
          </div>
          {correct < answers.length && (
            <div className="text-white/60">
              Answer: <span className="font-mono text-emerald-200">{answers.join("  ·  ")}</span>
            </div>
          )}
          {card.code && (
            <pre className="rounded-lg bg-[#0a0a0f] border border-white/10 p-2.5 text-[11.5px] font-mono text-emerald-100/90 whitespace-pre overflow-x-auto">
              {card.code}
            </pre>
          )}
          {card.explain && <p className="text-white/70">{card.explain}</p>}
          {(card.what || card.why) && (
            <div className="text-white/65 space-y-1 border-t border-white/10 pt-2">
              {card.what && (
                <div>
                  <span className="text-emerald-300/90 font-semibold text-[11px] uppercase">What </span>
                  {card.what}
                </div>
              )}
              {card.why && (
                <div>
                  <span className="text-emerald-300/90 font-semibold text-[11px] uppercase">Why </span>
                  {card.why}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => reset(-1)}
          disabled={i === 0}
          className="rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5 disabled:opacity-30"
        >
          Prev
        </button>
        <button
          type="button"
          onClick={() => setChecked(true)}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
        >
          Check
        </button>
        <button
          type="button"
          onClick={() => reset(1)}
          disabled={i >= pool.length - 1}
          className="rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5 disabled:opacity-30 ml-auto"
        >
          Next
        </button>
      </div>
    </div>
  );
}

/* ==================== WRITE A SNIPPET / SECTION ==================== */
function WriteIt({
  prompts,
}: Readonly<{ prompts: { key: string; label: string; sub?: string; answer: string }[] }>) {
  const [i, setI] = useState(0);
  const [text, setText] = useState("");
  const [reveal, setReveal] = useState(false);
  const p = prompts[i];

  const go = (d: number) => {
    setI((q) => Math.max(0, Math.min(prompts.length - 1, q + d)));
    setText("");
    setReveal(false);
  };
  if (!p) return <div className="text-sm text-white/50">Nothing to write.</div>;
  const score = reveal ? codeScore(text, p.answer) : 0;

  return (
    <div className="space-y-3">
      <div className="text-[11px] text-white/40">
        {i + 1}/{prompts.length} · {p.sub}
      </div>
      <div className="text-[14px] font-medium text-white">{p.label}</div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={Math.min(14, Math.max(4, p.answer.split("\n").length + 2))}
        placeholder="Write it from memory…"
        className="w-full rounded-lg border border-white/15 bg-[#0a0a0f] px-3 py-2 font-mono text-[12.5px] text-white/85"
        spellCheck={false}
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => go(-1)}
          disabled={i === 0}
          className="rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5 disabled:opacity-30"
        >
          Prev
        </button>
        <button
          type="button"
          onClick={() => setReveal(true)}
          className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
        >
          <Eye size={14} /> Reveal & score
        </button>
        <button
          type="button"
          onClick={() => {
            setText("");
            setReveal(false);
          }}
          className="inline-flex items-center gap-1 rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5"
        >
          <RotateCcw size={14} /> Clear
        </button>
        <button
          type="button"
          onClick={() => go(1)}
          disabled={i >= prompts.length - 1}
          className="rounded-lg border border-white/15 px-3 py-2 text-sm text-white/70 hover:bg-white/5 disabled:opacity-30 ml-auto"
        >
          Next
        </button>
      </div>

      {reveal && (
        <div className="space-y-2">
          <div
            className={`inline-flex items-center gap-1 text-sm font-medium ${
              score >= 0.85 ? "text-emerald-300" : score >= 0.5 ? "text-amber-300" : "text-rose-300"
            }`}
          >
            {score >= 0.85 ? <Check size={14} /> : <X size={14} />} {Math.round(score * 100)}% match
          </div>
          <pre className="rounded-lg bg-[#0a0a0f] border border-emerald-500/25 p-3 text-[12px] font-mono text-emerald-100/90 whitespace-pre overflow-x-auto">
            {p.answer}
          </pre>
        </div>
      )}
    </div>
  );
}

/* ============================ TEST TABS ============================ */
export function TestDrill({ cards }: Readonly<{ cards: MemoryCard[] }>) {
  const [mode, setMode] = useState<"blanks" | "snippet" | "section">("blanks");

  const snippetPrompts = useMemo(
    () =>
      cards
        .filter((c) => c.code && (c.kind === "line" || c.kind === "block" || c.kind === "pattern"))
        .map((c) => ({ key: c.id, label: c.front, sub: c.section, answer: c.code! })),
    [cards],
  );

  const sectionPrompts = useMemo(() => {
    const bySection = new Map<string, string[]>();
    for (const c of cards) {
      if (!c.code) continue;
      const arr = bySection.get(c.section) || [];
      arr.push(c.code);
      bySection.set(c.section, arr);
    }
    return Array.from(bySection.entries()).map(([sec, codes]) => ({
      key: sec,
      label: `Write the whole "${sec}" from memory.`,
      sub: sec,
      answer: codes.join("\n\n"),
    }));
  }, [cards]);

  return (
    <div className="space-y-4">
      <div className="flex rounded-lg border border-white/15 overflow-hidden text-xs w-fit">
        {(
          [
            ["blanks", "Fill blanks"],
            ["snippet", "Write a snippet"],
            ["section", "Write a section"],
          ] as const
        ).map(([m, label]) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`px-3 py-1.5 ${mode === m ? "bg-emerald-600 text-white" : "bg-white/5 text-white/60"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {mode === "blanks" && <FillBlanks cards={cards} />}
      {mode === "snippet" && <WriteIt prompts={snippetPrompts} />}
      {mode === "section" && <WriteIt prompts={sectionPrompts} />}
    </div>
  );
}
