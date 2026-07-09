from arcanis_brain.security.permissions import PermissionChecker
from arcanis_brain.security.sandbox import SafeExecutor
from arcanis_brain.security.audit import AuditLogger
from arcanis_brain.core.types import Permission, PermissionLevel


class CheckResult:
    def __init__(self, allowed: bool, message: str = ""):
        self.allowed = allowed
        self.message = message


class SecurityModule:
    def __init__(self, brain):
        self.brain = brain
        self.permissions = PermissionChecker(brain)
        self.sandbox = SafeExecutor(brain)
        self.audit = AuditLogger(brain)

    async def check_input(self, user_input: str, context) -> CheckResult:
        blocked = self.permissions.check_input_safety(user_input)
        if blocked:
            self.audit.log("input_blocked", {"input": user_input[:100], "reason": blocked})
            return CheckResult(False, blocked)
        return CheckResult(True)

    async def check_permission(self, agent, step: dict) -> Permission:
        return self.permissions.check_agent_permission(agent, step)

    async def execute_safe(self, agent, action: dict, context) -> dict:
        self.audit.log("action_executed", {
            "agent": agent.name if hasattr(agent, 'name') else str(agent),
            "action": action.get("tool", "unknown"),
        })
        return await self.sandbox.execute(agent, action, context)


__all__ = ["SecurityModule", "PermissionChecker", "SafeExecutor", "AuditLogger"]
