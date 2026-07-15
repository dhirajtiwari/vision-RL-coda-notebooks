"""Curriculum data models for the Study Lab."""

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
]


class LineAnnotation(BaseModel):
    line: int = Field(..., ge=1, description="1-based line number in beat code")
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
    template: str  # use {{id}} placeholders
    blanks: list[BlankSpec] = Field(default_factory=list)


class ConceptCard(BaseModel):
    term: str
    definition: str
    analogy: str = ""


class QuizItem(BaseModel):
    q: str
    a: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class CodeBeat(BaseModel):
    id: str
    title: str
    language: Language = "python"
    narrative: str = ""
    code: str = ""
    annotations: list[LineAnnotation] = Field(default_factory=list)
    line_quiz: list[LineQuizItem] = Field(default_factory=list)
    fill_blanks: FillBlanks | None = None


class StudyModule(BaseModel):
    id: str
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    story: str = ""
    one_liner: str = ""
    change_table: list[dict[str, str]] = Field(default_factory=list)
    beats: list[CodeBeat] = Field(default_factory=list)
    concepts: list[ConceptCard] = Field(default_factory=list)
    self_quiz: list[QuizItem] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    final_boss: list[str] = Field(default_factory=list)
    source: str = "seed"  # seed | notebook | upload
    order: int = 100
    estimated_minutes: int = 30

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "source": self.source,
            "order": self.order,
            "estimated_minutes": self.estimated_minutes,
            "beat_count": len(self.beats),
            "concept_count": len(self.concepts),
            "quiz_count": len(self.self_quiz),
            "line_quiz_count": sum(len(b.line_quiz) for b in self.beats),
        }


class GenerateRequest(BaseModel):
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    text: str = ""
    filename: str = "upload.md"


class ProgressPayload(BaseModel):
    module_id: str
    mode: str
    score: float | None = None
    completed_beat_ids: list[str] = Field(default_factory=list)
    notes: str = ""
