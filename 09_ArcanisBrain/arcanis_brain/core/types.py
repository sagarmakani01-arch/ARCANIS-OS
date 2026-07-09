from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum, auto
from datetime import datetime, timezone
import uuid


class MessageRole(Enum):
    SYSTEM = auto()
    USER = auto()
    AGENT = auto()
    TOOL = auto()


class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    DELEGATED = auto()
    CANCELLED = auto()


class MemoryType(Enum):
    EPISODIC = auto()
    SEMANTIC = auto()
    PROCEDURAL = auto()


class PermissionLevel(Enum):
    NONE = auto()
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    ADMIN = auto()


@dataclass
class Message:
    role: MessageRole
    content: str
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class Task:
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    objective: str = ""
    status: TaskStatus = TaskStatus.PENDING
    parent_id: Optional[str] = None
    subtasks: list[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    required_tools: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


@dataclass
class AgentIdentity:
    agent_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    role: str = ""
    capabilities: list[str] = field(default_factory=list)
    system_prompt: str = ""
    permission_level: PermissionLevel = PermissionLevel.READ
    parent_id: Optional[str] = None


@dataclass
class Context:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str = "anonymous"
    conversation_history: list[Message] = field(default_factory=list)
    active_task: Optional[Task] = None
    agent_chain: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryItem:
    content: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    key: str = field(default_factory=lambda: uuid.uuid4().hex)
    agent_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    embedding: Optional[list[float]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    access_count: int = 0


@dataclass
class ReasoningTrace:
    task_id: str
    steps: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    alternatives_considered: list[str] = field(default_factory=list)
    final_conclusion: Optional[str] = None
    confidence: float = 0.0
    duration_ms: float = 0.0


@dataclass
class Permission:
    resource: str
    level: PermissionLevel
    agent_id: str
    granted: bool = False
    reason: Optional[str] = None
