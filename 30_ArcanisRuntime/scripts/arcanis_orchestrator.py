"""Autonomous Orchestrator — self-managing system coordinator."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class OrchestratorState(Enum):
    INITIALIZING = "initializing"
    MONITORING = "monitoring"
    HEALING = "healing"
    OPTIMIZING = "optimizing"
    ERROR = "error"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class SystemTask:
    task_id: str = ""
    name: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    action: Optional[Callable] = None
    condition: Optional[Callable] = None
    interval_seconds: float = 60.0
    last_run: float = 0.0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    check_id: str = ""
    name: str = ""
    description: str = ""
    check_fn: Optional[Callable] = None
    auto_heal_fn: Optional[Callable] = None
    interval_seconds: float = 30.0
    last_check: float = 0.0
    last_status: str = "unknown"
    consecutive_failures: int = 0
    max_failures: int = 3


@dataclass
class Event:
    event_type: str = ""
    source: str = ""
    message: str = ""
    severity: str = "info"
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._history: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        self._history.append(event)
        if len(self._history) > 1000:
            self._history = self._history[-500:]
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                pass
        for handler in self._handlers.get("*", []):
            try:
                handler(event)
            except Exception:
                pass

    def get_history(self, event_type: str = "", limit: int = 50) -> list[Event]:
        events = self._history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]


class AutonomousOrchestrator:
    def __init__(self):
        self.state = OrchestratorState.INITIALIZING
        self.event_bus = EventBus()
        self._tasks: dict[str, SystemTask] = {}
        self._health_checks: dict[str, HealthCheck] = {}
        self._uptime_start: float = 0.0
        self._cycle_count: int = 0
        self._initialized = False

    def initialize(self) -> None:
        self._uptime_start = time.time()
        self.state = OrchestratorState.MONITORING
        self._initialized = True
        self.event_bus.publish(Event(
            event_type="system.init", source="orchestrator",
            message="Autonomous orchestrator initialized",
        ))

    def register_task(self, task: SystemTask) -> None:
        self._tasks[task.task_id] = task

    def register_health_check(self, check: HealthCheck) -> None:
        self._health_checks[check.check_id] = check

    def tick(self) -> dict[str, Any]:
        if not self._initialized:
            return {"error": "Not initialized"}

        self._cycle_count += 1
        now = time.time()
        results = {"tasks_run": 0, "checks_run": 0, "heals_attempted": 0, "events": []}

        for task in self._tasks.values():
            if not task.enabled:
                continue
            if task.condition and not task.condition():
                continue
            if now - task.last_run >= task.interval_seconds:
                if task.action:
                    try:
                        task.action()
                        task.last_run = now
                        results["tasks_run"] += 1
                    except Exception as e:
                        self.event_bus.publish(Event(
                            event_type="task.error", source=task.task_id,
                            message=str(e), severity="error",
                        ))

        for check in self._health_checks.values():
            if now - check.last_check >= check.interval_seconds:
                if check.check_fn:
                    try:
                        status = check.check_fn()
                        check.last_status = "healthy" if status else "unhealthy"
                        check.last_check = now
                        check.consecutive_failures = 0 if status else check.consecutive_failures + 1
                        results["checks_run"] += 1

                        if not status and check.consecutive_failures >= check.max_failures:
                            if check.auto_heal_fn:
                                try:
                                    check.auto_heal_fn()
                                    results["heals_attempted"] += 1
                                    self.event_bus.publish(Event(
                                        event_type="heal.attempt", source=check.check_id,
                                        message=f"Auto-healing triggered for {check.name}",
                                        severity="warning",
                                    ))
                                except Exception as e:
                                    self.event_bus.publish(Event(
                                        event_type="heal.failed", source=check.check_id,
                                        message=str(e), severity="error",
                                    ))
                    except Exception:
                        check.last_status = "error"
                        check.consecutive_failures += 1

        return results

    def get_status(self) -> dict:
        uptime = time.time() - self._uptime_start if self._uptime_start else 0
        healthy_checks = sum(1 for c in self._health_checks.values() if c.last_status == "healthy")
        total_checks = len(self._health_checks)
        return {
            "state": self.state.value,
            "uptime_seconds": round(uptime, 1),
            "cycle_count": self._cycle_count,
            "tasks_registered": len(self._tasks),
            "health_checks": f"{healthy_checks}/{total_checks}",
            "event_count": len(self.event_bus._history),
        }

    def shutdown(self) -> None:
        self.state = OrchestratorState.INITIALIZING
        self._initialized = False
        self.event_bus.publish(Event(
            event_type="system.shutdown", source="orchestrator",
            message="Autonomous orchestrator shut down",
        ))
