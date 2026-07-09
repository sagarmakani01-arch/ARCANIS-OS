"""Automation engine: create, trigger, chain, and execute workflows."""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Optional

from arcanis_automation.config import AutomationConfig
from arcanis_automation.core.models import (
    Workflow,
    Step,
    Trigger,
    TriggerType,
    ActionSpec,
    ExecutionResult,
    Schedule,
    _gen_id,
)
from arcanis_automation.security.guard import (
    SecurityContext,
    AuditLogger,
    SecurityError,
)
from arcanis_automation.actions.builtins import HANDLERS
from arcanis_automation.scheduler.loop import Scheduler
from arcanis_automation.ai.providers import get_provider
from arcanis_automation.ai.capabilities import WorkflowAI


@dataclass
class EngineEvent:
    name: str
    payload: dict[str, Any]
    timestamp: float = 0.0


class AutomationEngine:
    """Central orchestrator for ArcanisAutomation."""

    def __init__(self, config: Optional[AutomationConfig] = None):
        self.config = config or AutomationConfig()
        self.config.ensure_dirs()
        self.audit = AuditLogger(self.config.log_dir, self.config.audit_all)
        self.security = SecurityContext(
            safe_mode=self.config.safe_mode,
            allowed_paths=[self.config.workspace_dir],
        )
        self.scheduler = Scheduler() if self.config.enable_scheduler else None
        self.ai = WorkflowAI(get_provider(self.config.ai_provider))
        self._handlers: dict[str, Callable] = dict(HANDLERS)
        self._workflows: dict[str, Workflow] = {}
        self._event_subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._running: dict[str, list[ExecutionResult]] = {}
        self.load_store()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_action(self, kind: str, handler: Callable) -> None:
        self._handlers[kind] = handler

    def on_event(self, event: str, subscriber: Callable) -> None:
        self._event_subscribers[event].append(subscriber)

    def _emit(self, event: str, **payload: Any) -> None:
        evt = EngineEvent(event, payload, time.time())
        self.audit.record(event, **payload)
        for sub in self._event_subscribers.get(event, []):
            try:
                sub(evt)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Workflow lifecycle
    # ------------------------------------------------------------------
    def create_workflow(self, definition: dict[str, Any]) -> Workflow:
        wf = Workflow.from_dict(definition)
        wf.updated_at = time.time()
        self._workflows[wf.id] = wf
        self.persist(wf)
        self._emit("workflow.created", workflow_id=wf.id, name=wf.name)
        if wf.schedule and self.scheduler:
            self.scheduler.register(wf, self._on_schedule)
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        return list(self._workflows.values())

    def update_workflow(self, workflow_id: str, definition: dict[str, Any]) -> Workflow:
        definition["id"] = workflow_id
        wf = Workflow.from_dict(definition)
        wf.updated_at = time.time()
        self._workflows[workflow_id] = wf
        self.persist(wf)
        self._emit("workflow.updated", workflow_id=workflow_id)
        return wf

    def delete_workflow(self, workflow_id: str) -> None:
        self._workflows.pop(workflow_id, None)
        path = os.path.join(self.config.storage_dir, workflow_id + ".json")
        if os.path.exists(path):
            os.remove(path)
        self._emit("workflow.deleted", workflow_id=workflow_id)

    # ------------------------------------------------------------------
    # Triggers / events
    # ------------------------------------------------------------------
    def trigger(self, workflow_id: str, event: Optional[dict] = None) -> list[ExecutionResult]:
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise KeyError(f"Unknown workflow: {workflow_id}")
        self._emit("workflow.triggered", workflow_id=workflow_id,
                   trigger=event.get("type") if event else "manual")
        return self.run(wf, event or {})

    def emit_event(self, event_name: str, data: Optional[dict[str, Any]] = None) -> None:
        """Fire all workflows with an EVENT trigger matching `event_name`."""
        for wf in self._workflows.values():
            for trig in wf.triggers:
                if trig.type == TriggerType.EVENT and trig.spec.get("name") == event_name:
                    self.trigger(wf.id, {"type": "event", "name": event_name, **(data or {})})

    def _on_schedule(self, workflow_id: str) -> None:
        self._emit("workflow.scheduled", workflow_id=workflow_id)
        self.run(self._workflows[workflow_id], {"type": "schedule"})

    # ------------------------------------------------------------------
    # Execution (dependency-chained)
    # ------------------------------------------------------------------
    def run(self, wf: Workflow, context: dict[str, Any]) -> list[ExecutionResult]:
        results = asyncio.run(self._run_async(wf, context))
        self._running[wf.id] = results
        self._emit("workflow.finished", workflow_id=wf.id,
                   success=all(r.success for r in results))
        return results

    async def _run_async(self, wf: Workflow, context: dict[str, Any]) -> list[ExecutionResult]:
        results: dict[str, ExecutionResult] = {}
        completed: set[str] = set()
        captured: dict[str, Any] = {}
        pending = {s.id: s for s in wf.steps}
        semaphore = asyncio.Semaphore(self.config.max_concurrent_steps)

        async def execute(step: Step) -> None:
            async with semaphore:
                result = await self._execute_step(step, wf, context, captured)
                results[step.id] = result
                if result.success:
                    completed.add(step.id)
                    for k, v in step.captures.items():
                        captured[k] = _resolve(result.output, v)
                else:
                    if step.on_failure == "stop":
                        # mark downstream as skipped
                        for s in wf.steps:
                            if s.id not in results and s.id != step.id:
                                results[s.id] = ExecutionResult(
                                    s.id, False, error="skipped: upstream failure",
                                    started_at=time.time(), finished_at=time.time(),
                                )

        # Process in waves honoring run_after dependencies.
        remaining = dict(pending)
        while remaining:
            ready = [
                s for s in remaining.values()
                if all(d in completed for d in s.run_after)
            ]
            if not ready:
                # circular or blocked -> fail remaining
                for s in remaining.values():
                    results[s.id] = ExecutionResult(
                        s.id, False, error="unmet dependency", started_at=time.time(),
                        finished_at=time.time(),
                    )
                break
            await asyncio.gather(*(execute(s) for s in ready))
            for s in ready:
                remaining.pop(s.id, None)
        return [results[s.id] for s in wf.steps]

    async def _execute_step(
        self, step: Step, wf: Workflow, context: dict, captured: dict
    ) -> ExecutionResult:
        # permission check
        try:
            self.security.require(step.action.action)
        except SecurityError as exc:
            return ExecutionResult(step.id, False, error=str(exc),
                                   started_at=time.time(), finished_at=time.time())
        handler = self._handlers.get(step.action.action)
        if not handler:
            return ExecutionResult(step.id, False, error="no handler for action",
                                   started_at=time.time(), finished_at=time.time())
        params = dict(step.action.params)
        params = _interpolate(params, context, captured)
        spec = ActionSpec(step.action.action, params, step.action.timeout, step.action.retries)
        attempts = 0
        started = time.time()
        last_error: Optional[str] = None
        while attempts <= spec.retries:
            attempts += 1
            try:
                output = handler(spec, self.security, self, self.audit)
                return ExecutionResult(step.id, True, output, started_at=started,
                                       finished_at=time.time(), attempts=attempts)
            except Exception as exc:  # noqa: BLE001
                last_error = f"{type(exc).__name__}: {exc}"
                if step.on_failure != "retry":
                    break
        return ExecutionResult(step.id, False, error=last_error,
                               started_at=started, finished_at=time.time(),
                               attempts=attempts)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def persist(self, wf: Workflow) -> None:
        path = os.path.join(self.config.storage_dir, wf.id + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(wf.to_dict(), fh, indent=2)

    def load_store(self) -> None:
        if not os.path.isdir(self.config.storage_dir):
            return
        for name in os.listdir(self.config.storage_dir):
            if name.endswith(".json"):
                try:
                    with open(os.path.join(self.config.storage_dir, name),
                              "r", encoding="utf-8") as fh:
                        self._workflows[name[:-5]] = Workflow.from_dict(json.load(fh))
                except Exception:
                    continue

    # ------------------------------------------------------------------
    # Scheduler control
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self.scheduler:
            for wf in self._workflows.values():
                if wf.schedule:
                    self.scheduler.register(wf, self._on_schedule)
            self.scheduler.start()
            self._emit("engine.started")

    def stop(self) -> None:
        if self.scheduler:
            self.scheduler.stop()
            self._emit("engine.stopped")

    # ------------------------------------------------------------------
    # AI helpers
    # ------------------------------------------------------------------
    def generate_workflow(self, description: str) -> Workflow:
        wf = self.ai.generate(description)
        return self.create_workflow(wf.to_dict())

    def optimize_workflow(self, workflow_id: str) -> Workflow:
        wf = self._workflows[workflow_id]
        optimized = self.ai.optimize(wf)
        return self.update_workflow(workflow_id, optimized.to_dict())

    def detect_failures(self, workflow_id: str) -> dict[str, Any]:
        results = self._running.get(workflow_id, [])
        return self.ai.detect_failures([r.to_dict() for r in results])


def _interpolate(value: Any, context: dict, captured: dict) -> Any:
    if isinstance(value, str):
        for k, v in {**context, **captured}.items():
            value = value.replace("{{" + k + "}}", str(v))
        return value
    if isinstance(value, dict):
        return {k: _interpolate(v, context, captured) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v, context, captured) for v in value]
    return value


def _resolve(output: Any, path: str) -> Any:
    cur = output
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur
