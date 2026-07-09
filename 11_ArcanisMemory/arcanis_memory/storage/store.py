"""Storage abstraction for ArcanisMemory.

The :class:`MemoryStore` interface is the only thing the memory engine talks to
for persistence. The default implementation (:class:`DatabaseBackedStore`)
delegates to ArcanisDatabase, using its structured store for memory records,
its vector store + embedding store for semantic search, and its key-value store
for relationships and metadata.
"""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from arcanis_memory.core.types import Memory, MemoryID, MemoryRelation, MemoryType


class MemoryStore(ABC):
    """Abstract persistence contract for memories."""

    @abstractmethod
    def insert(self, memory: Memory) -> MemoryID: ...

    @abstractmethod
    def get(self, memory_id: MemoryID) -> Optional[Memory]: ...

    @abstractmethod
    def update(self, memory: Memory) -> bool: ...

    @abstractmethod
    def delete(self, memory_id: MemoryID) -> bool: ...

    @abstractmethod
    def query(
        self,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]: ...

    @abstractmethod
    def all(self) -> list[Memory]: ...

    @abstractmethod
    def insert_relation(self, relation: MemoryRelation) -> None: ...

    @abstractmethod
    def relations_for(self, memory_id: MemoryID) -> list[MemoryRelation]: ...

    @abstractmethod
    def delete_relations(self, memory_id: MemoryID) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


_COLLECTION = "memories"


class DatabaseBackedStore(MemoryStore):
    """Persistence backed by ArcanisDatabase."""

    def __init__(self, db):
        self.db = db
        self._init_schema()

    def _init_schema(self) -> None:
        conn = self.db.conn
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _arcanis_memory (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                project_id TEXT,
                session_id TEXT,
                tags TEXT NOT NULL DEFAULT '[]',
                importance REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                last_accessed TEXT NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                encrypted INTEGER NOT NULL DEFAULT 0,
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_user ON _arcanis_memory(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_type ON _arcanis_memory(memory_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_project ON _arcanis_memory(project_id)"
        )
        conn.commit()

    # --- Memories ---------------------------------------------------------------

    def insert(self, memory: Memory) -> MemoryID:
        conn = self.db.conn
        conn.execute(
            """
            INSERT OR REPLACE INTO _arcanis_memory (
                memory_id, content, memory_type, user_id, scope, project_id,
                session_id, tags, importance, created_at, updated_at,
                expires_at, last_accessed, access_count, encrypted, metadata
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                memory.memory_id,
                memory.content,
                memory.memory_type.to_string(),
                memory.user_id,
                memory.scope.to_string(),
                memory.project_id,
                memory.session_id,
                json.dumps(memory.tags),
                memory.importance,
                memory.created_at.isoformat(),
                memory.updated_at.isoformat(),
                memory.expires_at.isoformat() if memory.expires_at else None,
                memory.last_accessed.isoformat(),
                memory.access_count,
                int(memory.encrypted),
                json.dumps(memory.metadata),
            ),
        )
        conn.commit()

        # Maintain a vector entry for semantic search when an embedding exists.
        self._sync_vector(memory)
        return memory.memory_id

    def _sync_vector(self, memory: Memory) -> None:
        if memory.embedding is None:
            return
        try:
            meta = {"memory_id": memory.memory_id, "type": memory.memory_type.to_string()}
            self.db.embeddings.store(_COLLECTION, memory.embedding, meta)
        except Exception:
            # Semantic search is best-effort; structured store is source of truth.
            pass

    def get(self, memory_id: MemoryID) -> Optional[Memory]:
        cur = self.db.conn.execute(
            "SELECT * FROM _arcanis_memory WHERE memory_id=?", (memory_id,)
        )
        row = cur.fetchone()
        return self._row_to_memory(row) if row else None

    def update(self, memory: Memory) -> bool:
        return self.insert(memory) is not None

    def delete(self, memory_id: MemoryID) -> bool:
        cur = self.db.conn.execute(
            "DELETE FROM _arcanis_memory WHERE memory_id=?", (memory_id,)
        )
        self.db.conn.commit()
        self.delete_relations(memory_id)
        # Best-effort vector cleanup is skipped; stale vectors are ignored by search.
        return cur.rowcount > 0

    def query(
        self,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        clauses = []
        params: list = []
        if user_id is not None:
            clauses.append("user_id=?")
            params.append(user_id)
        if memory_type is not None:
            clauses.append("memory_type=?")
            params.append(memory_type.to_string())
        if project_id is not None:
            clauses.append("project_id=?")
            params.append(project_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM _arcanis_memory{where} ORDER BY importance DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = self.db.conn.execute(sql, params)
        rows = cur.fetchall()
        results = [self._row_to_memory(r) for r in rows]
        if tags:
            wanted = set(tags)
            results = [m for m in results if wanted.intersection(m.tags)]
        return results

    def all(self) -> list[Memory]:
        cur = self.db.conn.execute("SELECT * FROM _arcanis_memory")
        return [self._row_to_memory(r) for r in cur.fetchall()]

    def count(self) -> int:
        cur = self.db.conn.execute("SELECT COUNT(*) as c FROM _arcanis_memory")
        return cur.fetchone()["c"]

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        return Memory(
            content=row["content"],
            memory_type=MemoryType.from_string(row["memory_type"]),
            memory_id=row["memory_id"],
            user_id=row["user_id"],
            scope=__import__("arcanis_memory.core.types", fromlist=["MemoryScope"]).MemoryScope.from_string(row["scope"]),
            project_id=row["project_id"],
            session_id=row["session_id"],
            tags=json.loads(row["tags"]),
            importance=row["importance"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
            expires_at=_parse_dt(row["expires_at"]) if row["expires_at"] else None,
            last_accessed=_parse_dt(row["last_accessed"]),
            access_count=row["access_count"],
            encrypted=bool(row["encrypted"]),
            metadata=json.loads(row["metadata"]),
        )

    # --- Relations --------------------------------------------------------------

    def insert_relation(self, relation: MemoryRelation) -> None:
        self.db.kv.set(
            "memory_relations",
            f"{relation.source_id}:{relation.target_id}:{relation.relation.to_string()}",
            relation.to_dict(),
        )

    def relations_for(self, memory_id: MemoryID) -> list[MemoryRelation]:
        out: list[MemoryRelation] = []
        for key in self.db.kv.list_keys("memory_relations"):
            if key.startswith(f"{memory_id}:"):
                data = self.db.kv.get("memory_relations", key)
                if data:
                    out.append(MemoryRelation.from_dict(data))
        return out

    def delete_relations(self, memory_id: MemoryID) -> None:
        for key in self.db.kv.list_keys("memory_relations"):
            if key.startswith(f"{memory_id}:") or key.endswith(f":{memory_id}"):
                self.db.kv.delete("memory_relations", key)


def _parse_dt(value: Optional[str]):
    from datetime import datetime

    return datetime.fromisoformat(value) if value else None
