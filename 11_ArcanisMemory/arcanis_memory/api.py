"""Public Python API for ArcanisMemory.

Mirrors the ergonomic style of ``arcanisdb.api.python_api.ArcanisAPI`` so that
consumers already familiar with the database API feel at home. The API is a thin
async wrapper around :class:`MemoryEngine`, with convenience sync helpers.
"""

from __future__ import annotations

from typing import Iterable, Optional

from arcanis_memory.config import MemoryConfig
from arcanis_memory.core.engine import MemoryEngine
from arcanis_memory.core.types import (
    Memory,
    MemoryType,
    MemoryScope,
    PermissionLevel,
    RelationType,
)


class MemoryAPI:
    """High-level, user-facing API for the ArcanisMemory layer."""

    def __init__(self, config: Optional[MemoryConfig] = None, store=None):
        self.engine = MemoryEngine(config, store)

    # --- Lifecycle -------------------------------------------------------------

    async def initialize(self) -> None:
        await self.engine.initialize()

    async def maintenance(self) -> dict:
        return await self.engine.maintenance()

    async def shutdown(self) -> None:
        await self.engine.shutdown()

    # --- Store -----------------------------------------------------------------

    async def store(
        self,
        content: str,
        memory_type: str = "LONG_TERM",
        *,
        user_id: str = "anonymous",
        scope: str = "USER",
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        importance: float = 0.5,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> Memory:
        return await self.engine.store(
            content,
            MemoryType.from_string(memory_type),
            user_id=user_id,
            scope=MemoryScope.from_string(scope),
            project_id=project_id,
            session_id=session_id,
            tags=tags,
            importance=importance,
            ttl_seconds=ttl_seconds,
            metadata=metadata,
        )

    async def get(self, memory_id: str) -> Optional[Memory]:
        return await self.engine.get(memory_id)

    async def recall(
        self,
        *,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Memory]:
        mt = MemoryType.from_string(memory_type) if memory_type else None
        return await self.engine.recall(
            user_id=user_id,
            memory_type=mt,
            tags=tags,
            project_id=project_id,
            limit=limit,
        )

    async def search(self, query: str, *, user_id: Optional[str] = None,
                     memory_type: Optional[str] = None, top_k: int = 5) -> list[tuple[Memory, float]]:
        mt = MemoryType.from_string(memory_type) if memory_type else None
        return await self.engine.semantic_search(query, user_id=user_id, memory_type=mt, top_k=top_k)

    # --- Forget ----------------------------------------------------------------

    async def forget(self, memory_id: str) -> bool:
        return await self.engine.forget(memory_id)

    async def forget_expired(self) -> int:
        return await self.engine.forget_expired()

    async def purge_user(self, user_id: str) -> int:
        return await self.engine.purge_user(user_id)

    # --- Organize --------------------------------------------------------------

    async def tag(self, memory_id: str, tags: Iterable[str]) -> Optional[Memory]:
        return await self.engine.tag(memory_id, tags)

    async def relate(self, source_id: str, target_id: str,
                     relation: str = "RELATED", strength: float = 1.0) -> object:
        return await self.engine.relate(
            source_id, target_id, RelationType.from_string(relation), strength
        )

    async def relations(self, memory_id: str) -> list:
        return await self.engine.relations(memory_id)

    # --- AI --------------------------------------------------------------------

    async def build_context(self, query: str, *, user_id: Optional[str] = None,
                            project_id: Optional[str] = None, max_memories: int = 10) -> str:
        return await self.engine.build_context(
            query, user_id=user_id, project_id=project_id, max_memories=max_memories
        )

    async def summarize(self, memories: list[Memory], max_sentences: int = 3) -> str:
        return await self.engine.summarize(memories, max_sentences)

    # --- Security --------------------------------------------------------------

    def grant(self, principal_id: str, resource: str, level: str) -> object:
        return self.engine.grant(principal_id, resource, PermissionLevel.from_string(level))

    def revoke(self, principal_id: str, resource: str) -> None:
        self.engine.revoke(principal_id, resource)

    def is_encrypted(self) -> bool:
        return self.engine.is_encrypted()

    # --- System ----------------------------------------------------------------

    def info(self) -> dict:
        return self.engine.info()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.shutdown())
        except Exception:
            pass
