"""
Read-path cache for diagnose results (enterprise hot-path latency).

Key design (privacy + correctness):
  - Key = hash(tenant, product_id, asset_id, normalized_message, catalog_version)
  - Short TTL (default 90s) — free text must not live forever in Redis
  - Invalidated when named caches cleared after graph promote
  - Optional: disable via settings.enable_diagnose_cache=false

Not a substitute for Neo4j indexes — accelerates *repeat identical* diagnose requests
(agent retries, UI double-submit, load tests).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from config.settings import settings
from runtime.cache import get_named_cache


def catalog_version() -> str:
    """Fingerprint of knowledge catalog files so promote busts diagnose cache."""
    parts: list[str] = []
    for path in (settings.enterprise_catalog_file, settings.data_file):
        p = Path(path)
        if p.exists():
            st = p.stat()
            parts.append(f"{p.name}:{st.st_mtime_ns}:{st.st_size}")
        else:
            parts.append(f"{p.name}:missing")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _normalize_message(message: str) -> str:
    text = (message or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def diagnose_cache_key(
    message: str,
    *,
    product_id: str | None = None,
    asset_id: str | None = None,
    tenant_id: str | None = None,
) -> str:
    tenant = tenant_id or settings.default_tenant_id
    raw = "|".join(
        [
            tenant,
            product_id or "",
            asset_id or "",
            _normalize_message(message),
            catalog_version(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_diagnose_cache():
    return get_named_cache(
        "diagnose_results",
        ttl_seconds=float(settings.cache_ttl_diagnose_seconds),
        maxsize=int(settings.cache_maxsize_diagnose),
    )


def cache_get_diagnosis(key: str) -> dict[str, Any] | None:
    if not settings.enable_diagnose_cache:
        return None
    val = get_diagnose_cache().get(key)
    return val if isinstance(val, dict) else None


def cache_set_diagnosis(key: str, payload: dict[str, Any]) -> None:
    if not settings.enable_diagnose_cache:
        return
    # Store a plain dict so Redis pickle / memory paths stay simple
    get_diagnose_cache().set(key, payload)
