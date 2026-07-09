"""Generic functional agent used by the factory."""

from __future__ import annotations

from typing import Any, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import Message, MessageType
from ..core.factory import Behavior


class FunctionalAgent(Agent):
    def __init__(
        self,
        name: str,
        capabilities: set[AgentCapability],
        behavior: Behavior = Behavior.ECHO,
        description: str = "",
        agent_id: Optional[str] = None,
    ) -> None:
        super().__init__(name, agent_id)
        self.capabilities = capabilities
        self.behavior = behavior
        self.description = description

    async def handle(self, msg: Message) -> Optional[Message]:
        if msg.kind == "task.execute" and msg.msg_type is MessageType.REQUEST:
            data = msg.payload or {}
            task_id = data.get("task_id")
            result = await self._execute(data.get("description", ""), data.get("data"))
            if task_id is not None:
                self.ctx.memory.set("tasks", task_id, result, owner=self.agent_id)
            return self.ctx.bus.reply(msg, self.agent_id, result)
        return None

    async def _execute(self, description: str, data: Any) -> Any:
        if self.behavior is Behavior.ECHO:
            return {"agent": self.name, "echo": description, "data": data}
        return {"agent": self.name, "note": "no behavior implemented"}
