"""
Cost budget + circuit breaker (kickoff prompt §F, handbook ch06).

Tracks accumulated LLM spend within a rolling UTC day and trips a circuit breaker
when the ceiling is hit. Uses Redis when configured so multiple replicas share one
budget; otherwise in-process memory (single-node demo).
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("diagnostics.budget")


class BudgetExceeded(Exception):
    """Raised when the daily LLM cost ceiling is reached (circuit open)."""


class DailyCostBudget:
    def __init__(
        self,
        *,
        ceiling_usd: float,
        redis_client: Any | None = None,
        key_prefix: str = "diagnostics:budget:",
        prefer_redis: bool = True,
    ) -> None:
        self.ceiling_usd = ceiling_usd
        self._redis = redis_client
        self._prefer_redis = prefer_redis
        self._key_prefix = key_prefix
        self._spent = 0.0
        self._day = self._today()
        self._lock = threading.Lock()
        self.backend = "memory"

    @classmethod
    def from_settings(cls, app_settings: Any | None = None) -> DailyCostBudget:
        if app_settings is None:
            from config.settings import settings as app_settings

        from runtime.redis_client import get_redis_client, key_prefix

        client = get_redis_client() if getattr(app_settings, "redis_url", None) else None
        budget = cls(
            ceiling_usd=float(getattr(app_settings, "llm_cost_budget_usd_per_day", 5.0)),
            redis_client=client,
            key_prefix=key_prefix() + "budget:",
            prefer_redis=True,
        )
        budget.backend = "redis" if client is not None else "memory"
        return budget

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _client(self) -> Any | None:
        if not self._prefer_redis:
            return None
        if self._redis is not None:
            return self._redis
        from runtime.redis_client import get_redis_client

        return get_redis_client()

    def _rkey(self) -> str:
        return f"{self._key_prefix}day:{self._today()}"

    def _roll(self) -> None:
        today = self._today()
        if today != self._day:
            self._day = today
            self._spent = 0.0

    def check(self) -> None:
        """Raise BudgetExceeded if the circuit is open. Call BEFORE a spend."""
        if self.ceiling_usd <= 0:
            return
        client = self._client()
        if client is not None:
            try:
                spent = float(client.get(self._rkey()) or 0)
                self.backend = "redis"
                if spent >= self.ceiling_usd:
                    raise BudgetExceeded(f"daily LLM budget ${self.ceiling_usd:.2f} reached (spent ${spent:.2f})")
                return
            except BudgetExceeded:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("redis budget check failed, using memory: %s", exc)
        with self._lock:
            self._roll()
            self.backend = "memory"
            if self._spent >= self.ceiling_usd:
                raise BudgetExceeded(f"daily LLM budget ${self.ceiling_usd:.2f} reached (spent ${self._spent:.2f})")

    def record(self, cost_usd: float) -> None:
        """Record realised spend AFTER a call."""
        amount = max(0.0, cost_usd)
        client = self._client()
        if client is not None:
            try:
                rkey = self._rkey()
                client.incrbyfloat(rkey, amount)
                # Expire shortly after UTC day end (36h safety window).
                client.expire(rkey, 36 * 3600)
                self.backend = "redis"
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("redis budget record failed, using memory: %s", exc)
        with self._lock:
            self._roll()
            self.backend = "memory"
            self._spent += amount

    @property
    def spent_usd(self) -> float:
        client = self._client()
        if client is not None:
            try:
                return float(client.get(self._rkey()) or 0)
            except Exception:
                pass
        with self._lock:
            self._roll()
            return self._spent
