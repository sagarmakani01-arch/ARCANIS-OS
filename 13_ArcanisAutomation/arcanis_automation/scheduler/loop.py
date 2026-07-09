"""Time-based scheduler that dispatches workflows."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Callable, Optional

from arcanis_automation.core.models import Schedule, Workflow


class ScheduledTask:
    def __init__(self, workflow_id: str, schedule: Schedule, callback: Callable[[str], None]):
        self.task_id = "task_" + uuid.uuid4().hex[:8]
        self.workflow_id = workflow_id
        self.schedule = schedule
        self.callback = callback
        self.next_run: Optional[float] = schedule.next_run()
        self.enabled = True
        self.last_run: Optional[float] = None


class Scheduler:
    """Runs scheduled workflows. Single background thread, thread-safe."""

    def __init__(self, poll_interval: float = 1.0):
        self._tasks: dict[str, ScheduledTask] = {}
        self._lock = threading.RLock()
        self._poll = poll_interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def register(self, workflow: Workflow, callback: Callable[[str], None]) -> Optional[str]:
        if not workflow.schedule:
            return None
        task = ScheduledTask(workflow.id, workflow.schedule, callback)
        with self._lock:
            self._tasks[task.task_id] = task
        return task.task_id

    def unregister(self, task_id: str) -> None:
        with self._lock:
            self._tasks.pop(task_id, None)

    def disable(self, task_id: str) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].enabled = False

    def enable(self, task_id: str) -> None:
        with self._lock:
            if task_id in self._tasks:
                t = self._tasks[task_id]
                t.enabled = True
                t.next_run = t.schedule.next_run()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self._poll + 1)

    def _loop(self) -> None:
        while not self._stop.is_set():
            now = time.time()
            with self._lock:
                due = [
                    t for t in self._tasks.values()
                    if t.enabled and t.next_run is not None and t.next_run <= now
                ]
            for task in due:
                try:
                    task.callback(task.workflow_id)
                finally:
                    with self._lock:
                        task.last_run = now
                        task.next_run = task.schedule.next_run(now)
            self._stop.wait(self._poll)

    def list_tasks(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "task_id": t.task_id,
                    "workflow_id": t.workflow_id,
                    "enabled": t.enabled,
                    "next_run": t.next_run,
                    "last_run": t.last_run,
                }
                for t in self._tasks.values()
            ]
