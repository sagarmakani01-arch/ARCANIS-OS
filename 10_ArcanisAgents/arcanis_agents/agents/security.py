"""Security Agent — checks code for vulnerabilities."""

from __future__ import annotations

import re
from typing import Any, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import Message, MessageType

_PATTERNS = {
    "hardcoded_secret": re.compile(r"(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]"),
    "eval_usage": re.compile(r"\beval\s*\("),
    "shell_injection": re.compile(r"shell\s*=\s*True"),
    "exec_usage": re.compile(r"\bexec\s*\("),
    "sql_injection": re.compile(r"['\"].*%s.*['\"]"),
}


class SecurityAgent(Agent):
    role = "security"
    capabilities = {AgentCapability.SECURITY_SCAN}

    def __init__(self, name: str = "security", agent_id: Optional[str] = None) -> None:
        super().__init__(name, agent_id)

    async def handle(self, msg: Message) -> Optional[Message]:
        if msg.kind != "task.execute" or msg.msg_type is not MessageType.REQUEST:
            return None
        data = msg.payload or {}
        task_id = data.get("task_id")
        payload = data.get("data") or {}
        if not isinstance(payload, dict):
            payload = {}

        code = payload.get("code", "")
        if code:
            result = self._scan(code, task_id)
        else:
            result = {"action": "scan", "agent": self.name, "task_id": task_id, "severity": "none", "vulnerabilities": []}

        if task_id is not None:
            self.ctx.memory.set("tasks", task_id, result, owner=self.agent_id)
        return self.ctx.bus.reply(msg, self.agent_id, result)

    def _scan(self, code: str, task_id: str) -> dict:
        vulns = []
        for name, pattern in _PATTERNS.items():
            for line_no, line in enumerate(code.splitlines(), 1):
                if pattern.search(line):
                    vulns.append({"rule": name, "line": line_no, "severity": "high"})
        severity = "high" if vulns else "low"
        return {
            "action": "scan", "agent": self.name, "task_id": task_id,
            "severity": severity, "vulnerabilities": vulns,
        }
