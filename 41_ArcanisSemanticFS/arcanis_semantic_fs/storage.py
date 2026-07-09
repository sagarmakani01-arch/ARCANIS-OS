from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class FileEntity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    name: str = ""
    content_type: str = ""
    size: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    summary: str = ""
    intent: str = ""
    tags: list[str] = field(default_factory=list)
    embedding: Optional[list[float]] = None
    depends_on: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    source_id: str
    target_id: str
    rel_type: str
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MetadataStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                content_type TEXT,
                size INTEGER,
                created_at TEXT,
                modified_at TEXT,
                summary TEXT,
                intent TEXT,
                tags TEXT
            );
            CREATE TABLE IF NOT EXISTS relationships (
                source_id TEXT,
                target_id TEXT,
                type TEXT,
                confidence REAL,
                created_at TEXT,
                PRIMARY KEY (source_id, target_id, type)
            );
            CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
            CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);
            CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id);
            CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id);
        """)
        self.conn.commit()

    def upsert_file(self, entity: FileEntity) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO files
            (id, path, name, content_type, size, created_at, modified_at, summary, intent, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity.id, entity.path, entity.name, entity.content_type,
              entity.size, entity.created_at, entity.modified_at,
              entity.summary, entity.intent, json.dumps(entity.tags)))
        self.conn.commit()

    def get_file(self, file_id: str) -> Optional[FileEntity]:
        row = self.conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        if not row:
            return None
        return self._row_to_entity(row)

    def get_file_by_path(self, path: str) -> Optional[FileEntity]:
        row = self.conn.execute("SELECT * FROM files WHERE path = ?", (path,)).fetchone()
        if not row:
            return None
        return self._row_to_entity(row)

    def search_files(self, query: str, limit: int = 20) -> list[FileEntity]:
        rows = self.conn.execute(
            "SELECT * FROM files WHERE name LIKE ? OR summary LIKE ? OR tags LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def get_all_files(self) -> list[FileEntity]:
        rows = self.conn.execute("SELECT * FROM files").fetchall()
        return [self._row_to_entity(r) for r in rows]

    def delete_file(self, file_id: str) -> bool:
        cursor = self.conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def add_relationship(self, rel: Relationship) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO relationships
            (source_id, target_id, type, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (rel.source_id, rel.target_id, rel.rel_type, rel.confidence, rel.created_at))
        self.conn.commit()

    def get_related(self, file_id: str) -> list[FileEntity]:
        rows = self.conn.execute("""
            SELECT f.* FROM files f
            JOIN relationships r ON f.id = r.target_id
            WHERE r.source_id = ?
            ORDER BY r.confidence DESC
        """, (file_id,)).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def get_dependencies(self, file_id: str) -> list[FileEntity]:
        rows = self.conn.execute("""
            SELECT f.* FROM files f
            JOIN relationships r ON f.id = r.target_id
            WHERE r.source_id = ? AND r.type = 'depends_on'
        """, (file_id,)).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def get_stats(self) -> dict[str, Any]:
        file_count = self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        rel_count = self.conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        return {"files": file_count, "relationships": rel_count}

    def _row_to_entity(self, row: sqlite3.Row) -> FileEntity:
        return FileEntity(
            id=row["id"], path=row["path"], name=row["name"],
            content_type=row["content_type"], size=row["size"],
            created_at=row["created_at"], modified_at=row["modified_at"],
            summary=row["summary"], intent=row["intent"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )

    def close(self):
        self.conn.close()
