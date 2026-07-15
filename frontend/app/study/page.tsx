"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronLeft,
  Code2,
  Eye,
  EyeOff,
  FileUp,
  Flame,
  GraduationCap,
  Layers,
  PenLine,
  RefreshCw,
  Sparkles,
  Target,
  Upload,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "../../lib/api";
import type {
  CodeBeat,
  StudyMode,
  StudyModule,
  StudyModuleSummary,
} from "../../lib/study/types";

const MODES: { id: StudyMode; label: string; icon: React.ReactNode; tip: string }[] = [
  { id: "story", label: "Story", icon: <BookOpen size={14} />, tip: "Memory anchor — retell out loud" },
  { id: "annotated", label: "Annotated", icon: <Code2 size={14} />, tip: "Read code with line notes" },
  { id: "line-quiz", label: "Line quiz", icon: <Target size={14} />, tip: "Test each critical line" },
  { id: "fill", label: "Fill blanks", icon: <PenLine size={14} />, tip: "Recall tokens from memory" },
  { id: "blank", label: "Blank write", icon: <EyeOff size={14} />, tip: "Type the beat from scratch" },
  { id: "flash", label: "Flashcards", icon: <Brain size={14} />, tip: "Concept cards" },
  { id: "self-quiz", label: "Self-quiz", icon: <GraduationCap size={14} />, tip: "Q&A without looking" },
  { id: "boss", label: "Final boss", icon: <Flame size={14} />, tip: "Integrated oral / write checks" },
];

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function normalize(s: string) {
  return s.replace(/\s+/g, " ").trim().toLowerCase();
}

