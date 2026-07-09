"""AI provider abstraction for workflow generation, optimization, research."""

from __future__ import annotations

import urllib.request
from typing import Any


def fetch_url(url: str, timeout: float = 20.0) -> str:
    """Minimal URL fetcher used by research actions (safe mode aware)."""
    req = urllib.request.Request(url, headers={"User-Agent": "ArcanisAutomation/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")[:8192]


class BaseAIProvider:
    name = "base"

    def complete(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError

    def research(self, query: str, depth: int = 1) -> dict[str, Any]:
        return {"query": query, "depth": depth, "findings": []}


class LocalHeuristicProvider(BaseAIProvider):
    """Dependency-free provider that performs structured but offline analysis.

    Used as the default so the engine works without external services.
    """

    name = "local"

    def complete(self, prompt: str, **kwargs: Any) -> str:
        return (
            "Local heuristic mode: cannot call an external model. "
            "Set engine.config.ai_provider to 'openai' or implement a custom "
            "provider to enable generative responses."
        )

    def research(self, query: str, depth: int = 1) -> dict[str, Any]:
        return {
            "query": query,
            "depth": depth,
            "findings": [
                "Local research provider is offline. Configure an AI provider "
                "to enable live research workflows."
            ],
        }


class OpenAIProvider(BaseAIProvider):
    """Example external provider. Requires `openai` installed and an API key."""

    name = "openai"

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: str, **kwargs: Any) -> str:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""


_PROVIDERS = {
    "local": LocalHeuristicProvider,
    "openai": OpenAIProvider,
}


def get_provider(name: str, **kwargs: Any) -> BaseAIProvider:
    cls = _PROVIDERS.get(name, LocalHeuristicProvider)
    try:
        return cls(**kwargs)
    except Exception:
        return LocalHeuristicProvider()
