"""Memory capabilities: store, retrieve, forget, organize, and rank.

These are the core verbs the :class:`MemoryEngine` exposes. They are grouped
into a :class:`MemoryManager` so the engine stays thin and the policy logic is
testable in isolation.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Iterable, Optional

from arcanis_memory.core.types import (
    Memory,
    MemoryID,
    MemoryRelation,
    MemoryScope,
    MemoryType,
    RelationType,
    default_ttl,
)
from arcanis_memory.storage.store import MemoryStore


_TAG_RE = re.compile(r"#(\w+)")


class MemoryManager:
    """Implements the five memory capabilities on top of a store."""

    def __init__(self, store: MemoryStore, config):
        self._store = store
        self.config = config

    # --- Store -----------------------------------------------------------------

    def store(
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
        embedding: Optional[list[float]] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> Memory:
        tags = list(tags or [])
        tags.extend(_TAG_RE.findall(content))

        expires_at: Optional[datetime] = None
        if ttl_seconds is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        elif memory_type in (MemoryType.SHORT_TERM, MemoryType.EVENT):
            ttl = default_ttl(memory_type)
            if ttl is not None:
                expires_at = datetime.utcnow() + ttl

        memory = Memory(
            content=content,
            memory_type=memory_type,
            user_id=user_id,
            scope=scope,
            project_id=project_id,
            session_id=session_id,
            tags=tags,
            importance=importance,
            embedding=embedding,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._store.insert(memory)
        return memory

    # --- Retrieve --------------------------------------------------------------

    def get(self, memory_id: MemoryID) -> Optional[Memory]:
        m = self._store.get(memory_id)
        if m is not None:
            m.touch()
            self._store.update(m)
        return m

    def recall(
        self,
        *,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Memory]:
        memories = self._store.query(
            user_id=user_id,
            memory_type=memory_type,
            tags=tags,
            project_id=project_id,
            limit=limit,
        )
        for m in memories:
            m.touch()
        if memories:
            for m in memories:
                self._store.update(m)
        return memories

    # --- Forget ----------------------------------------------------------------

    def forget(self, memory_id: MemoryID) -> bool:
        return self._store.delete(memory_id)

    def forget_expired(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.utcnow()
        count = 0
        for m in self._store.all():
            if m.is_expired(now):
                self._store.delete(m.memory_id)
                count += 1
        return count

    def forget_low_importance(self, threshold: float) -> int:
        count = 0
        for m in self._store.all():
            if m.importance < threshold:
                self._store.delete(m.memory_id)
                count += 1
        return count

    def purge_scope(self, user_id: str) -> int:
        count = 0
        for m in self._store.query(user_id=user_id, limit=10_000):
            self._store.delete(m.memory_id)
            count += 1
        return count

    # --- Organize --------------------------------------------------------------

    def tag(self, memory_id: MemoryID, tags: Iterable[str]) -> Optional[Memory]:
        m = self._store.get(memory_id)
        if m is None:
            return None
        m.tags = list(sorted(set(m.tags) | set(tags)))
        self._store.update(m)
        return m

    def untag(self, memory_id: MemoryID, tags: Iterable[str]) -> Optional[Memory]:
        m = self._store.get(memory_id)
        if m is None:
            return None
        remove = set(tags)
        m.tags = [t for t in m.tags if t not in remove]
        self._store.update(m)
        return m

    def relate(
        self,
        source_id: MemoryID,
        target_id: MemoryID,
        relation: RelationType = RelationType.RELATED,
        strength: float = 1.0,
    ) -> MemoryRelation:
        rel = MemoryRelation(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            strength=strength,
        )
        self._store.insert_relation(rel)
        return rel

    def relations(self, memory_id: MemoryID) -> list[MemoryRelation]:
        return self._store.relations_for(memory_id)

    # --- Rank ------------------------------------------------------------------

    def rank(
        self,
        memories: list[Memory],
        now: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list[tuple[Memory, float]]:
        now = now or datetime.utcnow()
        cfg = self.config
        total = cfg.weight_importance + cfg.weight_recency + cfg.weight_access
        if total <= 0:
            total = 1.0

        scored = []
        for m in memories:
            recency = _recency_score(m.updated_at, now)
            access = min(1.0, m.access_count / 10.0)
            score = (
                cfg.weight_importance * m.importance
                + cfg.weight_recency * recency
                + cfg.weight_access * access
            ) / total
            scored.append((m, round(score, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        if limit is not None:
            scored = scored[:limit]
        return scored


def _recency_score(updated_at: datetime, now: datetime) -> float:
    age_seconds = max(0.0, (now - updated_at).total_seconds())
    half_life = 86400.0 * 7.0
    return float(0.5 ** (age_seconds / half_life))
