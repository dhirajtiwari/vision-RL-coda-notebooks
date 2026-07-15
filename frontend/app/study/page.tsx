"use client";

/**
 * Study Lab:
 *  - Lessons: Learn → Say → Code → Quiz → Rewrite → Boss
 *  - Flashcards: full deck with What/How/Where/When/Who/Why + sources
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  ExternalLink,
  GraduationCap,
  Layers,
  Mic,
  RefreshCw,
  ScrollText,
  Shuffle,
  Target,
  Upload,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "../../lib/api";
import MasterclassReader from "./masterclass-view";
import type {
  CodeBeat,
  Masterclass,
  MasterclassSummary,
  StudyModule,
  StudyModuleSummary,
  StudyStep,
} from "../../lib/study/types";
import { STUDY_STEPS } from "../../lib/study/types";

type Hub = "today" | "masters" | "lessons" | "flashcards";

interface FlashCard {
  id: string;
  front: string;
  track: string;
  tags: string[];
  kind: string;
  what: string;
  how: string;
  where: string;
  when: string;
  who: string;
  why: string;
  analogy?: string;
  code?: string;
  language?: string;
  pitfalls?: string[];
  say_aloud?: string;
  sources?: { title: string; url?: string; kind?: string }[];
  related_module_ids?: string[];
  difficulty?: string;
}

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
    <div className="rounded-xl border border-white/10 bg-[#0a0a0f] overflow-hidden font-mono text-[12.5px] leading-5">
      <div className="flex justify-between px-3 py-1.5 border-b border-white/10 text-[11px] text-white/45">
        <span>{language}</span>
        <span>{lines.length} lines</span>
      </div>
      <div className="overflow-x-auto max-h-[380px] overflow-y-auto p-2">
        {lines.map((ln, i) => {
          const n = i + 1;
          const active = highlightLine === n;
          const note = noteMap.get(n);
          return (
            <div key={n}>
              <div
                className={`flex gap-3 px-2 py-0.5 rounded ${
                  active ? "bg-emerald-500/20 ring-1 ring-emerald-400/40" : ""
                }`}
              >
                <span className="w-7 shrink-0 text-right text-white/30 select-none">{n}</span>
                <pre className="flex-1 whitespace-pre text-emerald-100/90">{ln || " "}</pre>
              </div>
              {note && (
                <div className="ml-11 mb-1 text-[11px] text-amber-200/85 border-l-2 border-amber-500/50 pl-2">
                  → {note}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const TRACK_LABEL: Record<string, string> = {
  foundations: "Foundations",
  graph: "Graph",
  pipeline: "ETL / pipeline",
  runtime: "Runtime scale",
  agent: "Agent",
  llmops: "LLMOps",
  observability: "Observability",
  evals: "EvalOps",
  cicd: "CI/CD",
  infra: "Infra / K8s / IaC",
  finops: "FinOps & cost",
  security: "Security",
  integrations: "Integrations",
  mlops: "MLOps / synthetic / images",
  aiops: "AIOps",
};

const W_FIELDS: { key: keyof FlashCard; label: string }[] = [
  { key: "what", label: "What" },
  { key: "how", label: "How" },
  { key: "where", label: "Where" },
  { key: "when", label: "When" },
  { key: "who", label: "Who" },
  { key: "why", label: "Why" },
];

export default function StudyLabPage() {
  const [hub, setHub] = useState<Hub>("flashcards");
  const [modules, setModules] = useState<StudyModuleSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mod, setMod] = useState<StudyModule | null>(null);
  const [step, setStep] = useState<StudyStep>("learn");
  const [beatIdx, setBeatIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [paste, setPaste] = useState("");
  const [uploadTitle, setUploadTitle] = useState("");

  const [said, setSaid] = useState<Record<number, boolean>>({});
  const [lineIdx, setLineIdx] = useState(0);
  const [lineFeedback, setLineFeedback] = useState<string | null>(null);
  const [quizIdx, setQuizIdx] = useState(0);
  const [quizShow, setQuizShow] = useState(false);
  const [fillAnswers, setFillAnswers] = useState<Record<string, string>>({});
  const [fillResult, setFillResult] = useState<any>(null);
  const [blankText, setBlankText] = useState("");
  const [blankReveal, setBlankReveal] = useState(false);
  const [progress, setProgress] = useState<Record<string, any>>({});

  // flashcards
  const [cards, setCards] = useState<FlashCard[]>([]);
  const [cardFilters, setCardFilters] = useState<{ tracks: string[]; tags: string[]; kinds: string[] }>({
    tracks: [],
    tags: [],
    kinds: [],
  });
  const [fTrack, setFTrack] = useState("");
  const [fTag, setFTag] = useState("");
  const [fKind, setFKind] = useState("");
  const [fQ, setFQ] = useState("");
  const [cardIdx, setCardIdx] = useState(0);
  const [cardFlipped, setCardFlipped] = useState(false);
  const [known, setKnown] = useState<Record<string, boolean>>({});

  // spaced repetition (Today)
  const [dash, setDash] = useState<any>(null);
  const [dueCards, setDueCards] = useState<FlashCard[]>([]);
  const [reviewIdx, setReviewIdx] = useState(0);
  const [reviewFlipped, setReviewFlipped] = useState(false);

  // Masterclasses (verbatim guides to memorize)
  const [mastersList, setMastersList] = useState<MasterclassSummary[]>([]);
  const [activeMaster, setActiveMaster] = useState<Masterclass | null>(null);

  // P3: focus mode (hide chrome) + one-time onboarding hint
  const [focusMode, setFocusMode] = useState(false);
  const [showIntro, setShowIntro] = useState(false);
  useEffect(() => {
    try {
      if (!localStorage.getItem("study-intro-seen")) setShowIntro(true);
    } catch {
      /* ignore */
    }
  }, []);
  const dismissIntro = useCallback(() => {
    setShowIntro(false);
    try {
      localStorage.setItem("study-intro-seen", "1");
    } catch {
      /* ignore */
    }
  }, []);

  const beat: CodeBeat | null = mod?.beats?.[beatIdx] ?? null;

  const loadList = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.studyModules();
      const list = res.modules || [];
      setModules(list);
      if (!activeId && list[0]) setActiveId(list[0].id);
    } catch (e: any) {
      toast.error(e?.message || "API not reachable on :8080");
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  const loadCards = useCallback(async () => {
    try {
      const res = await api.studyFlashcards({
        track: fTrack || undefined,
        tag: fTag || undefined,
        kind: fKind || undefined,
        q: fQ || undefined,
      });
      setCards(res.cards || []);
      setCardFilters(res.filters || { tracks: [], tags: [], kinds: [] });
      setCardIdx(0);
      setCardFlipped(false);
    } catch (e: any) {
      toast.error(e?.message || "Failed to load flashcards");
    }
  }, [fTrack, fTag, fKind, fQ]);

  const loadToday = useCallback(async () => {
    try {
      const [d, due] = await Promise.all([api.studyDashboard(), api.studyReviewDue("local", 40)]);
      setDash(d);
      setDueCards(due.cards || []);
      setReviewIdx(0);
      setReviewFlipped(false);
    } catch (e: any) {
      toast.error(e?.message || "Failed to load today");
    }
  }, []);

  const gradeReview = useCallback(
    async (quality: "again" | "hard" | "good" | "easy") => {
      const card = dueCards[reviewIdx];
      if (!card) return;
      try {
        await api.studyReviewGrade({ item_key: card.id, quality });
      } catch {
        /* keep the session flowing even if the write blips */
      }
      if (reviewIdx + 1 >= dueCards.length) {
        toast.success("Session complete — streak safe for today 🔥");
        loadToday();
      } else {
        setReviewIdx((i) => i + 1);
        setReviewFlipped(false);
      }
    },
    [dueCards, reviewIdx, loadToday],
  );

  useEffect(() => {
    loadList();
    try {
      const raw = localStorage.getItem("study-lab-v2");
      if (raw) setProgress(JSON.parse(raw));
      const k = localStorage.getItem("study-flash-known");
      if (k) setKnown(JSON.parse(k));
    } catch {
      /* ignore */
    }
  }, [loadList]);

  const loadMasters = useCallback(async () => {
    try {
      const r = await api.studyMasterclasses();
      setMastersList(r.masterclasses || []);
    } catch (e: any) {
      toast.error(e?.message || "Failed to load guides");
    }
  }, []);

  const openMaster = useCallback(async (id: string) => {
    try {
      const mc = await api.studyMasterclass(id);
      setActiveMaster(mc);
      window.scrollTo({ top: 0 });
    } catch (e: any) {
      toast.error(e?.message || "Failed to open guide");
    }
  }, []);

  useEffect(() => {
    if (hub === "flashcards") loadCards();
    if (hub === "today") loadToday();
    if (hub === "masters") loadMasters();
  }, [hub, loadCards, loadToday, loadMasters]);

  // Keyboard shortcuts for the Today review (1=Again 2=Hard 3=Good 4=Easy, Space=flip).
  useEffect(() => {
    if (hub !== "today" || !dueCards[reviewIdx]) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === " ") {
        e.preventDefault();
        setReviewFlipped((f) => !f);
      } else if (reviewFlipped) {
        if (e.key === "1") gradeReview("again");
        else if (e.key === "2") gradeReview("hard");
        else if (e.key === "3") gradeReview("good");
        else if (e.key === "4") gradeReview("easy");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [hub, dueCards, reviewIdx, reviewFlipped, gradeReview]);

  useEffect(() => {
    if (!activeId || hub !== "lessons") return;
    (async () => {
      try {
        const m = await api.studyModule(activeId);
        setMod(m);
        setStep("learn");
        setBeatIdx(0);
        setSaid({});
        setLineIdx(0);
        setLineFeedback(null);
        setQuizIdx(0);
        setQuizShow(false);
        setFillAnswers({});
        setFillResult(null);
        setBlankText("");
        setBlankReveal(false);
      } catch (e: any) {
        toast.error(e?.message || "Failed to load module");
      }
    })();
  }, [activeId, hub]);

  const saveProgress = (patch: Record<string, any>) => {
    if (!mod) return;
    const next = {
      ...progress,
      [mod.id]: { ...(progress[mod.id] || {}), ...patch, at: new Date().toISOString() },
    };
    setProgress(next);
    localStorage.setItem("study-lab-v2", JSON.stringify(next));
  };

  const markKnown = (id: string, v: boolean) => {
    const next = { ...known, [id]: v };
    setKnown(next);
    localStorage.setItem("study-flash-known", JSON.stringify(next));
  };

  const stepIndex = STUDY_STEPS.findIndex((s) => s.id === step);
  const goNextStep = () => {
    if (stepIndex < STUDY_STEPS.length - 1) {
      setStep(STUDY_STEPS[stepIndex + 1].id);
      saveProgress({ step: STUDY_STEPS[stepIndex + 1].id });
    }
  };
  const goPrevStep = () => {
    if (stepIndex > 0) setStep(STUDY_STEPS[stepIndex - 1].id);
  };

  const lineQuiz = beat?.line_quiz || [];
  const currentLQ = lineQuiz[lineIdx];
  const choices = useMemo(
    () => (currentLQ ? shuffle(currentLQ.choices || [currentLQ.answer]) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentLQ?.line, currentLQ?.prompt, beat?.id],
  );

  const blankScore = useMemo(() => {
    if (!beat?.code || !blankText.trim()) return null;
    const a = new Set(normalize(blankText).split(/[^a-z0-9_]+/).filter(Boolean));
    const b = normalize(beat.code).split(/[^a-z0-9_]+/).filter(Boolean);
    if (!b.length) return 0;
    let hit = 0;
    for (const t of b) if (a.has(t)) hit++;
    return hit / b.length;
  }, [blankText, beat?.code]);

  const onLineChoice = async (choice: string) => {
    if (!mod || !beat || !currentLQ) return;
    try {
      const res = await api.studyGradeLine({
        module_id: mod.id,
        beat_id: beat.id,
        line: currentLQ.line,
        choice,
      });
      setLineFeedback(
        res.ok
          ? `✓ Correct. ${res.why || ""}`
          : `✗ Not quite. Expected: ${res.expected}. ${res.why || ""}`,
      );
    } catch {
      const ok = normalize(choice) === normalize(currentLQ.answer);
      setLineFeedback(ok ? "✓ Correct" : `✗ Expected: ${currentLQ.answer}`);
    }
  };

  const onGradeFill = async () => {
    if (!mod || !beat?.fill_blanks) return;
    try {
      const res = await api.studyGradeFill({
        module_id: mod.id,
        beat_id: beat.id,
        answers: fillAnswers,
      });
      setFillResult(res);
      toast.success(`Fill score ${(res.score * 100).toFixed(0)}%`);
      saveProgress({ fill_score: res.score });
    } catch (e: any) {
      toast.error(e?.message || "Grade failed");
    }
  };

  const byTrack = useMemo(() => {
    const map = new Map<string, StudyModuleSummary[]>();
    for (const m of modules) {
      const t = m.track || "foundations";
      if (!map.has(t)) map.set(t, []);
      map.get(t)!.push(m);
    }
    return map;
  }, [modules]);

  const saidCount = Object.values(said).filter(Boolean).length;
  const sayTotal = mod?.say_aloud?.length || 0;
  const card = cards[cardIdx];
  const knownCount = cards.filter((c) => known[c.id]).length;

  return (
    <div className="min-h-screen bg-[var(--surface-0)] text-[var(--text-0)]">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-black/75 backdrop-blur-xl">
        <div className="max-w-[1100px] mx-auto px-4 py-3 flex items-center gap-3 flex-wrap">
          <Link href="/" className="inline-flex items-center gap-1 text-sm text-white/55 hover:text-white">
            <ChevronLeft size={16} /> App
          </Link>
          <GraduationCap className="text-emerald-400" size={20} />
          <div>
            <div className="font-semibold">Study Lab</div>
            <div className="text-[11px] text-white/45">
              Grounded lessons · authoritative flashcards (5W+H)
            </div>
          </div>
          <div
            className={`flex rounded-lg border border-white/15 overflow-hidden text-xs ml-2 ${
              focusMode ? "hidden" : ""
            }`}
          >
            <button
              type="button"
              onClick={() => setHub("today")}
              aria-pressed={hub === "today"}
              className={`px-3 py-1.5 inline-flex items-center gap-1 ${
                hub === "today" ? "bg-emerald-600 text-white" : "bg-white/5 text-white/60"
              }`}
            >
              <GraduationCap size={12} /> Today
            </button>
            <button
              type="button"
              onClick={() => setHub("masters")}
              aria-pressed={hub === "masters"}
              className={`px-3 py-1.5 inline-flex items-center gap-1 ${
                hub === "masters" ? "bg-emerald-600 text-white" : "bg-white/5 text-white/60"
              }`}
            >
              <ScrollText size={12} /> Masters
            </button>
            <button
              type="button"
              onClick={() => setHub("flashcards")}
              aria-pressed={hub === "flashcards"}
              className={`px-3 py-1.5 inline-flex items-center gap-1 ${
                hub === "flashcards" ? "bg-emerald-600 text-white" : "bg-white/5 text-white/60"
              }`}
            >
              <Layers size={12} /> Flashcards
            </button>
            <button
              type="button"
              onClick={() => setHub("lessons")}
              className={`px-3 py-1.5 inline-flex items-center gap-1 ${
                hub === "lessons" ? "bg-emerald-600 text-white" : "bg-white/5 text-white/60"
              }`}
            >
              <BookOpen size={12} /> Lessons
            </button>
          </div>
          <div className="flex-1" />
          <button
            type="button"
            onClick={() => setFocusMode((f) => !f)}
            aria-pressed={focusMode}
            title="Focus mode: hide navigation to reduce distraction"
            className={`inline-flex items-center gap-1.5 text-xs border rounded-lg px-2.5 py-1.5 ${
              focusMode
                ? "border-emerald-500/50 bg-emerald-600/20 text-emerald-200"
                : "border-white/15 text-white/70 hover:bg-white/5"
            }`}
          >
            <Target size={12} /> Focus
          </button>
          <button
            type="button"
            onClick={() =>
              api.studyReseed().then((r) => {
                toast.success(
                  `Reseeded ${r.seeded?.length || 0} lessons · ${r.flashcards || "?"} cards`,
                );
                setActiveId(null);
                loadList();
                loadCards();
              })
            }
            className="inline-flex items-center gap-1.5 text-xs border border-white/15 rounded-lg px-2.5 py-1.5 text-white/70 hover:bg-white/5"
          >
            <RefreshCw size={12} /> Reset content
          </button>
          <button
            type="button"
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center gap-1.5 text-xs border border-white/10 rounded-lg px-2.5 py-1.5 text-white/50 hover:bg-white/5"
          >
            <Upload size={12} /> Upload
          </button>
        </div>
      </header>

      {showIntro && (
        <div className="max-w-[820px] mx-auto mt-4 px-4">
          <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/[0.06] p-4 text-sm">
            <div className="font-semibold text-emerald-200 mb-1">Welcome to Study Lab 👋</div>
            <ul className="text-white/75 space-y-1 list-disc pl-5 text-[13px]">
              <li>
                <b>Today</b> — spaced repetition (SM-2). Rate recall Again/Hard/Good/Easy; keys
                1-4, Space flips.
              </li>
              <li>
                <b>Lessons</b> — 6 steps: Learn → Say → Code → Quiz → Rewrite → Boss. Each has
                Python cheat-codes and a “Go deeper” list of real sources.
              </li>
              <li>
                <b>Flashcards</b> — 5W+H explainers. <b>Focus</b> hides the nav when you want to
                concentrate.
              </li>
            </ul>
            <button
              type="button"
              onClick={dismissIntro}
              className="mt-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-medium"
            >
              Got it
            </button>
          </div>
        </div>
      )}

      {/* ═══════════════ TODAY (spaced repetition) ═══════════════ */}
      {hub === "today" && (
        <div className="max-w-[820px] mx-auto px-4 py-6 space-y-5">
          {/* Dashboard */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Streak", value: `${dash?.streak ?? 0}🔥`, hint: "days in a row" },
              { label: "Due today", value: dash?.due_today ?? 0, hint: "cards to review" },
              { label: "Reviewed", value: dash?.reviewed_today ?? 0, hint: "so far today" },
              { label: "Mastery", value: `${dash?.mastery_overall_pct ?? 0}%`, hint: "solid recall" },
            ].map((s) => (
              <div key={s.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                <div className="text-2xl font-bold text-emerald-300">{s.value}</div>
                <div className="text-xs text-white/70">{s.label}</div>
                <div className="text-[10px] text-white/40">{s.hint}</div>
              </div>
            ))}
          </div>

          {/* Mastery per track */}
          {dash?.mastery_by_track && Object.keys(dash.mastery_by_track).length > 0 && (
            <div className="rounded-2xl border border-white/10 p-4 space-y-2">
              <div className="text-sm font-medium text-white/80">Mastery by track</div>
              {Object.entries(dash.mastery_by_track).map(([track, m]: [string, any]) => (
                <div key={track} className="space-y-1">
                  <div className="flex justify-between text-xs text-white/60">
                    <span>{TRACK_LABEL[track] || track}</span>
                    <span>
                      {m.strong}/{m.total} · {m.pct}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full bg-emerald-500"
                      style={{ width: `${m.pct}%` }}
                      role="progressbar"
                      aria-valuenow={m.pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${track} mastery ${m.pct}%`}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Review session */}
          {dueCards.length === 0 ? (
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 text-center">
              <CheckCircle2 className="mx-auto text-emerald-400 mb-2" />
              <div className="font-medium">All caught up for today 🎉</div>
              <div className="text-sm text-white/60 mt-1">
                Come back tomorrow — SM-2 brings the right cards back automatically.
              </div>
            </div>
          ) : (
            (() => {
              const rc = dueCards[reviewIdx];
              if (!rc) return null;
              return (
                <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-transparent p-5 space-y-4">
                  <div className="flex justify-between text-xs text-white/50">
                    <span>
                      Card {reviewIdx + 1} / {dueCards.length}
                    </span>
                    <span>{TRACK_LABEL[rc.track] || rc.track}</span>
                  </div>
                  <div className="text-lg font-semibold">{rc.front}</div>
                  {!reviewFlipped ? (
                    <button
                      type="button"
                      onClick={() => setReviewFlipped(true)}
                      className="w-full rounded-xl border border-white/15 py-3 text-sm text-white/70 hover:bg-white/5"
                    >
                      Show answer <span className="text-white/40">(Space)</span>
                    </button>
                  ) : (
                    <div className="space-y-3">
                      <div className="grid sm:grid-cols-2 gap-2 text-sm">
                        {W_FIELDS.map((f) =>
                          rc[f.key] ? (
                            <div key={f.label} className="rounded-lg bg-black/30 border border-white/10 p-2">
                              <span className="text-[10px] uppercase text-emerald-300/80">{f.label}</span>
                              <div className="text-white/80">{String(rc[f.key])}</div>
                            </div>
                          ) : null,
                        )}
                      </div>
                      {rc.code && (
                        <pre className="rounded-lg bg-[#0a0a0f] border border-white/10 p-2 text-[11.5px] font-mono text-emerald-100/90 whitespace-pre-wrap overflow-x-auto">
                          {rc.code}
                        </pre>
                      )}
                      <div className="grid grid-cols-4 gap-2">
                        {(
                          [
                            ["again", "Again", "1", "bg-rose-600/80"],
                            ["hard", "Hard", "2", "bg-amber-600/80"],
                            ["good", "Good", "3", "bg-emerald-600/80"],
                            ["easy", "Easy", "4", "bg-sky-600/80"],
                          ] as const
                        ).map(([q, label, key, cls]) => (
                          <button
                            key={q}
                            type="button"
                            onClick={() => gradeReview(q)}
                            aria-label={`${label} (key ${key})`}
                            className={`${cls} rounded-xl py-2.5 text-sm font-medium text-white hover:brightness-110`}
                          >
                            {label}
                            <span className="block text-[10px] opacity-70">{key}</span>
                          </button>
                        ))}
                      </div>
                      <p className="text-[11px] text-white/40 text-center">
                        Honesty = faster mastery. Rate how well you recalled — SM-2 schedules the rest.
                      </p>
                    </div>
                  )}
                </div>
              );
            })()
          )}
        </div>
      )}

      {/* ═══════════════ MASTERS (verbatim memorize) ═══════════════ */}
      {hub === "masters" &&
        (activeMaster ? (
          <MasterclassReader mc={activeMaster} onBack={() => setActiveMaster(null)} />
        ) : (
          <div className="max-w-[820px] mx-auto px-4 py-6 space-y-4">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="text-sm font-semibold text-white/90">Master This Code — memorize verbatim</div>
              <p className="text-[13px] text-white/55 mt-1">
                Full guides stored word-for-word. Use <b>Memorize mode</b> to blur the text and
                recall it, then hover to reveal and check yourself.
              </p>
            </div>
            {mastersList.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => openMaster(m.id)}
                className="w-full text-left rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/[0.07] to-transparent p-4 hover:border-emerald-500/40"
              >
                <div className="flex items-start gap-3">
                  <ScrollText size={18} className="text-emerald-300 mt-0.5 shrink-0" />
                  <div>
                    <div className="font-semibold text-white">{m.title}</div>
                    {m.subtitle && <div className="text-[13px] text-white/55 mt-0.5">{m.subtitle}</div>}
                    <div className="mt-1 flex items-center gap-2 flex-wrap text-[11px] text-white/40">
                      <span>~{m.estimated_minutes} min</span>
                      <span>·</span>
                      <span>{m.char_count.toLocaleString()} chars</span>
                      {m.tags.slice(0, 3).map((t) => (
                        <span key={t} className="rounded bg-white/10 px-1.5 py-0.5 text-white/50">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </button>
            ))}
            {mastersList.length === 0 && (
              <div className="text-sm text-white/40">Loading guides…</div>
            )}
          </div>
        ))}

      {/* ═══════════════ FLASHCARDS HUB ═══════════════ */}
      {hub === "flashcards" && (
        <div className="max-w-[900px] mx-auto px-4 py-6 space-y-4">
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-violet-500/10 to-transparent p-4">
            <h1 className="text-lg font-semibold">Master deck — every concept, one card at a time</h1>
            <p className="text-sm text-white/60 mt-1">
              Each card has What / How / Where / When / Who / Why, optional code, pitfalls, and
              authoritative sources (W3C, Neo4j, academic papers, SRE practices). Not mock-derived.
            </p>
            <div className="text-xs text-white/45 mt-2">
              Showing {cards.length} cards · marked known {knownCount}/{cards.length}
            </div>
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            <select
              value={fTrack}
              onChange={(e) => setFTrack(e.target.value)}
              className="text-xs rounded-lg border border-white/15 bg-white/5 px-2 py-1.5"
            >
              <option value="">All tracks</option>
              {cardFilters.tracks.map((t) => (
                <option key={t} value={t}>
                  {TRACK_LABEL[t] || t}
                </option>
              ))}
            </select>
            <select
              value={fKind}
              onChange={(e) => setFKind(e.target.value)}
              className="text-xs rounded-lg border border-white/15 bg-white/5 px-2 py-1.5"
            >
              <option value="">All kinds</option>
              {cardFilters.kinds.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
            <select
              value={fTag}
              onChange={(e) => setFTag(e.target.value)}
              className="text-xs rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 max-w-[160px]"
            >
              <option value="">All tags</option>
              {cardFilters.tags.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              value={fQ}
              onChange={(e) => setFQ(e.target.value)}
              placeholder="Search…"
              className="text-xs rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 flex-1 min-w-[120px]"
            />
            <button
              type="button"
              onClick={() => {
                setCards((c) => shuffle(c));
                setCardIdx(0);
                setCardFlipped(false);
              }}
              className="text-xs inline-flex items-center gap-1 border border-white/15 rounded-lg px-2 py-1.5"
            >
              <Shuffle size={12} /> Shuffle
            </button>
          </div>

          {!card ? (
            <div className="text-center text-white/40 py-16">No cards match filters.</div>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setCardFlipped((f) => !f)}
                className="w-full text-left rounded-2xl border border-violet-500/30 bg-violet-500/5 p-6 min-h-[280px] hover:border-violet-400/50 transition"
              >
                {!cardFlipped ? (
                  <div className="flex flex-col items-center justify-center min-h-[220px] gap-3">
                    <div className="text-[10px] uppercase tracking-wide text-violet-300/70">
                      {card.kind} · {TRACK_LABEL[card.track] || card.track} · {card.difficulty}
                    </div>
                    <div className="text-2xl font-semibold text-center">{card.front}</div>
                    <div className="text-xs text-white/40">Click to reveal 5W+H explainers</div>
                    <div className="flex flex-wrap gap-1 justify-center">
                      {card.tags.map((t) => (
                        <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-white/10">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="text-lg font-semibold text-violet-100">{card.front}</div>
                    {W_FIELDS.map(({ key, label }) => {
                      const val = card[key];
                      if (!val || typeof val !== "string") return null;
                      return (
                        <div key={key}>
                          <div className="text-[11px] font-semibold text-emerald-300/90 uppercase tracking-wide">
                            {label}
                          </div>
                          <div className="text-sm text-white/80 leading-relaxed">{val}</div>
                        </div>
                      );
                    })}
                    {card.analogy && (
                      <div>
                        <div className="text-[11px] font-semibold text-amber-300/90 uppercase">
                          Analogy
                        </div>
                        <div className="text-sm text-white/75">{card.analogy}</div>
                      </div>
                    )}
                    {card.say_aloud && (
                      <div className="text-sm border border-emerald-500/20 bg-emerald-500/5 rounded-lg px-3 py-2">
                        <strong className="text-emerald-200">Say aloud:</strong> {card.say_aloud}
                      </div>
                    )}
                    {card.code && (
                      <CodeBlock code={card.code} language={card.language || "text"} />
                    )}
                    {!!card.pitfalls?.length && (
                      <div>
                        <div className="text-[11px] font-semibold text-rose-300/90 uppercase">
                          Pitfalls
                        </div>
                        <ul className="list-disc pl-5 text-sm text-white/70">
                          {card.pitfalls.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
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
                  </div>
                )}
              </button>

              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-xs text-white/45">
                  Card {cardIdx + 1} / {cards.length}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={cardIdx <= 0}
                    onClick={() => {
                      setCardIdx((i) => i - 1);
                      setCardFlipped(false);
                    }}
                    className="text-xs border border-white/15 rounded-lg px-3 py-1.5 disabled:opacity-30 inline-flex items-center gap-1"
                  >
                    <ChevronLeft size={12} /> Prev
                  </button>
                  <button
                    type="button"
                    onClick={() => markKnown(card.id, !known[card.id])}
                    className={`text-xs rounded-lg px-3 py-1.5 border ${
                      known[card.id]
                        ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-100"
                        : "border-white/15"
                    }`}
                  >
                    {known[card.id] ? "✓ Known" : "Mark known"}
                  </button>
                  <button
                    type="button"
                    disabled={cardIdx >= cards.length - 1}
                    onClick={() => {
                      setCardIdx((i) => i + 1);
                      setCardFlipped(false);
                    }}
                    className="text-xs border border-white/15 rounded-lg px-3 py-1.5 disabled:opacity-30 inline-flex items-center gap-1"
                  >
                    Next <ChevronRight size={12} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ═══════════════ LESSONS HUB ═══════════════ */}
      {hub === "lessons" && (
        <div className="max-w-[1100px] mx-auto px-4 py-5 grid grid-cols-1 md:grid-cols-[240px_1fr] gap-5">
          <aside className="space-y-4 max-h-[80vh] overflow-y-auto pr-1">
            <p className="text-[11px] text-white/40 uppercase tracking-wide">Path (do in order)</p>
            {loading && <p className="text-sm text-white/40">Loading…</p>}
            {[...byTrack.entries()].map(([track, list]) => (
              <div key={track}>
                <div className="text-[11px] font-medium text-emerald-400/80 mb-1.5">
                  {TRACK_LABEL[track] || track}
                </div>
                <div className="space-y-1">
                  {list.map((m) => {
                    const active = m.id === activeId;
                    const done = progress[m.id]?.boss;
                    return (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setActiveId(m.id)}
                        className={`w-full text-left rounded-lg px-2.5 py-2 text-sm border transition ${
                          active
                            ? "border-emerald-500/45 bg-emerald-500/10"
                            : "border-transparent hover:bg-white/5"
                        }`}
                      >
                        <div className="flex items-start gap-1.5">
                          {done ? (
                            <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                          ) : (
                            <span className="w-3.5" />
                          )}
                          <span className="leading-snug">{m.title}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </aside>

          <main className="min-w-0 space-y-4">
            {!mod ? (
              <div className="rounded-2xl border border-white/10 p-10 text-center text-white/50">
                Pick a lesson. Prefer Flashcards hub for full 5W+H coverage.
              </div>
            ) : (
              <>
                <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/10 via-transparent to-transparent p-5">
                  <div className="text-[11px] text-emerald-300/80 mb-1">
                    {TRACK_LABEL[mod.track || "foundations"]} · hand-authored path
                  </div>
                  <h1 className="text-xl font-semibold tracking-tight">{mod.title}</h1>
                  <p className="text-emerald-200/90 font-medium mt-2 text-[15px]">{mod.one_liner}</p>
                  {!!mod.why_it_matters?.length && (
                    <ul className="mt-3 text-sm text-white/65 list-disc pl-5 space-y-1">
                      {mod.why_it_matters.map((w) => (
                        <li key={w}>{w}</li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="flex flex-wrap gap-1">
                  {STUDY_STEPS.map((s, i) => (
                    <button
                      key={s.id}
                      type="button"
                      title={s.tip}
                      onClick={() => setStep(s.id)}
                      className={`text-xs rounded-full px-3 py-1.5 border font-medium ${
                        step === s.id
                          ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-100"
                          : i < stepIndex
                            ? "border-white/15 text-white/55"
                            : "border-white/10 text-white/35"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>

                {step === "learn" && (
                  <section className="rounded-2xl border border-white/10 p-5 space-y-4">
                    <h2 className="text-sm font-semibold">Read once. Slowly.</h2>
                    <p className="text-[15px] leading-relaxed text-white/85 whitespace-pre-wrap">
                      {mod.story}
                    </p>
                    {!!mod.cheat_sheet?.length && (
                      <div className="grid sm:grid-cols-2 gap-2">
                        {mod.cheat_sheet.map((row) => (
                          <div
                            key={row.term}
                            className="rounded-lg border border-white/10 bg-black/30 px-3 py-2"
                          >
                            <div className="text-sm font-medium text-emerald-200">{row.term}</div>
                            <div className="text-xs text-white/60 mt-0.5">{row.meaning}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {!!mod.further_reading?.length && (
                      <details className="rounded-xl border border-sky-500/25 bg-sky-500/[0.04] p-3">
                        <summary className="cursor-pointer text-sm font-medium text-sky-200 flex items-center gap-2">
                          <BookOpen size={14} /> Go deeper — {mod.further_reading.length} curated
                          sources
                        </summary>
                        <ul className="mt-3 space-y-3">
                          {mod.further_reading.map((r) => (
                            <li
                              key={r.title}
                              className="rounded-lg border border-white/10 bg-black/30 p-3"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <a
                                  href={r.url || "#"}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm font-medium text-sky-300 hover:underline"
                                >
                                  {r.title}
                                </a>
                                {r.kind && (
                                  <span className="shrink-0 text-[10px] uppercase tracking-wide text-white/40 border border-white/15 rounded px-1.5 py-0.5">
                                    {r.kind}
                                  </span>
                                )}
                              </div>
                              {r.author && (
                                <div className="text-[11px] text-white/45 mt-0.5">{r.author}</div>
                              )}
                              {r.takeaway && (
                                <p className="text-xs text-white/75 mt-1.5">💡 {r.takeaway}</p>
                              )}
                              {r.why && (
                                <p className="text-[11px] text-emerald-300/80 mt-1">
                                  Why here: {r.why}
                                </p>
                              )}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                    <button
                      type="button"
                      onClick={goNextStep}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
                    >
                      Next: Say aloud →
                    </button>
                  </section>
                )}

                {step === "say" && (
                  <section className="rounded-2xl border border-white/10 p-5 space-y-4">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <Mic size={16} className="text-amber-300" /> Speak each line
                    </div>
                    <p className="text-xs text-white/45">
                      {saidCount}/{sayTotal} spoken
                    </p>
                    {(mod.say_aloud || []).map((line, i) => (
                      <label
                        key={i}
                        className={`flex gap-3 items-start rounded-xl border px-3 py-3 cursor-pointer ${
                          said[i]
                            ? "border-emerald-500/40 bg-emerald-500/10"
                            : "border-white/10"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={!!said[i]}
                          onChange={(e) => setSaid((s) => ({ ...s, [i]: e.target.checked }))}
                          className="mt-1"
                        />
                        <span className="text-sm leading-relaxed">{line}</span>
                      </label>
                    ))}
                    <button
                      type="button"
                      disabled={sayTotal > 0 && saidCount < sayTotal}
                      onClick={goNextStep}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 px-4 py-2 text-sm font-medium"
                    >
                      Next: Code →
                    </button>
                  </section>
                )}

                {step === "code" && beat && (
                  <section className="space-y-3">
                    <div className="flex flex-wrap gap-1.5">
                      {mod.beats.map((b, i) => (
                        <button
                          key={b.id}
                          type="button"
                          onClick={() => setBeatIdx(i)}
                          className={`text-xs rounded-md px-2 py-1 border ${
                            i === beatIdx
                              ? "border-emerald-500/40 bg-emerald-500/10"
                              : "border-white/10"
                          }`}
                        >
                          Bite {i + 1}
                        </button>
                      ))}
                    </div>
                    {beat.goal && (
                      <div className="text-sm text-amber-100/90 border border-amber-500/20 bg-amber-500/5 rounded-lg px-3 py-2">
                        <strong>Goal:</strong> {beat.goal}
                      </div>
                    )}
                    <p className="text-sm text-white/65">{beat.narrative}</p>
                    <CodeBlock
                      code={beat.code}
                      language={beat.language}
                      annotations={beat.annotations}
                    />
                    {!!beat.pro_tips?.length && (
                      <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.05] p-3 space-y-1.5">
                        <div className="text-sm font-medium text-amber-200 flex items-center gap-2">
                          <BookOpen size={14} /> Pro tips (source-backed)
                        </div>
                        <ul className="space-y-1.5">
                          {beat.pro_tips.map((t) => (
                            <li key={t} className="text-[13px] text-white/80 leading-relaxed">
                              {t.startsWith("GOTCHA") ? "⚠️ " : "💡 "}
                              {t}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {mod.python_cheatsheet && mod.python_cheatsheet.length > 0 && (
                      <details className="rounded-xl border border-sky-500/25 bg-sky-500/5">
                        <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-sky-200/90 select-none">
                          🐍 Python cheat-codes for this topic ({mod.python_cheatsheet.length}) —
                          new to Python? open this
                        </summary>
                        <div className="p-3 pt-0 space-y-2">
                          {mod.python_cheatsheet.map((c, i) => (
                            <div
                              key={`${c.category}-${c.label}-${i}`}
                              className="rounded-lg border border-white/10 bg-black/30 p-2.5"
                            >
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-[10px] uppercase tracking-wide rounded bg-sky-500/20 text-sky-200 px-1.5 py-0.5">
                                  {c.category}
                                </span>
                                <span className="text-sm font-semibold text-white/90">
                                  {c.label}
                                </span>
                              </div>
                              <div className="text-sm text-emerald-200/90 mt-1">✅ Rule: {c.rule}</div>
                              {c.why && (
                                <div className="text-xs text-white/60 mt-0.5">Why: {c.why}</div>
                              )}
                              {c.code && (
                                <pre className="mt-1.5 rounded bg-[#0a0a0f] border border-white/10 p-2 text-[11.5px] font-mono text-emerald-100/90 whitespace-pre-wrap overflow-x-auto">
                                  {c.code}
                                </pre>
                              )}
                              {c.gotcha && (
                                <div className="text-xs text-rose-300/80 mt-1">⚠️ Trap: {c.gotcha}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                    {beat.fill_blanks && (
                      <div className="rounded-xl border border-white/10 p-4 space-y-2">
                        <pre className="text-xs font-mono whitespace-pre-wrap text-white/70">
                          {beat.fill_blanks.template}
                        </pre>
                        <div className="grid sm:grid-cols-2 gap-2">
                          {beat.fill_blanks.blanks.map((b) => (
                            <input
                              key={b.id}
                              value={fillAnswers[b.id] || ""}
                              onChange={(e) =>
                                setFillAnswers((p) => ({ ...p, [b.id]: e.target.value }))
                              }
                              placeholder={b.id}
                              className="rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 font-mono text-sm"
                            />
                          ))}
                        </div>
                        <button
                          type="button"
                          onClick={onGradeFill}
                          className="text-xs border border-white/15 rounded-lg px-3 py-1.5"
                        >
                          Check fills
                        </button>
                        {fillResult && (
                          <div className="text-xs">
                            Score {(fillResult.score * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={goNextStep}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
                    >
                      Next: Quiz →
                    </button>
                  </section>
                )}

                {step === "quiz" && (
                  <section className="rounded-2xl border border-white/10 p-5 space-y-5">
                    {beat && lineQuiz.length > 0 && currentLQ && (
                      <div className="space-y-3">
                        <CodeBlock
                          code={beat.code}
                          language={beat.language}
                          highlightLine={currentLQ.line}
                        />
                        <p className="text-sm font-medium">{currentLQ.prompt}</p>
                        {choices.map((c) => (
                          <button
                            key={c}
                            type="button"
                            onClick={() => onLineChoice(c)}
                            className="block w-full text-left text-sm rounded-lg border border-white/10 px-3 py-2 hover:border-emerald-500/40"
                          >
                            {c}
                          </button>
                        ))}
                        {lineFeedback && (
                          <div className="text-sm border border-white/10 rounded-lg px-3 py-2">
                            {lineFeedback}
                          </div>
                        )}
                        <div className="flex gap-2">
                          <button
                            type="button"
                            disabled={lineIdx <= 0}
                            onClick={() => {
                              setLineIdx((x) => x - 1);
                              setLineFeedback(null);
                            }}
                            className="text-xs border border-white/15 rounded px-2 py-1 disabled:opacity-30"
                          >
                            Prev
                          </button>
                          <button
                            type="button"
                            disabled={lineIdx >= lineQuiz.length - 1}
                            onClick={() => {
                              setLineIdx((x) => x + 1);
                              setLineFeedback(null);
                            }}
                            className="text-xs border border-white/15 rounded px-2 py-1 disabled:opacity-30"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    )}
                    {!!mod.self_quiz?.length && (
                      <div className="space-y-2 border-t border-white/10 pt-3">
                        <p className="text-base font-medium">{mod.self_quiz[quizIdx].q}</p>
                        {quizShow ? (
                          <div className="text-sm text-emerald-200">{mod.self_quiz[quizIdx].a}</div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setQuizShow(true)}
                            className="text-sm border border-white/15 rounded-lg px-3 py-1.5"
                          >
                            Reveal
                          </button>
                        )}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={goNextStep}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
                    >
                      Next: Rewrite →
                    </button>
                  </section>
                )}

                {step === "rewrite" && beat && (
                  <section className="rounded-2xl border border-white/10 p-5 space-y-3">
                    <div className="flex justify-between">
                      <h2 className="text-sm font-semibold">Type from memory</h2>
                      <button
                        type="button"
                        onClick={() => setBlankReveal((v) => !v)}
                        className="text-xs inline-flex items-center gap-1 border border-white/15 rounded-lg px-2 py-1"
                      >
                        {blankReveal ? <EyeOff size={12} /> : <Eye size={12} />} Peek
                      </button>
                    </div>
                    <textarea
                      value={blankText}
                      onChange={(e) => setBlankText(e.target.value)}
                      rows={12}
                      spellCheck={false}
                      className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2 font-mono text-sm"
                    />
                    {blankScore != null && (
                      <div className="text-sm">
                        Overlap:{" "}
                        <strong className="text-emerald-300">
                          {(blankScore * 100).toFixed(0)}%
                        </strong>
                      </div>
                    )}
                    {blankReveal && (
                      <CodeBlock code={beat.code} language={beat.language} annotations={beat.annotations} />
                    )}
                    <button
                      type="button"
                      onClick={goNextStep}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-sm font-medium"
                    >
                      Next: Boss →
                    </button>
                  </section>
                )}

                {step === "boss" && (
                  <section className="rounded-2xl border border-amber-500/25 bg-amber-500/5 p-5 space-y-3">
                    <ol className="list-decimal pl-5 space-y-2 text-sm">
                      {(mod.final_boss || []).map((b) => (
                        <li key={b}>{b}</li>
                      ))}
                    </ol>
                    <button
                      type="button"
                      onClick={() => {
                        saveProgress({ boss: true, step: "boss" });
                        toast.success("Lesson marked complete");
                      }}
                      className="rounded-lg bg-amber-600/90 px-4 py-2 text-sm font-medium"
                    >
                      Mark complete
                    </button>
                  </section>
                )}

                <div className="flex justify-between text-xs text-white/40">
                  <button type="button" onClick={goPrevStep}>
                    ← Prev step
                  </button>
                  <button type="button" onClick={goNextStep}>
                    Next step →
                  </button>
                </div>
              </>
            )}
          </main>
        </div>
      )}

      {showUpload && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-white/15 bg-[#0e0e12] p-5 space-y-3">
            <div className="flex justify-between">
              <h2 className="font-semibold text-sm">Upload notes (advanced)</h2>
              <button type="button" onClick={() => setShowUpload(false)} className="text-white/50">
                Close
              </button>
            </div>
            <p className="text-xs text-white/45">
              Prefer Flashcards + grounded lessons. Uploads are rough extras, not the master deck.
            </p>
            <input
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="Title"
              className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm"
            />
            <input
              type="file"
              accept=".md,.txt,.ipynb,.py"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                try {
                  const res = await api.studyUpload(f, uploadTitle, "");
                  toast.success(`Created ${res.module?.id}`);
                  setShowUpload(false);
                  setHub("lessons");
                  await loadList();
                } catch (err: any) {
                  toast.error(err?.message || "fail");
                }
              }}
            />
            <textarea
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 font-mono text-xs"
            />
            <button
              type="button"
              disabled={!paste.trim()}
              onClick={async () => {
                try {
                  await api.studyGenerate({ title: uploadTitle, text: paste });
                  toast.success("Generated");
                  setShowUpload(false);
                  setPaste("");
                  setHub("lessons");
                  loadList();
                } catch (err: any) {
                  toast.error(err?.message || "fail");
                }
              }}
              className="w-full rounded-lg bg-white/10 py-2 text-sm disabled:opacity-40"
            >
              Generate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
