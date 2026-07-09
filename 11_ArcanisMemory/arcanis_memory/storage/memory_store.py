"""In-memory implementation of :class:`MemoryStore`.

Used for tests and ephemeral sessions. Mirrors the behavior of the database
store but keeps everything in Python data structures. Semantic search is
performed with a cosine similarity over in-memory embeddings.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional

import numpy as np

from arcanis_memory.core.types import Memory, MemoryID, MemoryRelation, MemoryType
from arcanis_memory.storage.store import MemoryStore


class InMemoryStore(MemoryStore):
    """A volatile, process-local memory store."""

    def __init__(self) -> None:
        self._memories: dict[MemoryID, Memory] = {}
        self._relations: dict[MemoryID, list[MemoryRelation]] = defaultdict(list)
        self._vectors: dict[MemoryID, list[float]] = {}

    def insert(self, memory: Memory) -> MemoryID:
        self._memories[memory.memory_id] = memory
        if memory.embedding is not None:
            self._vectors[memory.memory_id] = memory.embedding
        return memory.memory_id

    def get(self, memory_id: MemoryID) -> Optional[Memory]:
        return self._memories.get(memory_id)

    def update(self, memory: Memory) -> bool:
        if memory.memory_id not in self._memories:
            return False
        self._memories[memory.memory_id] = memory
        if memory.embedding is not None:
            self._vectors[memory.memory_id] = memory.embedding
        return True

    def delete(self, memory_id: MemoryID) -> bool:
        existed = memory_id in self._memories
        self._memories.pop(memory_id, None)
        self._vectors.pop(memory_id, None)
        self.delete_relations(memory_id)
        return existed

    def query(
        self,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        results = list(self._memories.values())
        if user_id is not None:
            results = [m for m in results if m.user_id == user_id]
        if memory_type is not None:
            results = [m for m in results if m.memory_type == memory_type]
        if project_id is not None:
            results = [m for m in results if m.project_id == project_id]
        if tags:
            wanted = set(tags)
            results = [m for m in results if wanted.intersection(m.tags)]
        results.sort(key=lambda m: m.importance, reverse=True)
        return results[offset : offset + limit]

    def all(self) -> list[Memory]:
        return list(self._memories.values())

    def count(self) -> int:
        return len(self._memories)

    def insert_relation(self, relation: MemoryRelation) -> None:
        self._relations[relation.source_id].append(relation)

    def relations_for(self, memory_id: MemoryID) -> list[MemoryRelation]:
        return list(self._relations.get(memory_id, []))

    def delete_relations(self, memory_id: MemoryID) -> None:
        self._relations.pop(memory_id, None)
        for key in list(self._relations.keys()):
            self._relations[key] = [
                r for r in self._relations[key] if r.target_id != memory_id
            ]

    # --- Local semantic search (used by AI module when no DB vector store) -----

    def semantic_search(
        self, query_vector: list[float], top_k: int = 5, metric: str = "cosine"
    ) -> list[tuple[MemoryID, float]]:
        if not self._vectors:
            return []
        q = np.array(query_vector, dtype=np.float64)
        scored = []
        for mid, vec in self._vectors.items():
            v = np.array(vec, dtype=np.float64)
            if metric == "cosine":
                denom = np.linalg.norm(q) * np.linalg.norm(v)
                score = float(np.dot(q, v) / denom) if denom > 0 else 0.0
            elif metric == "dot":
                score = float(np.dot(q, v))
            elif metric == "euclidean":
                score = -float(np.linalg.norm(v - q))
            else:
                raise ValueError(f"Unknown metric: {metric}")
            scored.append((mid, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
