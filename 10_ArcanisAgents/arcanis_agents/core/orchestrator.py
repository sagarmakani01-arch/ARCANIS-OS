"""Task delegation and orchestration."""

from __future__ import annotations

import asyncio
import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from .agent import Agent, AgentCapability, AgentContext
from .message_bus import MessageBus, Message, MessageType
from .shared_memory import SharedMemory
from .permissions import PermissionSystem, Permission, Role

logger = logging.getLogger("arcanis.orchestrator")


class TaskStatus(enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"


@dataclass
class Task:
    description: str
    required_capability: Optional[AgentCapability] = None
    payload: Any = None
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    parent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def view(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


_CAP_TO_PERM: dict[AgentCapability, Permission] = {
    AgentCapability.WRITE_CODE: Permission.CODE_WRITE,
    AgentCapability.REVIEW_CODE: Permission.CODE_REVIEW,
    AgentCapability.DEBUG: Permission.CODE_WRITE,
    AgentCapability.RESEARCH: Permission.NETWORK_FETCH,
    AgentCapability.SUMMARIZE: Permission.MEMORY_WRITE,
    AgentCapability.AUTOMATE: Permission.OS_EXECUTE,
    AgentCapability.SECURITY_SCAN: Permission.SECURITY_SCAN,
    AgentCapability.OS_TASK: Permission.OS_EXECUTE,
}


class Orchestrator:
    def __init__(
        self,
        bus: Optional[MessageBus] = None,
        memory: Optional[SharedMemory] = None,
        permissions: Optional[PermissionSystem] = None,
    ) -> None:
        self.bus = bus or MessageBus()
        self.memory = memory or SharedMemory()
        self.permissions = permissions or PermissionSystem()
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self._cap_index: dict[AgentCapability, list[str]] = {}

    def register(self, agent: Agent, roles: Optional[list[Role]] = None) -> Agent:
        ctx = AgentContext(
            agent_id=agent.agent_id,
            name=agent.name,
            bus=self.bus,
            memory=self.memory,
            permissions=self.permissions,
        )
        agent.attach(ctx)
        self.agents[agent.agent_id] = agent
        for cap in agent.capabilities:
            self._cap_index.setdefault(cap, []).append(agent.agent_id)
        if roles:
            self.permissions.register_agent(agent.agent_id, agent.name, roles)
        elif not self.permissions.roles_of(agent.agent_id):
            self.permissions.register_agent(agent.agent_id, agent.name, [])
        return agent

    def start_all(self) -> None:
        for agent in self.agents.values():
            agent.start()

    async def stop_all(self) -> None:
        for agent in self.agents.values():
            await agent.stop()

    def _find_agent(self, capability: Optional[AgentCapability]) -> Optional[str]:
        if capability is None:
            ids = self._cap_index.get(AgentCapability.OS_TASK, [])
            return ids[0] if ids else next(iter(self.agents), None)
        candidates = self._cap_index.get(capability, [])
        return candidates[0] if candidates else None

    async def delegate(
        self,
        description: str,
        capability: Optional[AgentCapability] = None,
        payload: Any = None,
        parent_id: Optional[str] = None,
        requester: Optional[str] = None,
    ) -> Task:
        agent_id = self._find_agent(capability)
        task = Task(
            description=description,
            required_capability=capability,
            payload=payload,
            parent_id=parent_id,
        )
        if agent_id is None:
            task.status = TaskStatus.FAILED
            task.error = f"No agent with capability {capability}"
            self.tasks[task.task_id] = task
            return task
        if requester:
            perm = _CAP_TO_PERM.get(capability, Permission.MEMORY_READ)
            self.permissions.require(requester, perm)

        task.assigned_to = agent_id
        task.status = TaskStatus.IN_PROGRESS
        self.tasks[task.task_id] = task

        reply = await self.bus.request(
            sender=requester or "orchestrator",
            to=agent_id,
            kind="task.execute",
            payload={"task_id": task.task_id, "description": description, "data": payload},
        )
        if reply is not None and reply.payload is not None:
            task.result = reply.payload
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
        else:
            result = self.memory.get("tasks", task.task_id)
            if result is not None:
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
            else:
                task.status = TaskStatus.FAILED
                task.error = "no result returned"
        return task

    def status(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
