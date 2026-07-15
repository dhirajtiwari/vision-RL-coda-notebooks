"""Study Lab API — modular interview memorize / write / quiz platform."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from study.generator import generate_from_bytes, generate_module_from_text
from study.models import ProgressPayload
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


@router.get("/health")
def study_health() -> dict:
    ensure_seeded()
    return {"status": "ok", "modules": len(list_modules())}


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
        given = (body.answers.get(blank.id) or "").strip()
        exp = blank.answer.strip()
        ok = given.lower() == exp.lower()
        if ok:
            correct += 1
        results.append(
            {
                "id": blank.id,
                "ok": ok,
                "expected": exp,
                "given": given,
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
    from study.seed_curriculum import write_all_seeds

    ids = write_all_seeds()
    return {"seeded": ids}
