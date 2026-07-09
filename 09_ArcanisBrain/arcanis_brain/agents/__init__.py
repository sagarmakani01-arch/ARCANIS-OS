from arcanis_brain.agents.registry import AgentRegistry
from arcanis_brain.agents.communicator import AgentCommunicator
from arcanis_brain.agents.delegator import TaskDelegator
from arcanis_brain.agents.tools import ToolRegistry
from arcanis_brain.core.types import AgentIdentity, PermissionLevel


class AgentModule:
    def __init__(self, brain):
        self.brain = brain
        self.registry = AgentRegistry(brain)
        self.communicator = AgentCommunicator(brain)
        self.delegator = TaskDelegator(brain)
        self.tools = ToolRegistry(brain)

    async def initialize(self):
        self._register_default_agents()

    def _register_default_agents(self):
        self.registry.register(AgentIdentity(
            name="assistant", role="general_assistant",
            capabilities=["reason", "search", "compose"],
            permission_level=PermissionLevel.WRITE,
        ))
        self.registry.register(AgentIdentity(
            name="researcher", role="research",
            capabilities=["search", "analyze", "summarize"],
            permission_level=PermissionLevel.READ,
        ))
        self.registry.register(AgentIdentity(
            name="coder", role="code_generation",
            capabilities=["read", "write", "execute"],
            permission_level=PermissionLevel.WRITE,
        ))

    async def select_agent(self, step: dict) -> AgentIdentity:
        tool_needed = step.get("tool", "reason")
        return self.registry.select_for_tool(tool_needed)

    async def execute(self, agent: AgentIdentity, step: dict, context) -> "Task":
        return await self.delegator.execute(agent, step, context)

    async def shutdown(self):
        pass


__all__ = ["AgentModule", "AgentRegistry", "AgentCommunicator", "TaskDelegator", "ToolRegistry"]
