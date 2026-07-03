"""
Cost budget + circuit breaker (kickoff prompt §F, handbook ch06).

Tracks accumulated LLM spend within a rolling UTC day and trips a circuit breaker
when the ceiling is hit, so a runaway loop cannot rack up unbounded cost. In-memory
(single-node demo); back with a shared store for multi-replica deployments.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime


class BudgetExceeded(Exception):
    """Raised when the daily LLM cost ceiling is reached (circuit open)."""


class DailyCostBudget:
    def __init__(self, *, ceiling_usd: float) -> None:
        self.ceiling_usd = ceiling_usd
        self._spent = 0.0
        self._day = self._today()
        self._lock = threading.Lock()

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _roll(self) -> None:
        today = self._today()
        if today != self._day:
            self._day = today
            self._spent = 0.0

    def check(self) -> None:
        """Raise BudgetExceeded if the circuit is open. Call BEFORE a spend."""
        if self.ceiling_usd <= 0:
            return
        with self._lock:
            self._roll()
            if self._spent >= self.ceiling_usd:
                raise BudgetExceeded(f"daily LLM budget ${self.ceiling_usd:.2f} reached (spent ${self._spent:.2f})")

    def record(self, cost_usd: float) -> None:
        """Record realised spend AFTER a call."""
        with self._lock:
            self._roll()
            self._spent += max(0.0, cost_usd)

    @property
    def spent_usd(self) -> float:
        with self._lock:
            self._roll()
            return self._spent
