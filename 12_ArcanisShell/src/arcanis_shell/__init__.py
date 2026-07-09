"""ArcanisShell — next-generation shell with traditional and AI interfaces.

Public surface of the package.
"""

from __future__ import annotations

from .ai_interface import AIInterface
from .config import ShellConfig
from .engine import ShellEngine, repl
from .errors import ArcanisShellError
from .parser import CommandParser
from .security import ActivityLog, PermissionPolicy, Sandbox
from .types import CommandResult, ExecutionPlan, RiskLevel

__version__ = "0.1.0"

__all__ = [
    "AIInterface",
    "ShellConfig",
    "ShellEngine",
    "repl",
    "ArcanisShellError",
    "CommandParser",
    "ActivityLog",
    "PermissionPolicy",
    "Sandbox",
    "CommandResult",
    "ExecutionPlan",
    "RiskLevel",
]
