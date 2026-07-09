"""ArcanisAgents — multi-agent collaboration framework.

Build specialized AI agents that communicate, delegate tasks, share memory,
and enforce permissions.
"""

from __future__ import annotations

from .core.agent import Agent, AgentState, AgentCapability
from .core.message_bus import MessageBus, Message, MessageType
from .core.shared_memory import SharedMemory, MemoryScope
from .core.permissions import PermissionSystem, Permission, Role
from .core.orchestrator import Orchestrator, Task, TaskStatus
from .core.factory import AgentFactory, AgentSpec, Behavior
from .agents.developer import DeveloperAgent
from .agents.research import ResearchAgent
from .agents.automation import AutomationAgent
from .agents.security import SecurityAgent
from .agents.system import SystemAgent
from .api import API

__version__ = "0.1.0"

__all__ = [
    "Agent", "AgentState", "AgentCapability",
    "MessageBus", "Message", "MessageType",
    "SharedMemory", "MemoryScope",
    "PermissionSystem", "Permission", "Role",
    "Orchestrator", "Task", "TaskStatus",
    "AgentFactory", "AgentSpec", "Behavior",
    "DeveloperAgent", "ResearchAgent", "AutomationAgent",
    "SecurityAgent", "SystemAgent",
    "API", "__version__",
]
