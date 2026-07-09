"""10_ArcanisAgentSDK — Third-party agent development kit."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class AgentManifest:
    name: str = ""
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    entry_point: str = ""
    api_version: str = "1.0"


@dataclass
class AgentMessage:
    sender: str = ""
    receiver: str = ""
    content: Any = None
    msg_type: str = "request"
    timestamp: float = field(default_factory=time.time)
    msg_id: str = ""


@dataclass
class AgentResponse:
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentContext:
    def __init__(self, agent_name: str, capabilities: list[str]):
        self.agent_name = agent_name
        self.capabilities = capabilities
        self._shared_state: dict[str, Any] = {}

    def get_state(self, key: str) -> Any:
        return self._shared_state.get(key)

    def set_state(self, key: str, value: Any) -> None:
        self._shared_state[key] = value

    def log(self, message: str) -> None:
        pass


class BaseAgent:
    def __init__(self, manifest: AgentManifest):
        self.manifest = manifest
        self.context = AgentContext(manifest.name, manifest.capabilities)
        self._handlers: dict[str, Callable] = {}

    def on(self, message_type: str, handler: Callable[[AgentMessage], AgentResponse]) -> None:
        self._handlers[message_type] = handler

    def handle(self, message: AgentMessage) -> AgentResponse:
        handler = self._handlers.get(message.msg_type)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                return AgentResponse(success=False, error=str(e))
        return AgentResponse(success=False, error=f"No handler for {message.msg_type}")

    def send(self, bus: 'AgentBus', receiver: str, content: Any, msg_type: str = "request") -> Optional[AgentResponse]:
        msg = AgentMessage(sender=self.manifest.name, receiver=receiver,
                           content=content, msg_type=msg_type)
        return bus.dispatch(msg)


class AgentBus:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._message_log: list[AgentMessage] = []

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.manifest.name] = agent

    def unregister(self, name: str) -> bool:
        return self._agents.pop(name, None) is not None

    def dispatch(self, message: AgentMessage) -> AgentResponse:
        self._message_log.append(message)
        agent = self._agents.get(message.receiver)
        if not agent:
            return AgentResponse(success=False, error=f"Agent not found: {message.receiver}")
        return agent.handle(message)

    def broadcast(self, sender: str, content: Any, msg_type: str = "broadcast") -> dict[str, AgentResponse]:
        results: dict[str, AgentResponse] = {}
        for name, agent in self._agents.items():
            if name != sender:
                msg = AgentMessage(sender=sender, receiver=name, content=content, msg_type=msg_type)
                results[name] = agent.handle(msg)
        return results

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    def get_message_log(self, limit: int = 50) -> list[AgentMessage]:
        return self._message_log[-limit:]


class AgentSDK:
    def __init__(self):
        self.bus = AgentBus()
        self._manifests: dict[str, AgentManifest] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def register_agent(self, manifest: AgentManifest, agent_class: type) -> BaseAgent:
        self._manifests[manifest.name] = manifest
        agent = agent_class(manifest)
        self.bus.register(agent)
        return agent

    def create_manifest(self, name: str, description: str, capabilities: list[str],
                        permissions: list[str] | None = None) -> AgentManifest:
        return AgentManifest(
            name=name, description=description,
            capabilities=capabilities, permissions=permissions or [],
        )

    def send_message(self, sender: str, receiver: str, content: Any) -> AgentResponse:
        msg = AgentMessage(sender=sender, receiver=receiver, content=content)
        return self.bus.dispatch(msg)

    def get_status(self) -> dict:
        return {
            "initialized": self._initialized,
            "registered_agents": len(self._manifests),
            "active_agents": len(self.bus.list_agents()),
            "agents": self.bus.list_agents(),
        }
