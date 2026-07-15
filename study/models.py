"""Curriculum data models for the grounded Study Lab."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Language = Literal[
    "python",
    "cypher",
    "turtle",
    "sparql",
    "text",
    "typescript",
    "bash",
    "yaml",
    "hcl",
]

Track = Literal[
    "foundations",
    "graph",
    "pipeline",
    "runtime",
    "agent",
    "llmops",
    "observability",
    "evals",
    "cicd",
    "infra",
    "finops",
    "security",
    "integrations",
    "mlops",
    "aiops",
]


class LineAnnotation(BaseModel):
    line: int = Field(..., ge=1)
    note: str


class LineQuizItem(BaseModel):
    line: int = Field(..., ge=1)
    prompt: str
    answer: str
    choices: list[str] = Field(default_factory=list)
    why: str = ""


class BlankSpec(BaseModel):
    id: str
    answer: str
    hint: str = ""


class FillBlanks(BaseModel):
    template: str
    blanks: list[BlankSpec] = Field(default_factory=list)


class ConceptCard(BaseModel):
    term: str
    definition: str
    analogy: str = ""
    say_aloud: str = ""  # one sentence to speak from memory


class SourceRef(BaseModel):
    """Authoritative reference (standard, paper, or vendor docs)."""

    title: str
    url: str = ""
    kind: Literal["standard", "paper", "docs", "book", "spec"] = "docs"


class ReadingRef(BaseModel):
    """A curated 'go deeper' source: the authoritative publication/tutorial/repo
    behind a topic, plus the one thing to remember from it and why it matters.
    Every entry points at a real, citable primary source (W3C spec, vendor docs,
    canonical paper, or a well-known book/repo)."""

    title: str
    url: str = ""
    author: str = ""  # person / org / standards body
    kind: Literal["standard", "paper", "docs", "book", "tutorial", "repo", "spec"] = "docs"
    takeaway: str = ""  # the single most important idea to carry away
    why: str = ""  # why it matters for *this* project
    level: Literal["intro", "core", "deep"] = "core"


class FlashCard(BaseModel):
    """
    Full explainer flashcard: front for recall; back = 5W+H + sources + optional code.
    Designed for spaced run-through across the whole curriculum.
    """

    id: str
    front: str
    track: Track = "foundations"
    tags: list[str] = Field(default_factory=list)
    kind: Literal["concept", "code", "pattern", "process", "command", "theory"] = "concept"
    # 5W+H
    what: str = ""
    how: str = ""
    where: str = ""
    when: str = ""
    who: str = ""
    why: str = ""
    analogy: str = ""
    code: str = ""
    language: Language = "text"
    pitfalls: list[str] = Field(default_factory=list)
    say_aloud: str = ""
    sources: list[SourceRef] = Field(default_factory=list)
    related_module_ids: list[str] = Field(default_factory=list)
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class QuizItem(BaseModel):
    q: str
    a: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class PyNuance(BaseModel):
    """A Python cheat-code for a beginner: one memorizable rule + why + a tiny
    example + the trap it prevents. Designed so a non-Python developer can read
    the beat's code and know exactly *why* each idiom is used."""

    label: str  # short name, e.g. "with = auto-close"
    category: Literal[
        "syntax",
        "idiom",
        "stdlib",
        "typing",
        "gotcha",
        "performance",
        "style",
    ] = "idiom"
    rule: str  # the one-line cheat-code you can memorize
    why: str = ""  # what it buys you / what bug it prevents
    code: str = ""  # 2-4 line runnable example
    gotcha: str = ""  # the common beginner mistake / trap
    lang: Language = "python"


class CodeBeat(BaseModel):
    id: str
    title: str
    language: Language = "python"
    """One teaching goal for this beat (what you must walk away knowing)."""
    goal: str = ""
    narrative: str = ""
    code: str = ""
    """Tiny 'say this' after reading the code."""
    say_after: str = ""
    annotations: list[LineAnnotation] = Field(default_factory=list)
    line_quiz: list[LineQuizItem] = Field(default_factory=list)
    fill_blanks: FillBlanks | None = None
    """Source-backed 'pro tips' (verified TRICK/GOTCHA notes) shown under this beat."""
    pro_tips: list[str] = Field(default_factory=list)


