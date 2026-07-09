"""ArcanisShell — error definitions.

Centralized exception hierarchy so every layer can raise typed,
loggable errors instead of leaking raw exceptions to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class ArcanisShellError(Exception):
    """Base class for all ArcanisShell errors."""


@dataclass
class PermissionDeniedError(ArcanisShellError):
    """Raised when an action violates the active permission policy."""

    action: str
    reason: str

    def __str__(self) -> str:
        return f"permission denied: {self.action} — {self.reason}"


@dataclass
class SandboxViolationError(ArcanisShellError):
    """Raised when an action attempts to leave the sandbox boundary."""

    action: str
    attempted_path: Optional[Path] = None

    def __str__(self) -> str:
        target = self.attempted_path or "<unknown>"
        return f"sandbox violation: {self.action} attempted on {target}"


@dataclass
class CommandNotFoundError(ArcanisShellError):
    """Raised when a traditional command name is unknown."""

    name: str

    def __str__(self) -> str:
        return f"unknown command: {self.name}"


@dataclass
class ParseError(ArcanisShellError):
    """Raised when user input cannot be parsed into a command or intent."""

    raw: str
    detail: str = ""

    def __str__(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"parse error for {self.raw!r}{suffix}"


@dataclass
class PlanRejectedError(ArcanisShellError):
    """Raised when the user rejects a proposed AI plan."""

    step_count: int = 0

    def __str__(self) -> str:
        return f"plan rejected by user ({self.step_count} steps)"


@dataclass
class AIUnavailableError(ArcanisShellError):
    """Raised when the AI backend cannot be reached."""

    backend: str
    detail: str = ""

    def __str__(self) -> str:
        suffix = f": {self.detail}" if self.detail else ""
        return f"AI backend '{self.backend}' unavailable{suffix}"


@dataclass
class ShellRuntimeError(ArcanisShellError):
    """Generic internal runtime failure carrying structured context."""

    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message
