"""Research Agent — finds information and summarizes knowledge."""

from __future__ import annotations

import re
from typing import Any, Optional

from ..core.agent import Agent, AgentCapability
from ..core.message_bus import Message, MessageType


class ResearchAgent(Agent):
    role = "research"
    capabilities = {AgentCapability.RESEARCH, AgentCapability.SUMMARIZE}

    def __init__(self, name: str = "research", agent_id: Optional[str] = None) -> None:
        super().__init__(name, agent_id)

    async def handle(self, msg: Message) -> Optional[Message]:
        if msg.msg_type is not MessageType.REQUEST:
            return None
        data = msg.payload or {}
        task_id = data.get("task_id")
        payload = data.get("data") or data if isinstance(data, dict) else {}
        if not isinstance(payload, dict):
            payload = {}

        text = payload.get("text", "")
        if text:
            result = self._summarize(text, task_id)
        else:
            query = payload.get("query", data.get("description", ""))
            result = {"action": "research", "agent": self.name, "task_id": task_id, "query": query}

        if task_id is not None:
            self.ctx.memory.set("tasks", task_id, result, owner=self.agent_id)
        return self.ctx.bus.reply(msg, self.agent_id, result)

    def _summarize(self, text: str, task_id: str) -> dict:
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
        seen: set[str] = set()
        unique: list[str] = []
        for s in sentences:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        summary = ". ".join(unique[:3]) + "." if unique else ""
        return {
            "action": "summarize", "agent": self.name, "task_id": task_id,
            "summary": summary, "word_count": len(text.split()),
        }
