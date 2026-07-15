"""Study Lab API — modular interview memorize / write / quiz platform."""

from __future__ import annotations

import re

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from study.flashcards_deck import list_flashcards, load_deck, write_deck
from study.generator import generate_from_bytes, generate_module_from_text
from study.masterclass_cards import cards_for as mc_cards_for
from study.masterclass_cards import sections_for as mc_sections_for
from study.masterclasses import get_masterclass, list_masterclasses
from study.models import ProgressPayload
from study.references import library as reading_library
from study.review import dashboard as review_dashboard
from study.review import due_items
from study.review import grade as review_grade
from study.store import (
    delete_module,
    ensure_seeded,
    list_modules,
    load_module,
    load_progress,
    save_module,
    save_progress,
)

router = APIRouter(prefix="/study", tags=["study-lab"])


class GenerateBody(BaseModel):
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    text: str = ""
    filename: str = "paste.md"


class GradeFillBody(BaseModel):
    module_id: str
    beat_id: str
    answers: dict[str, str] = Field(default_factory=dict)


class GradeLineBody(BaseModel):
    module_id: str
    beat_id: str
    line: int
    choice: str


class ReviewGradeBody(BaseModel):
    client_key: str = "local"
    item_key: str
    quality: str  # again | hard | good | easy


@router.get("/health")
def study_health() -> dict:
    ensure_seeded()
    write_deck()
    return {
        "status": "ok",
        "modules": len(list_modules()),
        "flashcards": len(load_deck()),
    }


@router.get("/flashcards")
def get_flashcards(
    track: str | None = None,
    tag: str | None = None,
    kind: str | None = None,
    q: str | None = None,
) -> dict:
    """Full curriculum flashcard deck with 5W+H + authoritative sources."""
    ensure_seeded()
    write_deck()
    cards = list_flashcards(track=track, tag=tag, kind=kind, q=q)
    tracks = sorted({c.track for c in load_deck()})
    tags = sorted({t for c in load_deck() for t in c.tags})
    kinds = sorted({c.kind for c in load_deck()})
    return {
        "count": len(cards),
        "filters": {"tracks": tracks, "tags": tags, "kinds": kinds},
        "cards": [c.model_dump() for c in cards],
    }


@router.get("/flashcards/{card_id}")
def get_flashcard(card_id: str) -> dict:
    ensure_seeded()
    write_deck()
    for c in load_deck():
        if c.id == card_id:
            return c.model_dump()
    raise HTTPException(status_code=404, detail=f"flashcard not found: {card_id}")


@router.get("/review/due")
def review_due(client_key: str = "local", limit: int = 40) -> dict:
    """Today's spaced-repetition session: due cards first, then a capped set of
    new cards. This is what a learner should open every day."""
    ensure_seeded()
    write_deck()
    cards = load_deck()
    plan = due_items(client_key, [c.id for c in cards], limit=limit)
    by_id = {c.id: c for c in cards}
    session = [by_id[i].model_dump() for i in plan["session"] if i in by_id]
    return {**plan, "cards": session}


