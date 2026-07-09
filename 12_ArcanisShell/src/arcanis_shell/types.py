"""ArcanisShell — shared types and value objects.

Uses pydantic models for any externally-serializable structure (plans,
command specs) and lightweight dataclasses for internal runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk classification used by the permission and planning systems."""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommandSource(str, Enum):
    """How a command/action originated."""

    TRADITIONAL = "traditional"
    AI_GENERATED = "ai_generated"
    AUTOMATION = "automation"


@dataclass
class CommandResult:
    """Result of executing a single command or plan step."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def output(self) -> str:
        return self.stdout

    def __str__(self) -> str:
        return self.stdout if self.success else self.stderr


class CommandSpec(BaseModel):
    """Serializable description of a command a user can invoke."""

    name: str
    description: str
    category: str
    risk: RiskLevel = RiskLevel.LOW
    examples: list[str] = Field(default_factory=list)
    accepts_args: bool = True
    accepts_flags: bool = True


class PlanStep(BaseModel):
    """A single executable step in an AI-generated plan."""

    index: int
    description: str
    command: str
    risk: RiskLevel = RiskLevel.LOW
    rationale: str = ""


class ExecutionPlan(BaseModel):
    """A safe, reviewable plan produced from a natural-language request."""

    intent: str
    summary: str
    steps: list[PlanStep] = Field(default_factory=list)
    requires_approval: bool = True

    @property
    def max_risk(self) -> RiskLevel:
        order = list(RiskLevel)
        return max((step.risk for step in self.steps), key=order.index, default=RiskLevel.SAFE)


@dataclass
class ActivityEntry:
    """One line in the activity log."""

    timestamp: str
    source: CommandSource
    action: str
    risk: RiskLevel
    approved: bool
    outcome: str
    detail: str = ""
