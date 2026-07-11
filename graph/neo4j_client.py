"""
Neo4j Bolt clients for production and staging graphs.

Enterprise pattern: promote catalog into a **staging** Neo4j first, smoke there,
then promote to **production** Neo4j used by /diagnose.

Use ``neo4j_env("staging")`` context manager so existing code that calls
``get_driver()`` routes to the correct instance without rewriting every query.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from contextvars import ContextVar
from typing import Literal

from neo4j import Driver, GraphDatabase

from config.settings import settings

Neo4jEnv = Literal["production", "staging"]

_active_env: ContextVar[Neo4jEnv] = ContextVar("neo4j_env", default="production")
_drivers: dict[str, Driver] = {}


def current_neo4j_env() -> Neo4jEnv:
    return _active_env.get()


@contextmanager
def neo4j_env(env: Neo4jEnv) -> Iterator[None]:
    """Temporarily route ``get_driver()`` to staging or production."""
    if env not in ("production", "staging"):
        raise ValueError(f"invalid neo4j env: {env}")
    token = _active_env.set(env)
    try:
        yield
    finally:
        _active_env.reset(token)


def _uri_for(env: Neo4jEnv) -> str:
    if env == "staging":
        return settings.neo4j_staging_uri or settings.neo4j_uri
    return settings.neo4j_uri


def _password_for(env: Neo4jEnv) -> str:
    if env == "staging" and getattr(settings, "neo4j_staging_password", None):
        return settings.neo4j_staging_password or settings.neo4j_password
    return settings.neo4j_password


def get_driver(env: Neo4jEnv | None = None) -> Driver:
    """Shared Bolt driver for the active (or explicit) env — pooled, thread-safe."""
    target: Neo4jEnv = env or _active_env.get()
    if target not in _drivers:
        _drivers[target] = GraphDatabase.driver(
            _uri_for(target),
            auth=(settings.neo4j_user, _password_for(target)),
            max_connection_pool_size=settings.neo4j_max_connection_pool_size,
            connection_acquisition_timeout=settings.neo4j_connection_acquisition_timeout,
        )
    return _drivers[target]


def close_driver(env: Neo4jEnv | None = None) -> None:
    """Close one env driver, or all if env is None."""
    global _drivers
    if env is None:
        for key, driver in list(_drivers.items()):
            with suppress(Exception):
                driver.close()
            _drivers.pop(key, None)
        return
    driver = _drivers.pop(env, None)
    if driver is not None:
        with suppress(Exception):
            driver.close()


def verify_connection(env: Neo4jEnv | None = None) -> bool:
    try:
        get_driver(env).verify_connectivity()
        return True
    except Exception:
        return False


def neo4j_health() -> dict:
    """Status for /health — both environments."""
    prod_ok = verify_connection("production")
    staging_uri = settings.neo4j_staging_uri or settings.neo4j_uri
    same = staging_uri == settings.neo4j_uri
    staging_ok = prod_ok if same else verify_connection("staging")
    return {
        "production": {
            "uri": settings.neo4j_uri,
            "connected": prod_ok,
        },
        "staging": {
            "uri": staging_uri,
            "connected": staging_ok,
            "same_as_production": same,
        },
        "active_env": current_neo4j_env(),
    }
