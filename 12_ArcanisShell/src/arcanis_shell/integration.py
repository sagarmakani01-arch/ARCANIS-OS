"""ArcanisShell — ecosystem integration stubs.

Thin, dependency-free adapters for the sibling Arcanis projects. They are
designed to be wired to the real implementations later; until then they
provide deterministic, offline behavior so the shell remains usable
without the broader ecosystem installed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class BrainResponse:
    """Structured response from ArcanisBrain."""

    intent: str
    plan_steps: list[dict[str, Any]]
    explanation: str
    confidence: float


class BrainAdapter(ABC):
    """Interface to ArcanisBrain reasoning/planning."""

    @abstractmethod
    def understand(self, request: str, context: dict[str, Any]) -> BrainResponse: ...


class AgentsAdapter(ABC):
    """Interface to ArcanisAgents task delegation."""

    @abstractmethod
    def delegate(self, task: dict[str, Any]) -> dict[str, Any]: ...


class OSAdapter(ABC):
    """Interface to ArcanisOS services (fs, security, scheduling)."""

    @abstractmethod
    def filesystem_root(self) -> str: ...

    @abstractmethod
    def security_token(self) -> Optional[str]: ...


class LocalBrainAdapter(BrainAdapter):
    """Offline heuristic Brain used when the real backend is unavailable."""

    def understand(self, request: str, context: dict[str, Any]) -> BrainResponse:
        text = request.lower()
        steps: list[dict[str, Any]] = []
        if "organize" in text and "project" in text:
            root = context.get("cwd", ".")
            steps = [
                {
                    "description": f"Create folders under {root}",
                    "command": "mkdir -p project/src project/docs project/assets",
                    "risk": "low",
                },
                {
                    "description": "Move source files",
                    "command": "mv *.py project/src",
                    "risk": "medium",
                },
                {"description": "Move docs", "command": "mv *.md project/docs", "risk": "medium"},
            ]
            explanation = (
                "I detected an intent to organize project files. I will create a "
                "standard layout (src/docs/assets) and group files by type. "
                "Moves are reversible and scoped to the current directory."
            )
        elif "list" in text or "show" in text and "file" in text:
            steps = [{"description": "List files", "command": "ls", "risk": "safe"}]
            explanation = "I will list the contents of the current directory."
        else:
            steps = [
                {
                    "description": "Echo the request back (no action taken)",
                    "command": f"echo {request!r}",
                    "risk": "safe",
                }
            ]
            explanation = (
                "I could not confidently map this request to a concrete plan. "
                "As a safe default I will echo it back. Connect ArcanisBrain for "
                "richer planning."
            )
        return BrainResponse(
            intent=request, plan_steps=steps, explanation=explanation, confidence=0.6
        )


class LocalAgentsAdapter(AgentsAdapter):
    """Offline Agents adapter; records delegation locally."""

    def delegate(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"status": "delegated_offline", "task": task}


class LocalOSAdapter(OSAdapter):
    """Offline OS adapter using the local filesystem."""

    def filesystem_root(self) -> str:
        from pathlib import Path

        return str(Path.cwd())

    def security_token(self) -> Optional[str]:
        return None


def load_brain(backend: str) -> BrainAdapter:
    """Return a Brain adapter for the requested backend name."""
    if backend in ("arcanis_brain", "brain"):
        try:
            from arcanis_brain.api import BrainClient  # type: ignore

            class _Remote(BrainAdapter):
                def understand(self, request: str, context: dict[str, Any]) -> BrainResponse:
                    resp = BrainClient().plan(request, context)
                    return BrainResponse(**resp)

            return _Remote()
        except Exception:  # noqa: BLE001
            return LocalBrainAdapter()
    return LocalBrainAdapter()


def load_agents() -> AgentsAdapter:
    try:
        from arcanis_agents import AgentHub  # type: ignore

        class _Remote(AgentsAdapter):
            def delegate(self, task: dict[str, Any]) -> dict[str, Any]:
                return dict(AgentHub().dispatch(task))

        return _Remote()
    except Exception:  # noqa: BLE001
        return LocalAgentsAdapter()


def load_os() -> OSAdapter:
    try:
        from arcanis_os import FileSystem  # type: ignore

        class _Remote(OSAdapter):
            def filesystem_root(self) -> str:
                return str(FileSystem().root())

            def security_token(self) -> Optional[str]:
                token: Optional[str] = FileSystem().token()
                return token

        return _Remote()
    except Exception:  # noqa: BLE001
        return LocalOSAdapter()
