"""Core data types for ArcanisMemory.

These types are intentionally framework-agnostic: they describe *what* a memory
is and *how* it is governed, without binding to any storage backend.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional
import uuid


MemoryID = str


class MemoryType(Enum):
    """The five memory types supported by ArcanisMemory."""

    SHORT_TERM = auto()
    LONG_TERM = auto()
    PROJECT = auto()
    KNOWLEDGE = auto()
    EVENT = auto()

    @classmethod
    def from_string(cls, value: str) -> "MemoryType":
        return cls[value.upper()]

    def to_string(self) -> str:
        return self.name


class MemoryScope(Enum):
    """Who a memory belongs to. Drives permission checks and isolation."""

    GLOBAL = auto()
    USER = auto()
    SESSION = auto()
    PROJECT = auto()

    @classmethod
    def from_string(cls, value: str) -> "MemoryScope":
        return cls[value.upper()]

    def to_string(self) -> str:
        return self.name


class MemoryImportance(Enum):
    """Coarse-grained importance band used for ranking and forgetting."""

    TRIVIAL = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_score(cls, score: float) -> "MemoryImportance":
        if score >= 0.9:
            return cls.CRITICAL
        if score >= 0.7:
            return cls.HIGH
        if score >= 0.45:
            return cls.MEDIUM
        if score >= 0.2:
            return cls.LOW
        return cls.TRIVIAL


class PermissionLevel(Enum):
    """Action a principal may perform on a scope's memories."""

    NONE = auto()
    READ = auto()
    WRITE = auto()
    FORGET = auto()
    ADMIN = auto()

    @classmethod
    def from_string(cls, value: str) -> "PermissionLevel":
        return cls[value.upper()]

    def to_string(self) -> str:
        return self.name

    def implies(self, other: "PermissionLevel") -> bool:
        order = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.FORGET: 2,
            PermissionLevel.ADMIN: 3,
        }
        return order[self] >= order[other]


class RelationType(Enum):
    """How two memories relate. Surfaced to ArcanisKnowledgeGraph."""

    RELATED = auto()
    CAUSES = auto()
    CONTRADICTS = auto()
    SUPPORTS = auto()
    PART_OF = auto()
    SIMILAR = auto()

    @classmethod
    def from_string(cls, value: str) -> "RelationType":
        return cls[value.upper()]

    def to_string(self) -> str:
        return self.name


@dataclass
class Memory:
    """A single stored memory.

    A memory is content plus the governance metadata required to store,
    retrieve, rank, and eventually forget it.
    """

    content: str
    memory_type: MemoryType = MemoryType.LONG_TERM
    memory_id: MemoryID = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str = "anonymous"
    scope: MemoryScope = MemoryScope.USER
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    embedding: Optional[list[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    encrypted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    # --- Convenience accessors -------------------------------------------------

    @property
    def importance_band(self) -> MemoryImportance:
        return MemoryImportance.from_score(self.importance)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        now = now or datetime.utcnow()
        return now >= self.expires_at

    def touch(self, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        self.last_accessed = now
        self.access_count += 1
        self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type.to_string(),
            "user_id": self.user_id,
            "scope": self.scope.to_string(),
            "project_id": self.project_id,
            "session_id": self.session_id,
            "tags": list(self.tags),
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "encrypted": self.encrypted,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Memory":
        def _dt(value: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(value) if value else None

        return cls(
            content=data["content"],
            memory_type=MemoryType.from_string(data["memory_type"]),
            memory_id=data.get("memory_id") or uuid.uuid4().hex,
            user_id=data.get("user_id", "anonymous"),
            scope=MemoryScope.from_string(data.get("scope", "USER")),
            project_id=data.get("project_id"),
            session_id=data.get("session_id"),
            tags=list(data.get("tags", [])),
            importance=float(data.get("importance", 0.5)),
            created_at=_dt(data.get("created_at")) or datetime.utcnow(),
            updated_at=_dt(data.get("updated_at")) or datetime.utcnow(),
            expires_at=_dt(data.get("expires_at")),
            last_accessed=_dt(data.get("last_accessed")) or datetime.utcnow(),
            access_count=int(data.get("access_count", 0)),
            encrypted=bool(data.get("encrypted", False)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class Permission:
    """A grant of a permission level over a scope, for a principal."""

    resource: str
    level: PermissionLevel
    principal_id: str
    granted: bool = True
    reason: Optional[str] = None

    def allows(self, required: PermissionLevel) -> bool:
        if not self.granted:
            return False
        return self.level.implies(required)


@dataclass
class MemoryRelation:
    """A directed relationship between two memories."""

    source_id: MemoryID
    target_id: MemoryID
    relation: RelationType = RelationType.RELATED
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.to_string(),
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRelation":
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation=RelationType.from_string(data.get("relation", "RELATED")),
            strength=float(data.get("strength", 1.0)),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
            metadata=dict(data.get("metadata", {})),
        )


def default_ttl(memory_type: MemoryType) -> Optional[timedelta]:
    """Sensible default lifetimes per memory type, used when none is given."""
    return {
        MemoryType.SHORT_TERM: timedelta(hours=1),
        MemoryType.LONG_TERM: None,
        MemoryType.PROJECT: None,
        MemoryType.KNOWLEDGE: None,
        MemoryType.EVENT: timedelta(days=365),
    }.get(memory_type, timedelta(days=30))
