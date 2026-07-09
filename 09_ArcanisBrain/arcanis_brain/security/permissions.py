from typing import Optional
from arcanis_brain.core.types import Permission, PermissionLevel, AgentIdentity


class PermissionChecker:
    def __init__(self, brain):
        self.brain = brain
        self._blocked_patterns = [
            "ignore previous instructions",
            "you are now",
            "system prompt",
            "sudo",
            "rm -rf",
            "drop table",
            "delete from",
        ]

    def check_input_safety(self, user_input: str) -> Optional[str]:
        input_lower = user_input.lower()
        for pattern in self._blocked_patterns:
            if pattern in input_lower:
                return f"Input blocked: contains prohibited pattern '{pattern}'"

        dangerous_chars = [";", "|", "&", "`", "$("]
        for char in dangerous_chars:
            if char in user_input and len(user_input) > 200:
                return "Input blocked: dangerous characters detected in large input"

        return None

    def check_agent_permission(self, agent: AgentIdentity, step: dict) -> Permission:
        tool = step.get("tool", "")
        required = self._tool_permission(tool)
        granted = agent.permission_level.value >= required.value
        return Permission(
            resource=tool,
            level=required,
            agent_id=agent.agent_id,
            granted=granted,
            reason=None if granted else f"Agent '{agent.name}' lacks {required.name} permission for tool '{tool}'",
        )

    def _tool_permission(self, tool: str) -> PermissionLevel:
        dangerous = ["execute", "delete", "admin"]
        moderate = ["write", "update", "create", "modify"]
        if tool in dangerous:
            return PermissionLevel.EXECUTE
        if tool in moderate:
            return PermissionLevel.WRITE
        return PermissionLevel.READ

    def grant_permission(self, agent: AgentIdentity, level: PermissionLevel):
        agent.permission_level = level
        self.brain.event_bus.emit("permission.granted", {
            "agent_id": agent.agent_id, "level": level.name,
        })
