"""Test-suite hygiene (P1 — hermetic CI; SDD `04-PLATFORM-CI` "Hermetic CI").

Several pipeline/ETL tests exercise the real control plane, which writes to
repo-tracked catalog files (`enterprise_knowledge_catalog.json`,
`enterprise_sources/pim_catalog.json`) and emits timestamped ``run-*.json``
artifacts. Left unguarded, ``pytest`` mutates those tracked fixtures — which both
dirties the working tree AND makes some tests flaky in isolation (a later test
reads a fixture an earlier test overwrote).

This autouse, session-scoped fixture **redirects the writable `settings` paths to
a seeded temporary directory**. Tests then read/write *copies*, so:

* the real repo files are never mutated (pristine working tree after `pytest`);
* order-dependent pipeline tests still work (the temp copies persist for the
  whole session);
* tests that read a committed fixture directly always see the correct, unmutated
  content.

No production code path is changed.
"""

from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
# Ensure the project root is importable when pytest is invoked as a bare
# `pytest` (e.g. the pre-push hook) rather than `python -m pytest`.
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import settings  # noqa: E402  (import after sys.path bootstrap)

_STAGING = _ROOT / "data" / "pipeline_staging"

# Settings attributes whose targets tests write to (repo-tracked or noisy).
# Each is redirected to a seeded copy under a per-session temp directory.
_REDIRECT_ATTRS = (
    "enterprise_catalog_file",  # enterprise_knowledge_catalog.json
    "provenance_manifest_file",  # provenance_manifest.json
    "enterprise_sources_dir",  # pim_catalog.json + connector fixtures
    "lineage_dir",  # pipeline_runs/ + etl_batches.jsonl
)


@pytest.fixture(scope="session", autouse=True)
def _sandbox_writable_data():
    tmp = Path(tempfile.mkdtemp(prefix="diag-tests-"))
    originals = {attr: getattr(settings, attr) for attr in _REDIRECT_ATTRS}

    for attr, original in originals.items():
        new_path = tmp / Path(original).name
        # Seed the sandbox from the real file/dir so ETL reads see the fixtures.
        if isinstance(original, Path) and original.exists():
            if original.is_dir():
                shutil.copytree(original, new_path, dirs_exist_ok=True)
            else:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, new_path)
        else:
            new_path.mkdir(parents=True, exist_ok=True)
        setattr(settings, attr, new_path)

    # Staging run outputs go under the real data dir (git-ignored); record what
    # exists so we only clean up what the suite creates.
    pre_runs = set(_STAGING.glob("run-*.json")) if _STAGING.exists() else set()

    try:
        yield
    finally:
        for attr, original in originals.items():
            setattr(settings, attr, original)
        shutil.rmtree(tmp, ignore_errors=True)
        if _STAGING.exists():
            for run_file in _STAGING.glob("run-*.json"):
                if run_file not in pre_runs:
                    with contextlib.suppress(OSError):
                        run_file.unlink()
