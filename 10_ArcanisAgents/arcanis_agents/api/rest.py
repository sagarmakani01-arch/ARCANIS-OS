"""REST-style API facade for ArcanisAgents."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import MessageBus, Message, MessageType
from ..core.shared_memory import SharedMemory
from ..core.permissions import Permission, PermissionSystem, Role
from ..core.orchestrator import Orchestrator, Task, TaskStatus
from ..core.factory import AgentFactory, AgentSpec, Behavior
from ..agents.developer import DeveloperAgent
from ..agents.research import ResearchAgent
from ..agents.automation import AutomationAgent
from ..agents.security import SecurityAgent
from ..agents.system import SystemAgent

logger = logging.getLogger("arcanis.api")

_ROLE_CLASSES = {
    "developer": DeveloperAgent,
    "research": ResearchAgent,
    "automation": AutomationAgent,
    "security": SecurityAgent,
    "system": SystemAgent,
}

_ROLE_ENUM = {
    "developer": Role.DEVELOPER,
    "research": Role.RESEARCHER,
    "automation": Role.AUTOMATOR,
    "security": Role.SECURITY,
    "system": Role.SYSTEM,
}


class API:
    """High-level API for managing the ArcanisAgents swarm."""

    def __init__(self) -> None:
        self.bus = MessageBus()
        self.memory = SharedMemory()
        self.permissions = PermissionSystem()
        self.orchestrator = Orchestrator(bus=self.bus, memory=self.memory, permissions=self.permissions)
        self.factory = AgentFactory()
        self.factory.register_behavior(Behavior.ECHO, AgentFactory.default_builder)
        self._agents: dict[str, Agent] = {}
        self._started = False

    def spawn_agent(self, role: str, name: str, agent_id: Optional[str] = None) -> dict:
        cls = _ROLE_CLASSES.get(role)
        if cls is None:
            raise ValueError(f"Unknown role '{role}'")
        agent = cls(name=name, agent_id=agent_id)
        role_enum = _ROLE_ENUM.get(role)
        self.add_agent(agent, roles=[role_enum] if role_enum else None)
        return {"agent_id": agent.agent_id, "name": name, "role": role}

    def add_agent(self, agent: Agent, roles: Optional[list[Role]] = None) -> None:
        self.orchestrator.register(agent, roles)
        self._agents[agent.agent_id] = agent

    def spawn_default_agents(self) -> None:
        self.spawn_agent("developer", "Dev-01")
        self.spawn_agent("research", "Res-01")
        self.spawn_agent("automation", "Auto-01")
        self.spawn_agent("security", "Sec-01")
        self.spawn_agent("system", "Sys-01")

    async def send_message(self, sender: str, to: str, kind: str, payload: Any) -> Optional[Message]:
        return await self.bus.request(sender, to, kind, payload)

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self.orchestrator.start_all()

    async def stop(self) -> None:
        self._started = False
        await self.orchestrator.stop_all()

    def shutdown(self) -> None:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.stop())
        else:
            loop.run_until_complete(self.stop())

    def status(self) -> dict:
        return {"agents": list(self._agents.keys()), "started": self._started}

    def list_agents(self) -> list[dict]:
        return [{"agent_id": a.agent_id, "name": a.name, "role": getattr(a, "role", "agent")} for a in self._agents.values()]

    async def run_task(self, description: str, capability: Optional[AgentCapability] = None, data: Any = None) -> Task:
        task = await self.orchestrator.delegate(description=description, capability=capability, payload=data)
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return task
        for _ in range(50):
            await asyncio.sleep(0.05)
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                return task
        return task

    def task_status(self, task_id: str) -> Optional[dict]:
        task = self.orchestrator.status(task_id)
        if task is None:
            return None
        return {
            "task_id": task.task_id,
            "description": task.description,
            "assigned_to": task.assigned_to,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
        }

    def memory_get(self, key: str, namespace: str = "global") -> Any:
        return self.memory.get(namespace, key)

    def memory_set(self, key: str, value: Any, namespace: str = "global") -> None:
        self.memory.set(namespace, key, value, owner="api")

    def memory_keys(self, namespace: Optional[str] = None) -> list[str]:
        if namespace:
            return self.memory.keys(namespace)
        all_keys = []
        for ns in ["global", "developer", "research", "automation", "security", "system"]:
            all_keys.extend(self.memory.keys(ns))
        return all_keys
