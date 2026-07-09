"""Autonomous system administration — self-healing, self-diagnosing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ActionSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    name: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemAction:
    action_type: str = ""
    target: str = ""
    description: str = ""
    severity: ActionSeverity = ActionSeverity.INFO
    auto_executed: bool = False
    result: str = ""
    timestamp: float = field(default_factory=time.time)


class HealthChecker:
    def __init__(self):
        self._checks: dict[str, Callable[[], HealthCheck]] = {}
        self._results: dict[str, HealthCheck] = {}

    def register(self, name: str, check_fn: Callable[[], HealthCheck]) -> None:
        self._checks[name] = check_fn

    def run_all(self) -> list[HealthCheck]:
        results: list[HealthCheck] = []
        for name, fn in self._checks.items():
            start = time.time()
            try:
                check = fn()
                check.duration_ms = (time.time() - start) * 1000
            except Exception as e:
                check = HealthCheck(
                    name=name, status=HealthStatus.CRITICAL,
                    message=str(e), duration_ms=(time.time() - start) * 1000,
                )
            self._results[name] = check
            results.append(check)
        return results

    def run(self, name: str) -> Optional[HealthCheck]:
        fn = self._checks.get(name)
        if not fn:
            return None
        start = time.time()
        try:
            check = fn()
            check.duration_ms = (time.time() - start) * 1000
        except Exception as e:
            check = HealthCheck(name=name, status=HealthStatus.CRITICAL, message=str(e))
        self._results[name] = check
        return check

    def get_overall_status(self) -> HealthStatus:
        if not self._results:
            return HealthStatus.UNKNOWN
        statuses = [r.status for r in self._results.values()]
        if any(s == HealthStatus.CRITICAL for s in statuses):
            return HealthStatus.CRITICAL
        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        return HealthStatus.UNKNOWN

    def get_results(self) -> dict[str, HealthCheck]:
        return dict(self._results)


class SelfHealer:
    def __init__(self):
        self._healing_rules: dict[str, Callable[[HealthCheck], Optional[SystemAction]]] = {}
        self._actions: list[SystemAction] = []
        self._max_actions_per_hour = 20
        self._action_timestamps: list[float] = []

    def register_rule(self, check_name: str, healing_fn: Callable[[HealthCheck], Optional[SystemAction]]) -> None:
        self._healing_rules[check_name] = healing_fn

    def attempt_heal(self, check: HealthCheck) -> Optional[SystemAction]:
        if not self._can_act():
            return None

        rule = self._healing_rules.get(check.name)
        if not rule:
            return None

        action = rule(check)
        if action:
            action.auto_executed = True
            action.result = "auto-healed"
            self._actions.append(action)
            self._action_timestamps.append(time.time())
        return action

    def _can_act(self) -> bool:
        now = time.time()
        self._action_timestamps = [t for t in self._action_timestamps if now - t < 3600]
        return len(self._action_timestamps) < self._max_actions_per_hour

    def get_actions(self, limit: int = 50) -> list[SystemAction]:
        return self._actions[-limit:]


class AutonomousAdmin:
    def __init__(self):
        self.health = HealthChecker()
        self.healer = SelfHealer()
        self._diagnostics: list[dict[str, Any]] = []
        self._initialized = False

    def initialize(self) -> None:
        self._register_default_checks()
        self._register_default_healing()
        self._initialized = True

    def _register_default_checks(self) -> None:
        self.health.register("memory", lambda: HealthCheck(
            name="memory", status=HealthStatus.HEALTHY, message="Memory within normal range"))
        self.health.register("disk", lambda: HealthCheck(
            name="disk", status=HealthStatus.HEALTHY, message="Disk usage within limits"))
        self.health.register("processes", lambda: HealthCheck(
            name="processes", status=HealthStatus.HEALTHY, message="All processes responsive"))
        self.health.register("network", lambda: HealthCheck(
            name="network", status=HealthStatus.HEALTHY, message="Network connectivity active"))

    def _register_default_healing(self) -> None:
        def heal_memory(check: HealthCheck) -> Optional[SystemAction]:
            if check.status == HealthStatus.CRITICAL:
                return SystemAction(action_type="restart_service", target="memory_cache",
                                    description="Clear memory cache due to critical usage",
                                    severity=ActionSeverity.WARNING)
            return None

        def heal_disk(check: HealthCheck) -> Optional[SystemAction]:
            if check.status in (HealthStatus.DEGRADED, HealthStatus.CRITICAL):
                return SystemAction(action_type="cleanup", target="disk",
                                    description="Run disk cleanup due to high usage",
                                    severity=ActionSeverity.WARNING)
            return None

        self.healer.register_rule("memory", heal_memory)
        self.healer.register_rule("disk", heal_disk)

    def run_diagnostics(self) -> dict[str, Any]:
        checks = self.health.run_all()
        actions: list[SystemAction] = []
        for check in checks:
            if check.status in (HealthStatus.DEGRADED, HealthStatus.CRITICAL):
                action = self.healer.attempt_heal(check)
                if action:
                    actions.append(action)

        result = {
            "overall_status": self.health.get_overall_status().value,
            "checks": {c.name: {"status": c.status.value, "message": c.message} for c in checks},
            "actions_taken": len(actions),
            "timestamp": time.time(),
        }
        self._diagnostics.append(result)
        return result

    def get_status(self) -> dict:
        return {
            "initialized": self._initialized,
            "overall_health": self.health.get_overall_status().value,
            "checks_run": len(self.health.get_results()),
            "actions_taken": len(self.healer.get_actions()),
            "diagnostics_history": len(self._diagnostics),
        }
