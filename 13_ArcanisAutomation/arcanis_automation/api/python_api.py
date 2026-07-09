"""Pythonic high-level API for ArcanisAutomation."""

from __future__ import annotations

from typing import Any, Optional

from arcanis_automation.config import AutomationConfig
from arcanis_automation.core.engine import AutomationEngine


class Automation:
    """Convenience facade for scripting and embedding."""

    def __init__(self, config: Optional[AutomationConfig] = None):
        self.engine = AutomationEngine(config)

    def create(self, name: str, steps: list[dict], **kwargs: Any) -> str:
        wf = {
            "name": name,
            "steps": steps,
            "triggers": kwargs.get("triggers", [{"type": "manual"}]),
            **{k: v for k, v in kwargs.items() if k != "triggers"},
        }
        return self.engine.create_workflow(wf).id

    def run(self, workflow_id: str, context: Optional[dict] = None):
        return self.engine.trigger(workflow_id, context)

    def generate(self, description: str) -> str:
        return self.engine.generate_workflow(description).id

    def get(self, workflow_id: str):
        return self.engine.get_workflow(workflow_id)

    def list(self):
        return self.engine.list_workflows()

    def start(self) -> None:
        self.engine.start()

    def stop(self) -> None:
        self.engine.stop()
