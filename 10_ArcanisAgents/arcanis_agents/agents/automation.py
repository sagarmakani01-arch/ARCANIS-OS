"""Automation Agent — controls and executes workflows."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import Message, MessageType


class AutomationAgent(Agent):
    role = "automation"
    capabilities = {AgentCapability.AUTOMATE}

    def __init__(self, name: str = "automation", agent_id: Optional[str] = None) -> None:
        super().__init__(name, agent_id)
        self._workflows: dict[str, Callable] = {}

    def register_workflow(self, name: str, handler: Callable) -> None:
        self._workflows[name] = handler

    async def handle(self, msg: Message) -> Optional[Message]:
        if msg.kind != "task.execute" or msg.msg_type is not MessageType.REQUEST:
            return None
        data = msg.payload or {}
        task_id = data.get("task_id")
        payload = data.get("data") or {}
        if not isinstance(payload, dict):
            payload = {}

        if payload.get("action") == "run":
            result = self._run_workflow(payload, task_id)
        else:
            result = {"action": "automate", "agent": self.name, "task_id": task_id}

        if task_id is not None:
            self.ctx.memory.set("tasks", task_id, result, owner=self.agent_id)
        return self.ctx.bus.reply(msg, self.agent_id, result)

    def _run_workflow(self, payload: dict, task_id: str) -> dict:
        name = payload.get("workflow", "default")
        params = payload.get("params", {})
        handler = self._workflows.get(name)
        start = time.time()
        if handler:
            result = handler(params)
        else:
            result = f"workflow '{name}' not found"
        duration = time.time() - start
        return {
            "action": "completed", "agent": self.name, "task_id": task_id,
            "workflow": name, "result": result, "duration": duration,
        }
