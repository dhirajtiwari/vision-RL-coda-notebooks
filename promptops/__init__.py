"""
PromptOps runtime loader (kickoff prompt §B, handbook ch02).

Loads versioned prompt artifacts from ``prompts/<id>/vN.yaml`` and exposes their
``content_hash`` so every request can emit ``prompt_id`` + ``version`` +
``content_hash`` for tracing (§H). Validates each file against
``prompts/_schema.json`` when ``jsonschema`` is installed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass(frozen=True)
class Prompt:
    id: str
    version: int
    system: str
    user_template: str
    content_hash: str
    model_alias: str | None
    raw: dict[str, Any]

    def render_user(self, **kwargs: Any) -> str:
        return self.user_template.format(**kwargs)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_prompt(prompt_id: str, version: int, *, validate: bool = True) -> Prompt:
    """Load ``prompts/<id>/v<version>.yaml`` and return a Prompt."""
    path = _PROMPTS_DIR / prompt_id / f"v{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no prompt artifact: {path}")
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pyyaml is required to load prompts") from exc

    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    if validate:
        _validate(data)

    system = data.get("system", "")
    user_template = data.get("user_template", "")
    return Prompt(
        id=data["id"],
        version=int(data["version"]),
        system=system,
        user_template=user_template,
        content_hash=_hash(system + "\x00" + user_template),
        model_alias=data.get("model_alias"),
        raw=data,
    )


def _validate(data: dict[str, Any]) -> None:
    schema_path = _PROMPTS_DIR / "_schema.json"
    if not schema_path.exists():
        return
    try:
        import json

        import jsonschema

        schema = json.loads(schema_path.read_text())
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        # jsonschema optional; skip validation gracefully.
        return
