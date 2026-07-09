"""The :class:`MemoryEngine` facade.

This is the single entry point consumers (ArcanisBrain, scripts, tests) use.
It wires together the storage backend, capability manager, AI features, and
security policy, and exposes async-friendly verbs matching the project spec:

- store, retrieve, forget, organize, rank
- semantic search, context building, summarization, relationship detection
- user control, permissions, encryption
- integration with ArcanisDatabase / KnowledgeGraph / Brain
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Iterable, Optional

from arcanis_memory.ai.features import AIFeatures, Embedder
from arcanis_memory.config import MemoryConfig
from arcanis_memory.core.manager import MemoryManager
from arcanis_memory.core.types import (
    Memory,
    MemoryID,
    MemoryRelation,
    MemoryScope,
    MemoryType,
    PermissionLevel,
    RelationType,
)
from arcanis_memory.security.policy import MemorySecurity
from arcanis_memory.storage.store import DatabaseBackedStore, MemoryStore
from arcanis_memory.storage.memory_store import InMemoryStore


class MemoryEngine:
    """Top-level orchestrator for the ArcanisMemory layer."""

    def __init__(self, config: Optional[MemoryConfig] = None, store: Optional[MemoryStore] = None):
        self.config = config or MemoryConfig()
        if store is not None:
            self._store = store
        elif self.config.storage_backend == "arcanisdb":
            from arcanis_memory.integration.adapters import DatabaseAdapter

            self._db_adapter = DatabaseAdapter(
                path=self.config.storage_path,
                encryption_key=self.config.encryption_key,
            )
            self._store = self._db_adapter.store()
        else:
            self._store = InMemoryStore()

        self.manager = MemoryManager(self._store, self.config)
        self.embedder = Embedder(self.config.embedding_dim)
        self.ai = AIFeatures(self.manager, self.embedder)
        self.security = self._build_security()

    @property
    def store(self) -> MemoryStore:
        return self._store

    def _build_security(self) -> MemorySecurity:
        crypto = None
        if self.config.enable_encryption and self.config.encryption_key:
            try:
                from arcanisdb.system.crypto import CryptoEngine

                crypto = CryptoEngine(self.config.encryption_key)
            except Exception:
                crypto = None
        return MemorySecurity(
            crypto=crypto,
            default_level=PermissionLevel.WRITE if self.config.enable_encryption else PermissionLevel.ADMIN,
        )

    # --- Lifecycle -------------------------------------------------------------

    async def initialize(self) -> None:
        if self.config.auto_forget_expired:
            self.manager.forget_expired()
        # emit readiness through no-op; integration layer may hook event bus

    async def maintenance(self) -> dict:
        expired = 0
        if self.config.auto_forget_expired:
            expired = self.manager.forget_expired()
        low = 0
        if self.config.auto_forget_below_importance > 0:
            low = self.manager.forget_low_importance(
                self.config.auto_forget_below_importance
            )
        return {"forgotten_expired": expired, "forgotten_low_importance": low}

    async def shutdown(self) -> None:
        if hasattr(self, "_db_adapter"):
            self._db_adapter.close()

    # --- Store -----------------------------------------------------------------

    async def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        *,
        user_id: str = "anonymous",
        scope: MemoryScope = MemoryScope.USER,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        importance: float = 0.5,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
        embed: bool = True,
        principal_id: Optional[str] = None,
    ) -> Memory:
        principal_id = principal_id or user_id
        if not self.security.can_write(principal_id, scope, user_id):
            raise PermissionError(
                f"principal {principal_id} cannot write to scope {scope.to_string()}/{user_id}"
            )

        encrypted_content, was_encrypted = self.security.encrypt_content(content)
        embedding = self.embedder.embed(content) if embed else None

        memory = self.manager.store(
            encrypted_content,
            memory_type,
            user_id=user_id,
            scope=scope,
            project_id=project_id,
            session_id=session_id,
            tags=tags,
            importance=importance,
            embedding=embedding,
            ttl_seconds=ttl_seconds,
            metadata={**(metadata or {}), "_encrypted": was_encrypted},
        )
        memory.encrypted = was_encrypted

        if self.config.enable_relationship_detection:
            self.ai.auto_relate(memory)
        return self._decrypt(memory)

    # --- Retrieve --------------------------------------------------------------

    async def recall(
        self,
        *,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        principal_id: Optional[str] = None,
    ) -> list[Memory]:
        principal_id = principal_id or (user_id or "anonymous")
        scope = MemoryScope.PROJECT if project_id else MemoryScope.USER
        if not self.security.can_read(principal_id, scope, user_id or "anonymous"):
            raise PermissionError("read denied")
        memories = self.manager.recall(
            user_id=user_id,
            memory_type=memory_type,
            tags=tags,
            project_id=project_id,
            limit=limit,
        )
        return [self._decrypt(m) for m in memories]

    async def get(self, memory_id: MemoryID, principal_id: Optional[str] = None) -> Optional[Memory]:
        m = self.manager.get(memory_id)
        if m is None:
            return None
        principal_id = principal_id or m.user_id
        if not self.security.can_read(principal_id, m.scope, m.user_id):
            raise PermissionError("read denied")
        return self._decrypt(m)

    async def semantic_search(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[tuple[Memory, float]]:
        results = self.ai.search(
            query, user_id=user_id, memory_type=memory_type, top_k=top_k, min_score=min_score
        )
        return [(self._decrypt(m), s) for m, s in results]

    # --- Forget ----------------------------------------------------------------

    async def forget(self, memory_id: MemoryID, principal_id: Optional[str] = None) -> bool:
        m = self.manager.get(memory_id)
        if m is None:
            return False
        principal_id = principal_id or m.user_id
        if not self.security.can_forget(principal_id, m.scope, m.user_id):
            raise PermissionError("forget denied")
        return self.manager.forget(memory_id)

    async def forget_expired(self) -> int:
        return self.manager.forget_expired()

    async def purge_user(self, user_id: str, principal_id: Optional[str] = None) -> int:
        principal_id = principal_id or user_id
        if not self.security.can_forget(principal_id, MemoryScope.USER, user_id):
            raise PermissionError("forget denied")
        return self.manager.purge_scope(user_id)

    # --- Organize --------------------------------------------------------------

    async def tag(self, memory_id: MemoryID, tags: Iterable[str]) -> Optional[Memory]:
        m = self.manager.tag(memory_id, tags)
        return self._decrypt(m) if m else None

    async def relate(
        self,
        source_id: MemoryID,
        target_id: MemoryID,
        relation: RelationType = RelationType.RELATED,
        strength: float = 1.0,
    ) -> MemoryRelation:
        return self.manager.relate(source_id, target_id, relation, strength)

    async def relations(self, memory_id: MemoryID) -> list[MemoryRelation]:
        return self.manager.relations(memory_id)

    # --- Rank ------------------------------------------------------------------

    async def rank(self, memories: list[Memory], limit: Optional[int] = None) -> list[tuple[Memory, float]]:
        return self.manager.rank(memories, limit=limit)

    # --- AI features -----------------------------------------------------------

    async def build_context(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        max_memories: int = 10,
        max_tokens: int = 4000,
    ) -> str:
        return self.ai.build_context(
            query,
            user_id=user_id,
            project_id=project_id,
            max_memories=max_memories,
            max_tokens=max_tokens,
        )

    async def summarize(self, memories: list[Memory], max_sentences: int = 3) -> str:
        return self.ai.summarize([self._decrypt(m) for m in memories], max_sentences)

    async def detect_relationships(
        self, memory: Memory, candidates: Optional[list[Memory]] = None
    ) -> list[tuple[Memory, RelationType, float]]:
        return self.ai.detect_relationships(memory, candidates)

    # --- Security helpers ------------------------------------------------------

    def grant(self, principal_id: str, resource: str, level: PermissionLevel):
        return self.security.grant(principal_id, resource, level)

    def revoke(self, principal_id: str, resource: str):
        self.security.revoke(principal_id, resource)

    def is_encrypted(self) -> bool:
        return self.security.is_encrypted()

    # --- Internals -------------------------------------------------------------

    def _decrypt(self, memory: Memory) -> Memory:
        was_encrypted = memory.metadata.get("_encrypted", False)
        memory.content = self.security.decrypt_content(memory.content, was_encrypted)
        return memory

    # --- Convenience sync wrappers (for non-async callers) ---------------------

    def store_sync(self, *args, **kwargs) -> Memory:
        return asyncio.get_event_loop().run_until_complete(self.store(*args, **kwargs))

    def info(self) -> dict:
        return {
            "version": __import__("arcanis_memory").__version__,
            "memories": self._store.count(),
            "encrypted": self.is_encrypted(),
            "backend": type(self._store).__name__,
        }
