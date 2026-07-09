"""ArcanisMemory — the memory layer for the Arcanis ecosystem.

ArcanisMemory gives agents (notably ArcanisBrain) the ability to remember
information, preferences, projects, and experiences. It defines five memory
types, a pluggable storage system, semantic AI capabilities, a security layer,
and integration adapters for ArcanisDatabase, ArcanisKnowledgeGraph and
ArcanisBrain.

Project ID: 11-memory
Layer: 3 (AI)
Status: Alpha
"""

from arcanis_memory.core.engine import MemoryEngine
from arcanis_memory.core.types import (
    Memory,
    MemoryID,
    MemoryType,
    MemoryScope,
    MemoryImportance,
    Permission,
    PermissionLevel,
    RelationType,
    MemoryRelation,
)
from arcanis_memory.config import MemoryConfig

__version__ = "0.1.0"

__all__ = [
    "MemoryEngine",
    "Memory",
    "MemoryID",
    "MemoryType",
    "MemoryScope",
    "MemoryImportance",
    "Permission",
    "PermissionLevel",
    "RelationType",
    "MemoryRelation",
    "MemoryConfig",
]
