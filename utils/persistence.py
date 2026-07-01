"""
SQLite operational store — escalations, CCaaS cases, warranty claim submissions.

Replaces append-only JSON files for durability, queryability, and concurrent access.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from config.settings import settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OperationalStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._migrate_legacy_json()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS escalations (
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    status TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    diagnosis_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ccaas_cases (
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    status TEXT NOT NULL,
                    customer_id TEXT,
                    asset_id TEXT,
                    user_message TEXT,
                    escalation_reason TEXT,
                    source_system TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS claim_submissions (
                    claim_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status);
                CREATE INDEX IF NOT EXISTS idx_ccaas_status ON ccaas_cases(status);
                CREATE INDEX IF NOT EXISTS idx_claims_status ON claim_submissions(status);
                """
            )

    def _migrate_legacy_json(self) -> None:
        """One-time import from legacy JSON files if DB tables are empty."""
        if self.db_path.resolve() != settings.database_path.resolve():
            return
        with self._conn() as conn:
            if conn.execute("SELECT COUNT(*) FROM escalations").fetchone()[0] == 0:
                self._import_json_list(conn, settings.escalations_file, self._insert_escalation_row)
            if conn.execute("SELECT COUNT(*) FROM ccaas_cases").fetchone()[0] == 0:
                self._import_json_list(conn, settings.cases_file, self._insert_ccaas_row)
            claims_path = settings.enterprise_sources_dir / "claims_submissions.json"
            if conn.execute("SELECT COUNT(*) FROM claim_submissions").fetchone()[0] == 0:
                self._import_json_list(conn, claims_path, self._insert_claim_row)

    def _import_json_list(
        self,
        conn: sqlite3.Connection,
        path: Path,
        inserter,
    ) -> None:
        if not path.exists():
            return
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if not isinstance(rows, list):
            return
        for row in rows:
            inserter(conn, row)

    def _insert_escalation_row(self, conn: sqlite3.Connection, row: dict[str, Any]) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO escalations
            (case_id, created_at, updated_at, status, user_message, diagnosis_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("case_id") or str(uuid.uuid4())[:8],
                row.get("created_at") or _utc_now(),
                row.get("updated_at"),
                row.get("status", "open"),
                row.get("user_message", ""),
                json.dumps(row.get("diagnosis") or {}),
            ),
        )

    def _insert_ccaas_row(self, conn: sqlite3.Connection, row: dict[str, Any]) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO ccaas_cases
            (case_id, created_at, updated_at, status, customer_id, asset_id,
             user_message, escalation_reason, source_system, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("case_id") or f"CASE-{uuid.uuid4().hex[:8].upper()}",
                row.get("created_at") or _utc_now(),
                row.get("updated_at"),
                row.get("status", "open"),
                row.get("customer_id"),
                row.get("asset_id"),
                row.get("user_message"),
                row.get("escalation_reason", ""),
                row.get("source_system", "DiagnosticsPlatform"),
                json.dumps(row),
            ),
        )

    def _insert_claim_row(self, conn: sqlite3.Connection, row: dict[str, Any]) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO claim_submissions
            (claim_id, created_at, updated_at, status, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row.get("claim_id") or f"CLM-SUB-{uuid.uuid4().hex[:8].upper()}",
                row.get("submitted_at") or row.get("created_at") or _utc_now(),
                row.get("updated_at"),
                row.get("status", "submitted"),
                json.dumps(row),
            ),
        )

    # ── Escalations ───────────────────────────────────────────────────────────

    def count_escalations(self, *, status: str | None = None) -> int:
        with self._conn() as conn:
            if status:
                row = conn.execute(
                    "SELECT COUNT(*) FROM escalations WHERE status = ?",
                    (status,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) FROM escalations").fetchone()
        return int(row[0]) if row else 0

    def list_escalations(self, *, status: str | None = None) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM escalations WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM escalations ORDER BY created_at DESC"
                ).fetchall()
        return [self._escalation_from_row(r) for r in rows]

    def save_escalation(
        self,
        user_message: str,
        diagnosis_payload: dict[str, Any],
        status: str = "open",
    ) -> dict[str, Any]:
        case = {
            "case_id": str(uuid.uuid4())[:8],
            "created_at": _utc_now(),
            "status": status,
            "user_message": user_message,
            "diagnosis": diagnosis_payload,
        }
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO escalations
                (case_id, created_at, status, user_message, diagnosis_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    case["case_id"],
                    case["created_at"],
                    status,
                    user_message,
                    json.dumps(diagnosis_payload),
                ),
            )
        return case

    def update_escalation_status(self, case_id: str, status: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                """
                UPDATE escalations SET status = ?, updated_at = ?
                WHERE case_id = ?
                """,
                (status, _utc_now(), case_id),
            )
            return cur.rowcount > 0

    def _escalation_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "case_id": row["case_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "status": row["status"],
            "user_message": row["user_message"],
            "diagnosis": json.loads(row["diagnosis_json"]),
        }

    # ── CCaaS cases ───────────────────────────────────────────────────────────

    def list_cases(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM ccaas_cases ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def save_case(self, case: dict[str, Any]) -> dict[str, Any]:
        if not case.get("case_id"):
            case["case_id"] = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        if not case.get("created_at"):
            case["created_at"] = _utc_now()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO ccaas_cases
                (case_id, created_at, status, customer_id, asset_id, user_message,
                 escalation_reason, source_system, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case["case_id"],
                    case["created_at"],
                    case.get("status", "open"),
                    case.get("customer_id"),
                    case.get("asset_id"),
                    case.get("user_message"),
                    case.get("escalation_reason", ""),
                    case.get("source_system", "DiagnosticsPlatform"),
                    json.dumps(case),
                ),
            )
        return case

    # ── Claims ────────────────────────────────────────────────────────────────

    def list_claims(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM claim_submissions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def get_claim(self, claim_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT payload_json FROM claim_submissions WHERE claim_id = ?",
                (claim_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def save_claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO claim_submissions
                (claim_id, created_at, status, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    claim["claim_id"],
                    claim.get("submitted_at") or claim.get("created_at") or _utc_now(),
                    claim.get("status", "submitted"),
                    json.dumps(claim),
                ),
            )
        return claim

    def update_claim(self, claim_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        claim = self.get_claim(claim_id)
        if not claim:
            return None
        claim.update(updates)
        claim["updated_at"] = _utc_now()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE claim_submissions
                SET status = ?, updated_at = ?, payload_json = ?
                WHERE claim_id = ?
                """,
                (
                    claim.get("status", "submitted"),
                    claim["updated_at"],
                    json.dumps(claim),
                    claim_id,
                ),
            )
        return claim


_store: OperationalStore | None = None


def get_store() -> OperationalStore:
    global _store
    if _store is None:
        _store = OperationalStore()
    return _store