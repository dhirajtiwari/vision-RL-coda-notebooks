"""Filesystem store for study modules under data/study_modules/."""

from __future__ import annotations

import json
from pathlib import Path

from study.models import StudyModule

ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT / "data" / "study_modules"
PROGRESS_DIR = ROOT / "data" / "study_progress"


def modules_dir() -> Path:
    MODULES_DIR.mkdir(parents=True, exist_ok=True)
    return MODULES_DIR


def progress_dir() -> Path:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    return PROGRESS_DIR


def list_modules() -> list[dict]:
    ensure_seeded()
    items: list[StudyModule] = []
    for path in sorted(modules_dir().glob("*.json")):
        try:
            items.append(StudyModule.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    items.sort(key=lambda m: (m.order, m.title.lower()))
    return [m.summary() for m in items]


def load_module(module_id: str) -> StudyModule:
    ensure_seeded()
    path = modules_dir() / f"{module_id}.json"
    if not path.exists():
        # try fuzzy
        for p in modules_dir().glob("*.json"):
            if p.stem == module_id or module_id in p.stem:
                path = p
                break
    if not path.exists():
        raise FileNotFoundError(module_id)
    return StudyModule.model_validate_json(path.read_text(encoding="utf-8"))


def save_module(module: StudyModule) -> Path:
    path = modules_dir() / f"{module.id}.json"
    path.write_text(module.model_dump_json(indent=2), encoding="utf-8")
    return path


def delete_module(module_id: str) -> bool:
    path = modules_dir() / f"{module_id}.json"
    if not path.exists():
        return False
    # only allow deleting non-seed uploads by convention — still allow all
    path.unlink()
    return True


def save_progress(client_key: str, payload: dict) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in client_key)[:64]
    path = progress_dir() / f"{safe}.json"
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    modules = existing.setdefault("modules", {})
    mid = payload.get("module_id") or "unknown"
    prev = modules.get(mid, {})
    prev.update(payload)
    modules[mid] = prev
    existing["modules"] = modules
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return path


def load_progress(client_key: str) -> dict:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in client_key)[:64]
    path = progress_dir() / f"{safe}.json"
    if not path.exists():
        return {"modules": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"modules": {}}


_SEED_DONE = False


def ensure_seeded() -> None:
    """Write seed curriculum once if directory empty or missing core module."""
    global _SEED_DONE
    if _SEED_DONE:
        return
    d = modules_dir()
    core = d / "01-rdf-owl-tbox-abox.json"
    if not core.exists():
        from study.seed_curriculum import write_all_seeds

        write_all_seeds()
    _SEED_DONE = True
