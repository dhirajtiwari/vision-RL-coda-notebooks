"""
In-process rate limiter (kickoff prompt §E/§F).

A dependency-free sliding-window limiter keyed by client identity (admin token,
customer id, or source IP). Suitable for the single-node Mac-mini demo. For a
multi-replica deployment, back this with Redis (see docs/runbooks/cost-spike.md).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Fixed-capacity sliding window over ``window_seconds``."""

    def __init__(self, *, max_per_window: int = 60, window_seconds: float = 60.0) -> None:
        self.max_per_window = max_per_window
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """Return True if the request is within budget; records the hit."""
        if self.max_per_window <= 0:  # disabled
            return True
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_per_window:
                return False
            bucket.append(now)
            return True

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest hit in the window expires."""
        with self._lock:
            bucket = self._hits.get(key)
            if not bucket:
                return 0
            return max(0, int(self.window_seconds - (time.monotonic() - bucket[0])))
