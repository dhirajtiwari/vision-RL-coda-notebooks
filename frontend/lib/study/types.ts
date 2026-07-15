export type StudyLanguage =
  | "python"
  | "cypher"
  | "turtle"
  | "sparql"
  | "text"
  | "typescript"
  | "bash";

export interface StudyModuleSummary {
  id: string;
  title: string;
  description: string;
  tags: string[];
  source: string;
  order: number;
  estimated_minutes: number;
  beat_count: number;
  concept_count: number;
  quiz_count: number;
  line_quiz_count: number;
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
  narrative: string;
  code: string;
  annotations: LineAnnotation[];
  line_quiz: LineQuizItem[];
  fill_blanks: FillBlanks | null;
}

export interface ConceptCard {
  term: string;
  definition: string;
  analogy?: string;
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
  story: string;
  one_liner: string;
  change_table: Record<string, string>[];
  beats: CodeBeat[];
  concepts: ConceptCard[];
  self_quiz: QuizItem[];
  common_mistakes: string[];
  final_boss: string[];
  source: string;
  order: number;
  estimated_minutes: number;
}

export type StudyMode =
  | "story"
  | "annotated"
  | "line-quiz"
  | "fill"
  | "blank"
  | "flash"
  | "self-quiz"
  | "boss";
