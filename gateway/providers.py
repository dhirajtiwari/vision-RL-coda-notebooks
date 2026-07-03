"""
Provider adapters behind one interface (kickoff prompt §G).

Each adapter exposes ``complete(prompt, *, model, max_tokens) -> Completion``.
Adapters lazily import their SDKs so the app runs without them installed while
the LLM path is inactive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, *, model: str, max_tokens: int) -> Completion: ...


class OpenAIProvider:
    """OpenAI API adapter (inactive unless OPENAI_API_KEY + LLM_ENABLED set)."""

    name = "openai"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def complete(self, prompt: str, *, model: str, max_tokens: int) -> Completion:
        from openai import OpenAI  # lazy import

        client = OpenAI(api_key=self._api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        usage = resp.usage
        return Completion(
            text=resp.choices[0].message.content or "",
            input_tokens=getattr(usage, "prompt_tokens", 0),
            output_tokens=getattr(usage, "completion_tokens", 0),
            provider=self.name,
            model=model,
        )


class AzureFoundryProvider:
    """Azure AI Foundry / Azure OpenAI adapter (inactive by default)."""

    name = "azure_foundry"

    def __init__(self, api_key: str, endpoint: str, api_version: str) -> None:
        self._api_key = api_key
        self._endpoint = endpoint
        self._api_version = api_version

    def complete(self, prompt: str, *, model: str, max_tokens: int) -> Completion:
        from openai import AzureOpenAI  # lazy import (azure uses openai sdk)

        client = AzureOpenAI(
            api_key=self._api_key,
            azure_endpoint=self._endpoint,
            api_version=self._api_version,
        )
        resp = client.chat.completions.create(
            model=model,  # Azure deployment name
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        usage = resp.usage
        return Completion(
            text=resp.choices[0].message.content or "",
            input_tokens=getattr(usage, "prompt_tokens", 0),
            output_tokens=getattr(usage, "completion_tokens", 0),
            provider=self.name,
            model=model,
        )