class StudyModule(BaseModel):
    id: str
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    track: Track = "foundations"
    """Plain story you must be able to retell."""
    story: str = ""
    one_liner: str = ""
    """Why this exists in a real system (1-3 bullets)."""
    why_it_matters: list[str] = Field(default_factory=list)
    """Ordered sentences to speak out loud without notes."""
    say_aloud: list[str] = Field(default_factory=list)
    """Term → meaning table for quick revision."""
    cheat_sheet: list[dict[str, str]] = Field(default_factory=list)
    change_table: list[dict[str, str]] = Field(default_factory=list)
    beats: list[CodeBeat] = Field(default_factory=list)
    concepts: list[ConceptCard] = Field(default_factory=list)
    self_quiz: list[QuizItem] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    """Python cheat-codes: idioms/rules/traps for this topic's code (beginner-friendly)."""
    python_cheatsheet: list[PyNuance] = Field(default_factory=list)
    """Curated authoritative sources to go deeper (standards, papers, docs, books)."""
    further_reading: list[ReadingRef] = Field(default_factory=list)
    final_boss: list[str] = Field(default_factory=list)
    source: str = "seed"
    order: int = 100
    estimated_minutes: int = 25
    """If true, this is hand-authored grounded content (preferred)."""
    grounded: bool = True

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "track": self.track,
            "source": self.source,
            "order": self.order,
            "estimated_minutes": self.estimated_minutes,
            "grounded": self.grounded,
            "beat_count": len(self.beats),
            "concept_count": len(self.concepts),
            "quiz_count": len(self.self_quiz),
            "line_quiz_count": sum(len(b.line_quiz) for b in self.beats),
            "say_aloud_count": len(self.say_aloud),
            "cheat_sheet_count": len(self.cheat_sheet),
            "python_cheat_count": len(self.python_cheatsheet),
            "reading_count": len(self.further_reading),
        }


class ProgressPayload(BaseModel):
    module_id: str
    mode: str
    score: float | None = None
    completed_beat_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    step: str = ""  # learn | say | code | quiz | rewrite | boss


class Masterclass(BaseModel):
    """A long-form 'Master This Code' guide to memorize VERBATIM.

    Unlike a StudyModule (interactive, paraphrased), a Masterclass stores the
    exact guide text so the learner can memorize it word-for-word. `body` is the
    full markdown; the frontend splits it by headings for a reveal-based drill.
    """

    id: str
    title: str
    subtitle: str = ""
    track: Track = "foundations"
    order: int = 100
    tags: list[str] = Field(default_factory=list)
    estimated_minutes: int = 45
    body: str = ""  # verbatim markdown of the whole guide

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "track": self.track,
            "order": self.order,
            "tags": self.tags,
            "estimated_minutes": self.estimated_minutes,
            "char_count": len(self.body),
        }


class MemoryCard(BaseModel):
    """One atomic thing to memorize from a Masterclass: a single line of code,
    a code block, a concept, or a reusable pattern. Rich enough to drill by
    reading (front -> reveal), by fill-in-the-blank, and by writing from memory.
    """

    id: str
    masterclass_id: str
    section: str  # which Beat/Part this belongs to
    order: int = 0
    kind: Literal["concept", "line", "block", "pattern"] = "line"
    front: str  # the recall prompt ("write the line that declares OUR namespace")
    code: str = ""  # the exact line/snippet = the answer for write-it tests
    language: Language = "text"
    explain: str = ""  # what it does / why it's there
    mental_model: str = ""  # the analogy that makes it stick
    memory_hook: str = ""  # a mnemonic / trick to recall it
    blank: str = ""  # fill-in-the-blank template using ____ for each gap
    answers: list[str] = Field(default_factory=list)  # ordered fill-in answers
