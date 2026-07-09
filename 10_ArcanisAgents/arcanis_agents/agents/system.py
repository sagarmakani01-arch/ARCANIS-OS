"""System Agent — manages ArcanisOS tasks and system state."""

from __future__ import annotations

import platform
from typing import Any, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import Message, MessageType


class SystemAgent(Agent):
    role = "system"
    capabilities = {AgentCapability.OS_TASK}

    def __init__(self, name: str = "system", agent_id: Optional[str] = None) -> None:
        super().__init__(name, agent_id)
        self._runtime: Any = None

    def attach_runtime(self, runtime: Any) -> None:
        self._runtime = runtime

    async def handle(self, msg: Message) -> Optional[Message]:
        if msg.kind != "task.execute" or msg.msg_type is not MessageType.REQUEST:
            return None
        data = msg.payload or {}
        task_id = data.get("task_id")
        payload = data.get("data") or {}
        if not isinstance(payload, dict):
            payload = {}

        if payload.get("action") == "status":
            result = self._report_status(task_id)
        else:
            result = {"action": "system", "agent": self.name, "task_id": task_id}

        if task_id is not None:
            self.ctx.memory.set("tasks", task_id, result, owner=self.agent_id)
        return self.ctx.bus.reply(msg, self.agent_id, result)

    def _report_status(self, task_id: str) -> dict:
        agents: list[str] = []
        memory_keys: list[str] = []
        if self._runtime:
            agents = [a.name for a in self._runtime.agents.values()]
            memory_keys = self._runtime.memory.keys("global")
        return {
            "action": "status", "agent": self.name, "task_id": task_id,
            "platform": platform.system(), "agents": agents, "memory_keys": memory_keys,
        }
