from typing import Any
from arcanis_brain.core.types import AgentIdentity


class SafeExecutor:
    def __init__(self, brain):
        self.brain = brain
        self._allowed_commands = ["read", "write", "search", "list", "analyze"]
        self._blocked_commands = ["rm", "del", "format", "shutdown", "reboot"]

    async def execute(self, agent: AgentIdentity, action: dict, context: Any) -> dict:
        tool = action.get("tool", "")
        if tool in self._blocked_commands:
            return {
                "status": "blocked",
                "error": f"Tool '{tool}' is not allowed in safe mode",
            }
        if tool not in self._allowed_commands and self.brain.config.safety_mode == "strict":
            if not await self._verify_agent(agent, tool):
                return {"status": "blocked", "error": f"Tool '{tool}' requires verification"}
        return {
            "status": "ok",
            "result": f"Executed {tool} safely",
            "agent": agent.name,
        }

    async def _verify_agent(self, agent: AgentIdentity, tool: str) -> bool:
        return agent.permission_level.value >= 3

    def is_action_safe(self, action: dict) -> bool:
        tool = action.get("tool", "")
        target = str(action.get("target", ""))
        if tool not in self._allowed_commands:
            return False
        if ".." in target or target.startswith("/"):
            return False
        return True
