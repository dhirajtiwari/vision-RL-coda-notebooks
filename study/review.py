"""Spaced-repetition + progress engine for the Study Lab.

Implements the **SM-2 algorithm** (P. A. Wozniak, SuperMemo 1988 — the basis of
Anki) so items you almost forget come back at exactly the right time. This is the
single biggest lever for durable memory: without scheduling you re-study what you
already know and forget what you don't.

State is per "client" (a browser/user key) under ``data/study_review/``. Each
reviewable item (a flashcard id, or ``beat:<module>:<beat>``) tracks:

* ``ef``       — ease factor (how easy the item is), starts 2.5, floor 1.3
* ``interval`` — days until next review
* ``reps``     — successful reps in a row
* ``due``      — ISO date the item is next due
* ``lapses``   — times you failed it

UI grade buttons map to SM-2 quality: Again=1, Hard=3, Good=4, Easy=5.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REVIEW_DIR = ROOT / "data" / "study_review"

EF_START = 2.5
EF_FLOOR = 1.3

# UI button -> SM-2 quality (0..5)
QUALITY = {"again": 1, "hard": 3, "good": 4, "easy": 5}


def _today() -> date:
    return datetime.now().date()


def _safe(client_key: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (client_key or "local"))[:64]


def _path(client_key: str) -> Path:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    return REVIEW_DIR / f"{_safe(client_key)}.json"


def _load(client_key: str) -> dict[str, Any]:
    p = _path(client_key)
    if not p.exists():
        return {"items": {}, "history": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("items", {})
        data.setdefault("history", {})
        return data
    except Exception:
        return {"items": {}, "history": {}}


def _save(client_key: str, data: dict[str, Any]) -> None:
    _path(client_key).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _sm2(item: dict[str, Any], quality: int) -> dict[str, Any]:
    """Apply one SM-2 update and return the new item state."""
    ef = float(item.get("ef", EF_START))
    reps = int(item.get("reps", 0))
    interval = int(item.get("interval", 0))
    lapses = int(item.get("lapses", 0))

    if quality < 3:
        # Lapse: reset the streak, see it again tomorrow.
        reps = 0
        interval = 1
        lapses += 1
    else:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = round(interval * ef)
        # EF update (clamped at the 1.3 floor).
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ef = max(EF_FLOOR, ef)

    due = _today() + timedelta(days=max(interval, 1))
    return {
        "ef": round(ef, 3),
        "reps": reps,
        "interval": interval,
        "lapses": lapses,
        "due": due.isoformat(),
        "last": _today().isoformat(),
        "last_quality": quality,
    }


def grade(client_key: str, item_key: str, quality_label: str) -> dict[str, Any]:
    """Record a review outcome and schedule the next one.

    ``quality_label`` is one of again|hard|good|easy.
    """
    q = QUALITY.get((quality_label or "").lower())
    if q is None:
        raise ValueError(f"invalid quality '{quality_label}' (again|hard|good|easy)")
    data = _load(client_key)
    item = data["items"].get(item_key, {})
    new_state = _sm2(item, q)
    data["items"][item_key] = new_state
    # Streak history: count reviews per day.
    today = _today().isoformat()
    data["history"][today] = int(data["history"].get(today, 0)) + 1
    _save(client_key, data)
    return {"item_key": item_key, **new_state}


def due_items(client_key: str, candidate_ids: list[str], *, limit: int = 40) -> dict[str, Any]:
    """Split candidate item ids into due / new / later for today's session.

    * due   — scheduled on or before today (review these)
    * new   — never seen (learn these; capped so a session stays finite)
    * later — scheduled in the future (not shown today)
    """
    data = _load(client_key)
    items = data["items"]
    today = _today().isoformat()
    due, new, later = [], [], []
    for cid in candidate_ids:
        st = items.get(cid)
        if st is None:
            new.append(cid)
        elif st.get("due", today) <= today:
            due.append(cid)
        else:
            later.append(cid)
    session = due + new[: max(0, limit - len(due))]
    return {
        "due": due,
        "new": new,
        "later": later,
        "session": session[:limit],
        "counts": {"due": len(due), "new": len(new), "later": len(later)},
    }


def _streak(history: dict[str, Any]) -> int:
    """Consecutive days (ending today or yesterday) with >=1 review."""
    if not history:
        return 0
    days = {d for d, n in history.items() if int(n) > 0}
    streak = 0
    cursor = _today()
    # Allow the streak to still count if you haven't studied yet *today*.
    if cursor.isoformat() not in days:
        cursor = cursor - timedelta(days=1)
    while cursor.isoformat() in days:
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


def dashboard(client_key: str, item_to_track: dict[str, str]) -> dict[str, Any]:
    """Progress overview: streak, today's counts, and mastery per track.

    ``item_to_track`` maps every reviewable item id -> its track/module id so we
    can compute a mastery % (share of items with a healthy interval >= 7 days).
    """
    data = _load(client_key)
    items = data["items"]
    today = _today().isoformat()

    reviewed_today = int(data["history"].get(today, 0))
    due_today = sum(1 for st in items.values() if st.get("due", today) <= today)

    # Mastery per track: fraction of that track's items with interval >= 7 days.
    by_track_total: dict[str, int] = {}
    by_track_strong: dict[str, int] = {}
    for item_id, track in item_to_track.items():
        by_track_total[track] = by_track_total.get(track, 0) + 1
        st = items.get(item_id)
        if st and int(st.get("interval", 0)) >= 7:
            by_track_strong[track] = by_track_strong.get(track, 0) + 1

    mastery = {
        track: {
            "strong": by_track_strong.get(track, 0),
            "total": total,
            "pct": round(100 * by_track_strong.get(track, 0) / total) if total else 0,
        }
        for track, total in by_track_total.items()
    }
    overall_total = sum(by_track_total.values())
    overall_strong = sum(by_track_strong.values())

    # Weak spots: items failed most (highest lapses), still not strong.
    weak = sorted(
        (
            {"item_key": k, "lapses": int(v.get("lapses", 0)), "interval": int(v.get("interval", 0))}
            for k, v in items.items()
            if int(v.get("lapses", 0)) > 0 and int(v.get("interval", 0)) < 7
        ),
        key=lambda x: (-x["lapses"], x["interval"]),
    )[:10]

    return {
        "streak": _streak(data["history"]),
        "reviewed_today": reviewed_today,
        "due_today": due_today,
        "seen": len(items),
        "mastery_overall_pct": round(100 * overall_strong / overall_total) if overall_total else 0,
        "mastery_by_track": mastery,
        "weak_spots": weak,
        "history": data["history"],
    }