function CodeBlock({
  code,
  language,
  highlightLine,
  annotations,
}: {
  code: string;
  language: string;
  highlightLine?: number;
  annotations?: { line: number; note: string }[];
}) {
  const lines = code.split("\n");
  const noteMap = new Map((annotations || []).map((a) => [a.line, a.note]));
  return (
    <div className="rounded-xl border border-white/10 bg-[#0a0a0f] overflow-hidden font-mono text-[12px] leading-5">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 text-[11px] text-white/50">
        <span>{language}</span>
        <span>{lines.length} lines</span>
      </div>
      <div className="overflow-x-auto max-h-[420px] overflow-y-auto p-2">
        {lines.map((ln, i) => {
          const n = i + 1;
          const active = highlightLine === n;
          const note = noteMap.get(n);
          return (
            <div key={n} className="group">
              <div
                className={`flex gap-3 px-2 py-0.5 rounded ${
                  active ? "bg-emerald-500/20 ring-1 ring-emerald-400/40" : "hover:bg-white/5"
                }`}
              >
                <span className="w-8 shrink-0 text-right text-white/30 select-none">{n}</span>
                <pre className="flex-1 whitespace-pre text-emerald-100/90">{ln || " "}</pre>
              </div>
              {note && (
                <div className="ml-12 mb-1 text-[11px] text-amber-200/80 border-l-2 border-amber-500/40 pl-2">
                  {note}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function StudyLabPage() {
  const [modules, setModules] = useState<StudyModuleSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mod, setMod] = useState<StudyModule | null>(null);
  const [mode, setMode] = useState<StudyMode>("story");
  const [beatIdx, setBeatIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [paste, setPaste] = useState("");
  const [uploadTitle, setUploadTitle] = useState("");
  const [tagFilter, setTagFilter] = useState("");

  // practice state
  const [lineIdx, setLineIdx] = useState(0);
  const [fillAnswers, setFillAnswers] = useState<Record<string, string>>({});
  const [fillResult, setFillResult] = useState<any>(null);
  const [blankText, setBlankText] = useState("");
  const [blankRevealed, setBlankRevealed] = useState(false);
  const [flashIdx, setFlashIdx] = useState(0);
  const [flashFlip, setFlashFlip] = useState(false);
  const [quizIdx, setQuizIdx] = useState(0);
  const [quizShow, setQuizShow] = useState(false);
  const [lineFeedback, setLineFeedback] = useState<string | null>(null);
  const [localProgress, setLocalProgress] = useState<Record<string, any>>({});

  const beat: CodeBeat | null = mod?.beats?.[beatIdx] ?? null;

  const loadList = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.studyModules();
      setModules(res.modules || []);
      if (!activeId && res.modules?.length) {
        setActiveId(res.modules[0].id);
      }
    } catch (e: any) {
      toast.error(e?.message || "Failed to load study modules — is API on :8080?");
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  useEffect(() => {
    loadList();
    try {
      const raw = localStorage.getItem("study-lab-progress");
      if (raw) setLocalProgress(JSON.parse(raw));
    } catch {
      /* ignore */
    }
  }, [loadList]);

  useEffect(() => {
    if (!activeId) return;
    (async () => {
      try {
        const m = await api.studyModule(activeId);
        setMod(m);
        setBeatIdx(0);
        setMode("story");
        setLineIdx(0);
        setFillAnswers({});
        setFillResult(null);
        setBlankText("");
        setBlankRevealed(false);
      } catch (e: any) {
        toast.error(e?.message || "Failed to load module");
      }
    })();
  }, [activeId]);

  const markProgress = (patch: Record<string, any>) => {
    if (!mod) return;
    const next = {
      ...localProgress,
      [mod.id]: { ...(localProgress[mod.id] || {}), ...patch, updated_at: new Date().toISOString() },
    };
    setLocalProgress(next);
    localStorage.setItem("study-lab-progress", JSON.stringify(next));
    api
      .studyProgressSave({
        module_id: mod.id,
        mode,
        score: patch.score,
        completed_beat_ids: patch.completed_beat_ids || [],
      })
      .catch(() => undefined);
  };

  const filtered = useMemo(() => {
    const t = tagFilter.trim().toLowerCase();
    if (!t) return modules;
    return modules.filter(
      (m) =>
        m.title.toLowerCase().includes(t) ||
        m.tags?.some((x) => x.toLowerCase().includes(t)) ||
        m.description?.toLowerCase().includes(t),
    );
  }, [modules, tagFilter]);

  const lineQuiz = beat?.line_quiz || [];
  const currentLineQ = lineQuiz[lineIdx];
  const lineChoices = useMemo(
    () => (currentLineQ ? shuffle(currentLineQ.choices || [currentLineQ.answer]) : []),
    // re-shuffle when question changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentLineQ?.line, currentLineQ?.prompt, beat?.id],
  );

  const onGradeFill = async () => {
    if (!mod || !beat?.fill_blanks) return;
    try {
      const res = await api.studyGradeFill({
        module_id: mod.id,
        beat_id: beat.id,
        answers: fillAnswers,
      });
      setFillResult(res);
      markProgress({ score: res.score, last_mode: "fill" });
      toast.success(`Score ${(res.score * 100).toFixed(0)}%`);
    } catch (e: any) {
      toast.error(e?.message || "Grade failed");
    }
  };

  const onLineChoice = async (choice: string) => {
    if (!mod || !beat || !currentLineQ) return;
    try {
      const res = await api.studyGradeLine({
        module_id: mod.id,
        beat_id: beat.id,
        line: currentLineQ.line,
        choice,
      });
      setLineFeedback(res.ok ? `✓ Correct — ${res.why || ""}` : `✗ Expected: ${res.expected}`);
      if (res.ok) {
        markProgress({
          last_mode: "line-quiz",
          line_ok: (localProgress[mod.id]?.line_ok || 0) + 1,
        });
      }
    } catch (e: any) {
      // offline fallback
      const ok = normalize(choice) === normalize(currentLineQ.answer);
      setLineFeedback(ok ? "✓ Correct" : `✗ Expected: ${currentLineQ.answer}`);
    }
  };

  const blankScore = useMemo(() => {
    if (!beat?.code || !blankText) return null;
    const a = normalize(blankText);
    const b = normalize(beat.code);
    if (!a || !b) return 0;
    // crude token overlap
    const at = new Set(a.split(/[^a-z0-9_]+/).filter(Boolean));
    const bt = b.split(/[^a-z0-9_]+/).filter(Boolean);
    if (!bt.length) return 0;
    let hit = 0;
    for (const t of bt) if (at.has(t)) hit++;
    return hit / bt.length;
  }, [blankText, beat?.code]);

  const onUploadFile = async (file: File) => {
    try {
      const res = await api.studyUpload(file, uploadTitle, "");
      toast.success(`Module created: ${res.module?.title || res.module?.id}`);
      setShowUpload(false);
      await loadList();
      if (res.module?.id) setActiveId(res.module.id);
    } catch (e: any) {
      toast.error(e?.message || "Upload failed");
    }
  };

  const onGeneratePaste = async () => {
    try {
      const res = await api.studyGenerate({
        title: uploadTitle,
        text: paste,
        filename: "paste.md",
      });
      toast.success(`Module created: ${res.module?.title}`);
      setShowUpload(false);
      setPaste("");
      await loadList();
      if (res.module?.id) setActiveId(res.module.id);
    } catch (e: any) {
      toast.error(e?.message || "Generate failed");
    }
  };

  const progressPct = mod
    ? Math.min(
        100,
        Math.round(
          ((localProgress[mod.id]?.line_ok || 0) +
            (localProgress[mod.id]?.score ? 3 : 0) +
            (localProgress[mod.id]?.last_mode ? 1 : 0)) *
            8,
        ),
      )
    : 0;

  return (
    <div className="min-h-screen bg-[var(--surface-0)] text-[var(--text-0)]">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="max-w-[1400px] mx-auto px-4 py-3 flex items-center gap-3 flex-wrap">
          <Link
            href="/"
            className="inline-flex items-center gap-1 text-sm text-white/60 hover:text-white"
          >
            <ChevronLeft size={16} /> Diagnostics
          </Link>
          <div className="flex items-center gap-2">
            <GraduationCap className="text-emerald-400" size={20} />
            <div>
              <div className="font-semibold tracking-tight">Study Lab</div>
              <div className="text-[11px] text-white/45">
                Memorize · Write · Quiz — modular interview trainer
              </div>
            </div>
          </div>
          <div className="flex-1" />
          <button
            type="button"
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-sm font-medium"
          >
            <Upload size={14} /> New module
          </button>
          <button
            type="button"
            onClick={() =>
              api.studyReseed().then(() => {
                toast.success("Reseeded curriculum");
                loadList();
              })
            }
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 px-3 py-1.5 text-sm text-white/70 hover:bg-white/5"
          >
            <RefreshCw size={14} /> Reseed
          </button>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-4 py-5 grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-5">
        {/* Sidebar */}
        <aside className="space-y-3">
          <input
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
            placeholder="Filter modules / tags…"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-emerald-500/50"
          />
          <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
            {loading && <div className="text-sm text-white/40">Loading modules…</div>}
            {!loading &&
              filtered.map((m) => {
                const active = m.id === activeId;
                const done = !!localProgress[m.id]?.last_mode;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setActiveId(m.id)}
                    className={`w-full text-left rounded-xl border px-3 py-2.5 transition ${
                      active
                        ? "border-emerald-500/50 bg-emerald-500/10"
                        : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <Layers size={14} className="mt-0.5 text-emerald-400 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-sm font-medium leading-snug flex items-center gap-1">
                          {m.title}
                          {done && <CheckCircle2 size={12} className="text-emerald-400" />}
                        </div>
                        <div className="text-[11px] text-white/45 mt-0.5 line-clamp-2">
                          {m.description}
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10">
                            {m.beat_count} beats
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10">
                            ~{m.estimated_minutes}m
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10">
                            {m.source}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
          </div>
        </aside>

        {/* Main */}
        <main className="min-w-0 space-y-4">
          {!mod ? (
            <div className="rounded-2xl border border-white/10 p-10 text-center text-white/50">
              Select a module or upload notes to generate one.
            </div>
          ) : (
            <>
              <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-transparent p-5">
                <div className="flex flex-wrap items-start gap-3 justify-between">
                  <div>
                    <h1 className="text-xl font-semibold tracking-tight">{mod.title}</h1>
                    <p className="text-sm text-white/60 mt-1 max-w-3xl">{mod.description}</p>
                    <p className="text-sm text-emerald-300/90 mt-2 font-medium">{mod.one_liner}</p>
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {mod.tags?.map((t) => (
                        <span
                          key={t}
                          className="text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-black/30"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] text-white/45">Local progress</div>
                    <div className="text-2xl font-semibold text-emerald-400">{progressPct}%</div>
                    <div className="w-28 h-1.5 rounded bg-white/10 mt-1 overflow-hidden ml-auto">
                      <div
                        className="h-full bg-emerald-500"
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Modes */}
              <div className="flex flex-wrap gap-1.5">
                {MODES.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    title={m.tip}
                    onClick={() => setMode(m.id)}
                    className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium border ${
                      mode === m.id
                        ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-200"
                        : "border-white/10 text-white/60 hover:bg-white/5"
                    }`}
                  >
                    {m.icon}
                    {m.label}
                  </button>
                ))}
              </div>

              {/* Beat selector for code modes */}
              {["annotated", "line-quiz", "fill", "blank"].includes(mode) && (
                <div className="flex flex-wrap gap-2 items-center">
                  <span className="text-xs text-white/45">Beat</span>
                  {mod.beats.map((b, i) => (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => {
                        setBeatIdx(i);
                        setLineIdx(0);
                        setFillAnswers({});
                        setFillResult(null);
                        setBlankText("");
                        setBlankRevealed(false);
                        setLineFeedback(null);
                      }}
                      className={`text-xs rounded-md px-2 py-1 border ${
                        i === beatIdx
                          ? "border-emerald-500/40 bg-emerald-500/10"
                          : "border-white/10 hover:bg-white/5"
                      }`}
                    >
                      {i + 1}. {b.title}
                    </button>
                  ))}
                </div>
              )}

              {/* Mode panels */}
              {mode === "story" && (
                <section className="rounded-2xl border border-white/10 p-5 space-y-4">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    <Sparkles size={16} className="text-amber-300" /> Memory anchor
                  </h2>
                  <p className="text-[15px] leading-relaxed text-white/85 whitespace-pre-wrap">
                    {mod.story}
                  </p>
                  {!!mod.change_table?.length && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="text-left text-white/50 border-b border-white/10">
                            {Object.keys(mod.change_table[0]).map((k) => (
                              <th key={k} className="py-2 pr-3 font-medium capitalize">
                                {k}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {mod.change_table.map((row, i) => (
                            <tr key={i} className="border-b border-white/5">
                              {Object.values(row).map((v, j) => (
                                <td key={j} className="py-2 pr-3 text-white/80">
                                  {v}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      markProgress({ last_mode: "story" });
                      toast.success("Story marked reviewed");
                    }}
                    className="text-sm rounded-lg bg-white/10 hover:bg-white/15 px-3 py-1.5"
                  >
                    I can retell this without looking
                  </button>
                </section>
              )}

              {mode === "annotated" && beat && (
                <section className="space-y-3">
                  <p className="text-sm text-white/65">{beat.narrative}</p>
                  <CodeBlock
                    code={beat.code}
                    language={beat.language}
                    annotations={beat.annotations}
                  />
                </section>
              )}

              {mode === "line-quiz" && beat && (
                <section className="space-y-4 rounded-2xl border border-white/10 p-5">
                  {!lineQuiz.length ? (
                    <p className="text-sm text-white/50">No line quizzes on this beat.</p>
                  ) : (
                    <>
                      <div className="text-xs text-white/45">
                        Question {lineIdx + 1} / {lineQuiz.length} · line {currentLineQ?.line}
                      </div>
                      <CodeBlock
                        code={beat.code}
                        language={beat.language}
                        highlightLine={currentLineQ?.line}
                        annotations={beat.annotations?.filter((a) => a.line === currentLineQ?.line)}
                      />
                      <p className="text-sm font-medium">{currentLineQ?.prompt}</p>
                      <div className="grid gap-2">
                        {lineChoices.map((c) => (
                          <button
                            key={c}
                            type="button"
                            onClick={() => onLineChoice(c)}
                            className="text-left text-sm rounded-lg border border-white/10 bg-white/[0.03] hover:border-emerald-500/40 px-3 py-2"
                          >
                            {c}
                          </button>
                        ))}
                      </div>
                      {lineFeedback && (
                        <div className="text-sm text-white/80 border border-white/10 rounded-lg px-3 py-2 bg-black/30">
                          {lineFeedback}
                        </div>
                      )}
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={lineIdx <= 0}
                          onClick={() => {
                            setLineIdx((x) => Math.max(0, x - 1));
                            setLineFeedback(null);
                          }}
                          className="text-xs px-3 py-1.5 rounded border border-white/15 disabled:opacity-30"
                        >
                          Prev
                        </button>
                        <button
                          type="button"
                          disabled={lineIdx >= lineQuiz.length - 1}
                          onClick={() => {
                            setLineIdx((x) => Math.min(lineQuiz.length - 1, x + 1));
                            setLineFeedback(null);
                          }}
                          className="text-xs px-3 py-1.5 rounded border border-white/15 disabled:opacity-30"
                        >
                          Next
                        </button>
                      </div>
                    </>
                  )}
                </section>
              )}

              {mode === "fill" && beat && (
                <section className="space-y-4 rounded-2xl border border-white/10 p-5">
                  {!beat.fill_blanks ? (
                    <p className="text-sm text-white/50">No fill-in template on this beat.</p>
                  ) : (
                    <>
                      <p className="text-sm text-white/65">
                        Fill each <code className="text-emerald-300">{"{{blank}}"}</code> from
                        memory.
                      </p>
                      <pre className="text-xs md:text-sm font-mono whitespace-pre-wrap rounded-xl bg-black/40 border border-white/10 p-3 text-emerald-100/90">
                        {beat.fill_blanks.template}
                      </pre>
                      <div className="grid sm:grid-cols-2 gap-3">
                        {beat.fill_blanks.blanks.map((b) => (
                          <label key={b.id} className="text-sm space-y-1">
                            <span className="text-white/50 text-xs">
                              {b.id} {b.hint ? `· ${b.hint}` : ""}
                            </span>
                            <input
                              value={fillAnswers[b.id] || ""}
                              onChange={(e) =>
                                setFillAnswers((prev) => ({ ...prev, [b.id]: e.target.value }))
                              }
                              className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 font-mono text-sm"
                              placeholder={b.id}
                            />
                          </label>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={onGradeFill}
                        className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
                      >
                        Check answers
                      </button>
                      {fillResult && (
                        <div className="text-sm space-y-1">
                          <div>
                            Score:{" "}
                            <strong className="text-emerald-300">
                              {(fillResult.score * 100).toFixed(0)}%
                            </strong>
                          </div>
                          {fillResult.results?.map((r: any) => (
                            <div key={r.id} className={r.ok ? "text-emerald-300/90" : "text-rose-300/90"}>
                              {r.id}: {r.ok ? "ok" : `got “${r.given}” · expected “${r.expected}”`}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </section>
              )}

              {mode === "blank" && beat && (
                <section className="space-y-3 rounded-2xl border border-white/10 p-5">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-white/65">
                      Hide the reference. Type the full beat from memory, then compare.
                    </p>
                    <button
                      type="button"
                      onClick={() => setBlankRevealed((v) => !v)}
                      className="inline-flex items-center gap-1 text-xs border border-white/15 rounded-lg px-2 py-1"
                    >
                      {blankRevealed ? <EyeOff size={12} /> : <Eye size={12} />}
                      {blankRevealed ? "Hide solution" : "Reveal solution"}
                    </button>
                  </div>
                  <textarea
                    value={blankText}
                    onChange={(e) => setBlankText(e.target.value)}
                    rows={14}
                    spellCheck={false}
                    placeholder={`Write ${beat.language} from memory…`}
                    className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2 font-mono text-sm outline-none focus:border-emerald-500/40"
                  />
                  {blankScore != null && (
                    <div className="text-sm text-white/70">
                      Rough token overlap:{" "}
                      <strong className="text-emerald-300">{(blankScore * 100).toFixed(0)}%</strong>
                      <button
                        type="button"
                        className="ml-3 text-xs underline text-white/50"
                        onClick={() => markProgress({ score: blankScore, last_mode: "blank" })}
                      >
                        Save attempt
                      </button>
                    </div>
                  )}
                  {blankRevealed && (
                    <CodeBlock code={beat.code} language={beat.language} annotations={beat.annotations} />
                  )}
                </section>
              )}

              {mode === "flash" && (
                <section className="rounded-2xl border border-white/10 p-6 min-h-[240px] flex flex-col items-center justify-center gap-4">
                  {!mod.concepts?.length ? (
                    <p className="text-white/50 text-sm">No concept cards.</p>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => setFlashFlip((f) => !f)}
                        className="w-full max-w-lg min-h-[160px] rounded-2xl border border-emerald-500/30 bg-emerald-500/5 px-6 py-8 text-center"
                      >
                        {!flashFlip ? (
                          <div className="text-xl font-semibold">{mod.concepts[flashIdx].term}</div>
                        ) : (
                          <div className="space-y-2">
                            <div className="text-sm text-white/80">
                              {mod.concepts[flashIdx].definition}
                            </div>
                            {mod.concepts[flashIdx].analogy && (
                              <div className="text-xs text-white/45">
                                Analogy: {mod.concepts[flashIdx].analogy}
                              </div>
                            )}
                          </div>
                        )}
                      </button>
                      <div className="text-xs text-white/45">
                        Card {flashIdx + 1}/{mod.concepts.length} · click card to flip
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="text-xs border border-white/15 rounded-lg px-3 py-1.5"
                          onClick={() => {
                            setFlashIdx((i) => Math.max(0, i - 1));
                            setFlashFlip(false);
                          }}
                        >
                          Prev
                        </button>
                        <button
                          type="button"
                          className="text-xs border border-white/15 rounded-lg px-3 py-1.5"
                          onClick={() => {
                            setFlashIdx((i) => Math.min(mod.concepts.length - 1, i + 1));
                            setFlashFlip(false);
                          }}
                        >
                          Next
                        </button>
                      </div>
                    </>
                  )}
                </section>
              )}

              {mode === "self-quiz" && (
                <section className="rounded-2xl border border-white/10 p-5 space-y-4">
                  {!mod.self_quiz?.length ? (
                    <p className="text-sm text-white/50">No self-quiz items.</p>
                  ) : (
                    <>
                      <div className="text-xs text-white/45">
                        {quizIdx + 1} / {mod.self_quiz.length}
                      </div>
                      <p className="text-base font-medium">{mod.self_quiz[quizIdx].q}</p>
                      {quizShow ? (
                        <div className="text-sm text-emerald-200/90 border border-emerald-500/20 bg-emerald-500/5 rounded-lg px-3 py-2">
                          {mod.self_quiz[quizIdx].a}
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setQuizShow(true)}
                          className="text-sm rounded-lg border border-white/15 px-3 py-1.5"
                        >
                          Reveal answer
                        </button>
                      )}
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="text-xs border border-white/15 rounded-lg px-3 py-1.5"
                          onClick={() => {
                            setQuizIdx((i) => Math.max(0, i - 1));
                            setQuizShow(false);
                          }}
                        >
                          Prev
                        </button>
                        <button
                          type="button"
                          className="text-xs border border-white/15 rounded-lg px-3 py-1.5"
                          onClick={() => {
                            setQuizIdx((i) => Math.min(mod.self_quiz.length - 1, i + 1));
                            setQuizShow(false);
                          }}
                        >
                          Next
                        </button>
                      </div>
                    </>
                  )}
                  {!!mod.common_mistakes?.length && (
                    <div className="pt-2 border-t border-white/10">
                      <h3 className="text-xs font-semibold text-rose-300/90 mb-2">Common mistakes</h3>
                      <ul className="list-disc pl-5 text-sm text-white/70 space-y-1">
                        {mod.common_mistakes.map((m) => (
                          <li key={m}>{m}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </section>
              )}

              {mode === "boss" && (
                <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5 space-y-3">
                  <h2 className="font-semibold flex items-center gap-2 text-amber-100">
                    <Flame size={16} /> Final boss
                  </h2>
                  <ol className="list-decimal pl-5 space-y-2 text-sm text-white/85">
                    {(mod.final_boss || []).map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ol>
                  <button
                    type="button"
                    onClick={() => {
                      markProgress({ last_mode: "boss", score: 1 });
                      toast.success("Boss marked complete — revisit weak modules tomorrow");
                    }}
                    className="rounded-lg bg-amber-600/90 hover:bg-amber-500 px-4 py-2 text-sm font-medium"
                  >
                    I completed these aloud / on paper
                  </button>
                </section>
              )}
            </>
          )}
        </main>
      </div>

      {/* Upload modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-2xl border border-white/15 bg-[#0e0e12] p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold flex items-center gap-2">
                <FileUp size={16} className="text-emerald-400" /> Generate study module
              </h2>
              <button type="button" className="text-white/50 text-sm" onClick={() => setShowUpload(false)}>
                Close
              </button>
            </div>
            <p className="text-xs text-white/50">
              Upload Markdown, text, Turtle, Cypher, or a Jupyter <code>.ipynb</code>. The system
              extracts story, code beats, line quizzes, fill-blanks, and concepts — a new module
              appears in the sidebar.
            </p>
            <input
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="Optional title override"
              className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm"
            />
            <label className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/20 bg-white/[0.03] px-4 py-8 cursor-pointer hover:border-emerald-500/40">
              <Upload size={20} className="text-emerald-400" />
              <span className="text-sm text-white/70">Click to choose a file</span>
              <input
                type="file"
                className="hidden"
                accept=".md,.txt,.ttl,.cypher,.cql,.ipynb,.py,.sparql,.rq"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) onUploadFile(f);
                }}
              />
            </label>
            <div className="text-center text-[11px] text-white/35">or paste notes</div>
            <textarea
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
              rows={8}
              placeholder="# My topic&#10;&#10;Story…&#10;&#10;```python&#10;print('code')&#10;```"
              className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2 font-mono text-xs"
            />
            <button
              type="button"
              disabled={!paste.trim()}
              onClick={onGeneratePaste}
              className="w-full rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 py-2 text-sm font-medium"
            >
              Generate from paste
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
