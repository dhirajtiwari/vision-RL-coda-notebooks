export type StudyLanguage =
  | "python"
  | "cypher"
  | "turtle"
  | "sparql"
  | "text"
  | "typescript"
  | "bash";

export type StudyTrack = "foundations" | "graph" | "pipeline" | "runtime" | "agent";

/** Linear memorize path — one step at a time */
export type StudyStep = "learn" | "say" | "code" | "quiz" | "rewrite" | "boss";

export interface StudyModuleSummary {
  id: string;
  title: string;
  description: string;
  tags: string[];
  track?: StudyTrack;
  source: string;
  order: number;
  estimated_minutes: number;
  grounded?: boolean;
  beat_count: number;
  concept_count: number;
  quiz_count: number;
  line_quiz_count: number;
  say_aloud_count?: number;
  cheat_sheet_count?: number;
}

export interface LineAnnotation {
  line: number;
  note: string;
}

export interface LineQuizItem {
  line: number;
  prompt: string;
  answer: string;
  choices: string[];
  why?: string;
}

export interface BlankSpec {
  id: string;
  answer: string;
  hint?: string;
}

export interface FillBlanks {
  template: string;
  blanks: BlankSpec[];
}

export interface CodeBeat {
  id: string;
  title: string;
  language: StudyLanguage;
  goal?: string;
  narrative: string;
  code: string;
  say_after?: string;
  annotations: LineAnnotation[];
  line_quiz: LineQuizItem[];
  fill_blanks: FillBlanks | null;
  pro_tips?: string[];
}

export interface ConceptCard {
  term: string;
  definition: string;
  analogy?: string;
  say_aloud?: string;
}

export interface QuizItem {
  q: string;
  a: string;
  difficulty?: string;
}

export interface StudyModule {
  id: string;
  title: string;
  description: string;
  tags: string[];
  track?: StudyTrack;
  story: string;
  one_liner: string;
  why_it_matters?: string[];
  say_aloud?: string[];
  cheat_sheet?: { term: string; meaning: string }[];
  change_table: Record<string, string>[];
  beats: CodeBeat[];
  concepts: ConceptCard[];
  self_quiz: QuizItem[];
  common_mistakes: string[];
  final_boss: string[];
  python_cheatsheet?: PyNuance[];
  further_reading?: ReadingRef[];
  source: string;
  order: number;
  estimated_minutes: number;
  grounded?: boolean;
}

export interface ReadingRef {
  title: string;
  url?: string;
  author?: string;
  kind?: string;
  takeaway?: string;
  why?: string;
  level?: string;
}

export interface MasterclassSummary {
  id: string;
  title: string;
  subtitle?: string;
  track?: StudyTrack;
  order: number;
  tags: string[];
  estimated_minutes: number;
  char_count: number;
}

export interface Masterclass extends MasterclassSummary {
  body: string;
}

export interface MemoryCard {
  id: string;
  masterclass_id: string;
  section: string;
  order: number;
  kind: "concept" | "line" | "block" | "pattern";
  front: string;
  code?: string;
  language?: StudyLanguage;
  explain?: string;
  mental_model?: string;
  memory_hook?: string;
  blank?: string;
  answers?: string[];
}

export interface PyNuance {
  label: string;
  category: string;
  rule: string;
  why?: string;
  code?: string;
  gotcha?: string;
  lang?: string;
}

export const STUDY_STEPS: { id: StudyStep; label: string; tip: string }[] = [
  { id: "learn", label: "1 · Learn", tip: "Read the story + cheat sheet" },
  { id: "say", label: "2 · Say", tip: "Speak lines out loud" },
  { id: "code", label: "3 · Code", tip: "Read tiny beats with notes" },
  { id: "quiz", label: "4 · Quiz", tip: "Line + concept questions" },
  { id: "rewrite", label: "5 · Rewrite", tip: "Type from memory" },
  { id: "boss", label: "6 · Boss", tip: "Final checklist" },
];
