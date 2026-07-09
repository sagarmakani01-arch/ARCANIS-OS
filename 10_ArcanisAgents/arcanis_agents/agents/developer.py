"""Developer Agent — writes, reviews, and debugs code."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import Message

logger = logging.getLogger("arcanis.agents.developer")

_DANGEROUS_PATTERNS = {
    "hardcoded_secret": re.compile(r"(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]"),
    "eval_usage": re.compile(r"\beval\s*\("),
    "shell_injection": re.compile(r"shell\s*=\s*True"),
}


class DeveloperAgent(Agent):
    role = "developer"
    capabilities = {AgentCapability.WRITE_CODE, AgentCapability.REVIEW_CODE, AgentCapability.DEBUG}

    def __init__(self, name: str = "developer", agent_id: Optional[str] = None) -> None:
        super().__init__(name, agent_id)

    async def handle(self, msg: Message) -> Optional[Message]:
        payload = msg.payload if isinstance(msg.payload, dict) else {}
        data = payload.get("data", {})
        if isinstance(data, dict) and "action" in data:
            action = data["action"]
        elif "action" in payload:
            action = payload["action"]
        else:
            action = payload.get("description", "write_code")
        code = data.get("code") if isinstance(data, dict) else None
        if code:
            result = self._review(code, action)
        else:
            result = {"action": action, "agent": self.name}
        return Message(sender=self.agent_id, receiver=msg.sender, kind="task.result", payload=result)

    def _review(self, code: str, action: str) -> dict:
        findings = []
        for name, pattern in _DANGEROUS_PATTERNS.items():
            for line_no, line in enumerate(code.splitlines(), 1):
                if pattern.search(line):
                    findings.append({"rule": name, "line": line_no})
        return {"action": action, "agent": self.name, "severity": "high" if findings else "low", "findings": findings}
