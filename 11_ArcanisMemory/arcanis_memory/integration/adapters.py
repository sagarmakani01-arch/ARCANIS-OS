"""Integration adapters for the rest of the Arcanis ecosystem.

- :class:`DatabaseAdapter` — opens an ArcanisDatabase and exposes it as the
  backing store for memories.
- :class:`KnowledgeGraphAdapter` — pushes memory relations into
  ArcanisKnowledgeGraph (used when that project is available).
- :class:`BrainAdapter` — bridges ArcanisBrain's ``store_interaction`` /
  ``get_relevant_context`` calls into the memory engine.
"""

from __future__ import annotations

from typing import Optional

from arcanis_memory.core.types import MemoryType, MemoryScope


class DatabaseAdapter:
    """Connects ArcanisMemory to an ArcanisDatabase instance."""

    def __init__(self, db=None, *, path: str = ":memory:", encryption_key: Optional[str] = None):
        if db is not None:
            self.db = db
        else:
            from arcanisdb import ArcanisDatabase

            self.db = ArcanisDatabase(path, encryption_key)

    def store(self) -> "DatabaseBackedStore":  # noqa: F821
        from arcanis_memory.storage.store import DatabaseBackedStore

        return DatabaseBackedStore(self.db)

    def info(self) -> dict:
        return self.db.info()

    def close(self) -> None:
        self.db.close()


class KnowledgeGraphAdapter:
    """Mirrors memory relations into ArcanisKnowledgeGraph.

    ArcanisKnowledgeGraph (project 08) is not yet implemented, so this adapter
    degrades gracefully: it stores relations in an internal log and emits an
    event through the provided callback. When the graph becomes available,
    replace :meth:`_push` with a call to the graph's edge API.
    """

    def __init__(self, graph=None, on_sync=None):
        self.graph = graph
        self.on_sync = on_sync
        self._log: list[dict] = []

    def sync_relation(self, source_id: str, target_id: str, relation: str, strength: float) -> dict:
        edge = {
            "source": source_id,
            "target": target_id,
            "type": relation,
            "weight": strength,
        }
        if self.graph is not None:
            self.graph.add_edge(source_id, target_id, relation, weight=strength)
        else:
            self._log.append(edge)
        if self.on_sync:
            self.on_sync(edge)
        return edge

    def sync_memories(self, relations: list) -> list[dict]:
        """Push a batch of :class:`MemoryRelation` objects to the graph."""
        pushed = []
        for rel in relations:
            pushed.append(
                self.sync_relation(
                    rel.source_id, rel.target_id, rel.relation.to_string(), rel.strength
                )
            )
        return pushed

    def pending(self) -> list[dict]:
        return list(self._log)


class BrainAdapter:
    """Bridges ArcanisBrain memory calls into the memory engine.

    ArcanisBrain defines ``store_interaction`` and ``get_relevant_context`` on
    its :class:`MemoryModule`. This adapter implements the same contract so the
    brain can delegate to ArcanisMemory instead of maintaining its own store.
    """

    def __init__(self, engine):
        self.engine = engine

    async def store_interaction(
        self, user_input: str, response: str, user_id: str = "anonymous"
    ) -> None:
        await self.engine.store(
            content=f"User: {user_input}\nAssistant: {response}",
            memory_type=MemoryType.SHORT_TERM,
            user_id=user_id,
            tags=["interaction"],
            importance=0.4,
        )
        # Persist a long-term event memory for significant exchanges.
        await self.engine.store(
            content=response,
            memory_type=MemoryType.EVENT,
            user_id=user_id,
            tags=["response"],
            importance=0.5,
        )

    async def get_relevant_context(self, query: str, user_id: str = "anonymous") -> str:
        return await self.engine.build_context(query, user_id=user_id)

    async def persist(self) -> None:
        await self.engine.maintenance()

    async def initialize(self) -> None:
        await self.engine.initialize()
