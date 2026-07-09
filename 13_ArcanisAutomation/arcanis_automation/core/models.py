"""Data models describing the ArcanisAutomation workflow format."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Callable


class WorkflowStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TriggerType(enum.Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    WEBHOOK = "webhook"
    CONDITION = "condition"


class PermissionLevel(enum.Enum):
    DENY = "deny"
    READ = "read"
    EXECUTE = "execute"
    ADMIN = "admin"


class ActionKind(enum.Enum):
    FILE_ORGANIZE = "file.organize"
    FILE_MOVE = "file.move"
    FILE_COPY = "file.copy"
    FILE_DELETE = "file.delete"
    APP_LAUNCH = "app.launch"
    APP_KILL = "app.kill"
    APP_FOCUS = "app.focus"
    DATA_TRANSFORM = "data.transform"
    DATA_AGGREGATE = "data.aggregate"
    RESEARCH_QUERY = "research.query"
    RESEARCH_FETCH = "research.fetch"
    SHELL = "shell"
    HTTP = "http"
    NOTIFY = "notify"
    AI_GENERATE = "ai.generate"
    AI_ANALYZE = "ai.analyze"


@dataclass
class ActionSpec:
    """A single invocation target: <action_kind> with parameters."""

    action: str
    params: dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, "params": self.params,
                "timeout": self.timeout, "retries": self.retries}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionSpec":
        return cls(
            action=data["action"],
            params=data.get("params", {}) or {},
            timeout=float(data.get("timeout", 30.0)),
            retries=int(data.get("retries", 0)),
        )


@dataclass
class Trigger:
    """Describes when a workflow may run."""

    type: TriggerType
    spec: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "spec": self.spec}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trigger":
        return cls(
            type=TriggerType(data["type"]),
            spec=data.get("spec", {}) or {},
        )


@dataclass
class Schedule:
    """Scheduling descriptor for time-based triggers."""

    cron: Optional[str] = None
    interval_seconds: Optional[float] = None
    at_timestamp: Optional[float] = None
    timezone: str = "UTC"

    def next_run(self, after: Optional[float] = None) -> Optional[float]:
        after = after or time.time()
        if self.at_timestamp is not None and self.at_timestamp >= after:
            return self.at_timestamp
        if self.interval_seconds is not None:
            return after + self.interval_seconds
        if self.cron is not None:
            return _next_cron(self.cron, after, self.timezone)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cron": self.cron,
            "interval_seconds": self.interval_seconds,
            "at_timestamp": self.at_timestamp,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        return cls(
            cron=data.get("cron"),
            interval_seconds=data.get("interval_seconds"),
            at_timestamp=data.get("at_timestamp"),
            timezone=data.get("timezone", "UTC"),
        )


@dataclass
class Step:
    """One node in a workflow. Steps may chain via `run_after`."""

    id: str
    action: ActionSpec
    name: str = ""
    run_after: list[str] = field(default_factory=list)
    on_failure: str = "stop"  # stop | continue | retry
    condition: Optional[str] = None
    captures: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action.to_dict(),
            "run_after": self.run_after,
            "on_failure": self.on_failure,
            "condition": self.condition,
            "captures": self.captures,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            action=ActionSpec.from_dict(data["action"]),
            run_after=data.get("run_after", []) or [],
            on_failure=data.get("on_failure", "stop"),
            condition=data.get("condition"),
            captures=data.get("captures", {}) or {},
        )


@dataclass
class Permission:
    """Per-scope permission grant."""

    level: PermissionLevel = PermissionLevel.EXECUTE
    scope: str = "*"  # action prefix, e.g. "file.*" or "app.launch"

    def allows(self, action: str) -> bool:
        if self.level == PermissionLevel.DENY:
            return False
        if self.scope == "*":
            return True
        if self.scope.endswith(".*"):
            return action.startswith(self.scope[:-1])
        return action == self.scope

    def to_dict(self) -> dict[str, Any]:
        return {"level": self.level.value, "scope": self.scope}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Permission":
        return cls(
            level=PermissionLevel(data.get("level", "execute")),
            scope=data.get("scope", "*"),
        )


@dataclass
class Workflow:
    """A complete automation workflow."""

    id: str
    name: str
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    triggers: list[Trigger] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    schedule: Optional[Schedule] = None
    permissions: list[Permission] = field(default_factory=list)
    owner: str = "system"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "triggers": [t.to_dict() for t in self.triggers],
            "steps": [s.to_dict() for s in self.steps],
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "permissions": [p.to_dict() for p in self.permissions],
            "owner": self.owner,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        sched = data.get("schedule")
        return cls(
            id=data.get("id") or _gen_id(),
            name=data["name"],
            description=data.get("description", ""),
            status=WorkflowStatus(data.get("status", "draft")),
            triggers=[Trigger.from_dict(t) for t in data.get("triggers", [])],
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            schedule=Schedule.from_dict(sched) if sched else None,
            permissions=[Permission.from_dict(p) for p in data.get("permissions", [])],
            owner=data.get("owner", "system"),
            tags=data.get("tags", []) or [],
            metadata=data.get("metadata", {}) or {},
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class ExecutionResult:
    """Outcome of running one step or a whole workflow."""

    step_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    finished_at: float = field(default_factory=time.time)
    attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _gen_id() -> str:
    return "wf_" + uuid.uuid4().hex[:12]


def _next_cron(expr: str, after: float, tz: str) -> Optional[float]:
    """Best-effort next-run for a 5-field cron expression.

    Falls back to +60s if no cron library is available. This keeps the
    package dependency-free while still providing functional scheduling.
    """
    try:
        from croniter import croniter  # type: ignore
        from datetime import datetime, timezone
        base = datetime.fromtimestamp(after, tz=timezone.utc)
        return croniter(expr, base).get_next(float)
    except Exception:
        return after + 60.0
