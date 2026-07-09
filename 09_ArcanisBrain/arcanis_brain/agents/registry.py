from typing import Optional
from arcanis_brain.core.types import AgentIdentity


class AgentRegistry:
    def __init__(self, brain):
        self.brain = brain
        self._agents: dict[str, AgentIdentity] = {}

    def register(self, agent: AgentIdentity):
        self._agents[agent.name] = agent
        self.brain.event_bus.emit("agent.registered", agent)

    def unregister(self, name: str):
        return self._agents.pop(name, None)

    def get(self, name: str) -> Optional[AgentIdentity]:
        return self._agents.get(name)

    def list(self) -> list[AgentIdentity]:
        return list(self._agents.values())

    def select_for_tool(self, tool: str) -> AgentIdentity:
        for agent in self._agents.values():
            if tool in agent.capabilities:
                return agent
        return self._agents.get("assistant", AgentIdentity(name="assistant"))

    def find_by_capability(self, capability: str) -> list[AgentIdentity]:
        return [a for a in self._agents.values() if capability in a.capabilities]
