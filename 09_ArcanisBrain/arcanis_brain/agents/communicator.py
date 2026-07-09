from typing import Any
from arcanis_brain.core.types import Message, MessageRole


class AgentCommunicator:
    def __init__(self, brain):
        self.brain = brain
        self._channels: dict[str, list[dict]] = {}

    async def send(self, recipient: str, message: Message) -> bool:
        if recipient not in self._channels:
            self._channels[recipient] = []
        self._channels[recipient].append({
            "message": message,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
        self.brain.event_bus.emit("agent.message.sent", {
            "recipient": recipient, "message_id": message.message_id,
        })
        return True

    async def broadcast(self, message: Message, roles: list[str] = None):
        for agent_id in list(self._channels.keys()):
            agent = self.brain.agents.registry.get(agent_id)
            if agent and (roles is None or agent.role in roles):
                await self.send(agent_id, message)

    async def receive(self, agent_id: str, limit: int = 10) -> list[dict]:
        return (self._channels.get(agent_id) or [])[-limit:]

    def get_channel_size(self, agent_id: str) -> int:
        return len(self._channels.get(agent_id, []))