@router.post("/review/grade")
def review_grade_ep(body: ReviewGradeBody) -> dict:
    """Record a recall attempt (again|hard|good|easy) and schedule the next review (SM-2)."""
    try:
        return review_grade(body.client_key, body.item_key, body.quality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/dashboard")
def study_dashboard(client_key: str = "local") -> dict:
    """Streak, due-today count, and mastery % per track — the motivation layer."""
    ensure_seeded()
    write_deck()
    cards = load_deck()
    item_to_track = {c.id: c.track for c in cards}
    return review_dashboard(client_key, item_to_track)


@router.get("/modules")
def get_modules() -> dict:
    return {"modules": list_modules()}


@router.get("/modules/{module_id}")
def get_module(module_id: str) -> dict:
    try:
        m = load_module(module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"module not found: {module_id}") from None
    return m.model_dump()


@router.post("/modules/generate")
def generate_module(body: GenerateBody) -> dict:
    try:
        mod = generate_module_from_text(
            body.text,
            title=body.title,
            tags=body.tags,
            source="upload",
            filename=body.filename or "paste.md",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    # avoid clobbering seed ids
    if mod.id.startswith(("01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-")):
        mod.id = f"u-{mod.id}"
    path = save_module(mod)
    return {"module": mod.summary(), "path": str(path)}


@router.post("/modules/upload")
async def upload_module(
    file: UploadFile = File(...),
    title: str = Form(""),
    tags: str = Form(""),
) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file")
    if len(data) > 2_000_000:
        raise HTTPException(status_code=400, detail="file too large (max 2MB)")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        mod = generate_from_bytes(
            file.filename or "upload.md",
            data,
            title=title,
            tags=tag_list,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"could not parse upload: {e}") from e
    if mod.id.startswith(("01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-")):
        mod.id = f"u-{mod.id}"
    path = save_module(mod)
    return {"module": mod.summary(), "path": str(path)}


@router.delete("/modules/{module_id}")
def remove_module(module_id: str) -> dict:
    if module_id.startswith(("01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-")):
        raise HTTPException(status_code=400, detail="refusing to delete seed module")
    ok = delete_module(module_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": module_id}


def _normalize_blank(text: str) -> str:
    """Structure-aware normalisation for fill-in answers: lowercase, collapse
    whitespace, and drop surrounding quotes/backticks/parentheses/trailing
    punctuation so `Rdf:type`, `rdf:type ;` and '"rdf:type"' all match."""
    t = (text or "").strip().lower()
    t = t.strip("`'\"()[]{} ;,.")
    t = re.sub(r"\s+", " ", t)
    return t


def _blank_matches(given: str, expected: str) -> bool:
    """A blank is correct if the normalised strings match, or (for multi-token
    answers) if the token *sets* match — order- and spacing-insensitive."""
    g, e = _normalize_blank(given), _normalize_blank(expected)
    if not e:
        return not g
    if g == e:
        return True
    g_tokens, e_tokens = set(g.split()), set(e.split())
    return len(e_tokens) > 1 and g_tokens == e_tokens


@router.get("/library")
def study_library() -> dict:
    """All curated further-reading sources (standards, papers, docs, books)
    grouped by module — the 'go deeper' library."""
    return {"library": reading_library()}


@router.get("/masterclasses")
def study_masterclasses() -> dict:
    """List the verbatim 'Master This Code' guides to memorize word-for-word."""
    return {"masterclasses": list_masterclasses()}


@router.get("/masterclasses/{mc_id}")
def study_masterclass(mc_id: str) -> dict:
    """Full verbatim body of one masterclass guide."""
    mc = get_masterclass(mc_id)
    if mc is None:
        raise HTTPException(status_code=404, detail=f"masterclass not found: {mc_id}")
    return {**mc.model_dump(), "char_count": len(mc.body)}


@router.get("/masterclasses/{mc_id}/cards")
def study_masterclass_cards(mc_id: str) -> dict:
    """Line-by-line + concept memory cards for a masterclass, grouped for drills
    (read, fill-in-the-blank, write-a-snippet, write-a-section)."""
    cards = mc_cards_for(mc_id)
    if not cards:
        raise HTTPException(status_code=404, detail=f"no cards for masterclass: {mc_id}")
    return {
        "masterclass_id": mc_id,
        "cards": [c.model_dump() for c in cards],
        "sections": mc_sections_for(mc_id),
        "counts": {
            "total": len(cards),
            "blanks": sum(1 for c in cards if c.blank),
            "writable": sum(1 for c in cards if c.code),
        },
    }


@router.post("/grade/fill-blanks")
def grade_fill(body: GradeFillBody) -> dict:
    try:
        mod = load_module(body.module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="module not found") from None
    beat = next((b for b in mod.beats if b.id == body.beat_id), None)
    if not beat or not beat.fill_blanks:
        raise HTTPException(status_code=404, detail="beat/fill_blanks not found")
    results = []
    correct = 0
    for blank in beat.fill_blanks.blanks:
        given = body.answers.get(blank.id) or ""
        ok = _blank_matches(given, blank.answer)
        if ok:
            correct += 1
        results.append(
            {
                "id": blank.id,
                "ok": ok,
                "expected": blank.answer.strip(),
                "given": given.strip(),
                "hint": blank.hint,
            }
        )
    total = max(len(results), 1)
    return {
        "score": correct / total,
        "correct": correct,
        "total": total,
        "results": results,
    }


@router.post("/grade/line-quiz")
def grade_line(body: GradeLineBody) -> dict:
    try:
        mod = load_module(body.module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="module not found") from None
    beat = next((b for b in mod.beats if b.id == body.beat_id), None)
    if not beat:
        raise HTTPException(status_code=404, detail="beat not found")
    item = next((q for q in beat.line_quiz if q.line == body.line), None)
    if not item:
        raise HTTPException(status_code=404, detail="line quiz not found")
    ok = body.choice.strip() == item.answer.strip() or body.choice.strip().lower() == item.answer.strip().lower()
    return {
        "ok": ok,
        "expected": item.answer,
        "why": item.why,
        "prompt": item.prompt,
    }


@router.get("/progress/{client_key}")
def get_progress(client_key: str) -> dict:
    return load_progress(client_key)


@router.post("/progress")
def post_progress(body: ProgressPayload, client_key: str = "local") -> dict:
    path = save_progress(client_key, body.model_dump())
    return {"saved": True, "path": str(path)}


@router.post("/reseed")
def reseed() -> dict:
    """Replace seed modules + flashcard deck (keeps u-* uploads)."""
    from study.seed_curriculum import write_all_seeds

    ids = write_all_seeds(wipe_old=True)
    path = write_deck()
    return {
        "seeded": ids,
        "grounded": True,
        "flashcards": len(load_deck()),
        "flashcards_path": str(path),
    }
