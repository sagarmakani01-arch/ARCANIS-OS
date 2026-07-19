import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from collections import defaultdict, deque
from threading import RLock


MEMORY_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".kernel")
MEMORY_DB_PATH = os.path.join(MEMORY_DB_DIR, "memory.db")


class MemoryStore:
    _instance = None
    _lock = RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir=None):
        if self._initialized:
            return
        self._initialized = True
        db_dir = data_dir or MEMORY_DB_DIR
        db_path = os.path.join(db_dir, "memory.db")
        os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()
        self._lock = RLock()
        self._short_term = deque(maxlen=100)
        self._working = {}

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                source TEXT DEFAULT 'system',
                confidence REAL DEFAULT 1.0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                target_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                relation_type TEXT NOT NULL DEFAULT 'related',
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT DEFAULT 'system',
                content TEXT NOT NULL,
                context TEXT DEFAULT '',
                memory_type TEXT DEFAULT 'general',
                importance REAL DEFAULT 0.5,
                access_level TEXT DEFAULT 'public',
                embedding BLOB,
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT
            );
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                episode_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                details TEXT DEFAULT '{}',
                outcome TEXT DEFAULT '',
                importance REAL DEFAULT 0.5,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS memory_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                keywords TEXT DEFAULT '',
                embedding BLOB,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS knowledge_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                snapshot TEXT NOT NULL,
                created_by TEXT DEFAULT 'system',
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(entity_type, entity_id, version)
            );
        """)
        self.conn.commit()

    # ── Short-term Memory ────────────────────────────────────
    def remember_short_term(self, agent_id, content):
        entry = {"agent": agent_id, "content": content, "time": time.time()}
        self._short_term.append(entry)
        return entry

    def recall_short_term(self, agent_id=None, limit=10):
        results = list(self._short_term)
        if agent_id:
            results = [r for r in results if r["agent"] == agent_id]
        return list(results)[-limit:]

    # ── Working Memory ────────────────────────────────────────
    def set_working(self, agent_id, key, value):
        if agent_id not in self._working:
            self._working[agent_id] = {}
        self._working[agent_id][key] = {"value": value, "updated": time.time()}

    def get_working(self, agent_id, key, default=None):
        store = self._working.get(agent_id, {})
        entry = store.get(key)
        if entry:
            return entry["value"]
        return default

    def clear_working(self, agent_id):
        self._working.pop(agent_id, None)

    # ── Long-term / Semantic Memory ───────────────────────────
    def store_semantic(self, agent_id, content, context="", memory_type="general",
                       importance=0.5, access_level="public"):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO semantic_memories (agent_id, content, context, memory_type, importance, access_level) "
                "VALUES (?,?,?,?,?,?)",
                (agent_id, content, context, memory_type, importance, access_level)
            )
            self.conn.commit()
            return c.lastrowid

    def recall_semantic(self, query="", memory_type="", agent_id="", limit=50):
        with self._lock:
            c = self.conn.cursor()
            conditions = []
            params = []
            if query:
                conditions.append("content LIKE ?")
                params.append(f"%{query}%")
            if memory_type:
                conditions.append("memory_type=?")
                params.append(memory_type)
            if agent_id:
                conditions.append("agent_id=?")
                params.append(agent_id)
            sql = "SELECT * FROM semantic_memories"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
            params.append(limit)
            c.execute(sql, params)
            return [dict(r) for r in c.fetchall()]

    # ── Episodic Memory ───────────────────────────────────────
    def store_episode(self, agent_id, episode_type, summary, details=None,
                      outcome="", importance=0.5):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO episodic_memories (agent_id, episode_type, summary, details, outcome, importance) "
                "VALUES (?,?,?,?,?,?)",
                (agent_id, episode_type, summary, json.dumps(details or {}), outcome, importance)
            )
            self.conn.commit()
            return c.lastrowid

    def recall_episodes(self, agent_id="", episode_type="", limit=50):
        with self._lock:
            c = self.conn.cursor()
            conditions = []
            params = []
            if agent_id:
                conditions.append("agent_id=?")
                params.append(agent_id)
            if episode_type:
                conditions.append("episode_type=?")
                params.append(episode_type)
            sql = "SELECT * FROM episodic_memories"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            c.execute(sql, params)
            return [dict(r) for r in c.fetchall()]

    # ── Knowledge Graph (Concepts & Relations) ────────────────
    def add_concept(self, name, description="", category="general", source="system"):
        with self._lock:
            try:
                c = self.conn.cursor()
                c.execute("INSERT OR IGNORE INTO concepts (name, description, category, source) VALUES (?,?,?,?)",
                         (name, description, category, source))
                self.conn.commit()
                return c.lastrowid
            except Exception:
                return None

    def get_concepts(self, search="", limit=50):
        with self._lock:
            c = self.conn.cursor()
            if search:
                c.execute("SELECT * FROM concepts WHERE name LIKE ? ORDER BY updated_at DESC LIMIT ?",
                         (f"%{search}%", limit))
            else:
                c.execute("SELECT * FROM concepts ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_concept_count(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]

    def add_relation(self, source, target, rel_type="related", weight=1.0):
        with self._lock:
            try:
                c = self.conn.cursor()
                c.execute("SELECT id FROM concepts WHERE name=?", (source,))
                s = c.fetchone()
                c.execute("SELECT id FROM concepts WHERE name=?", (target,))
                t = c.fetchone()
                if s and t:
                    c.execute("INSERT OR IGNORE INTO relations (source_id, target_id, relation_type, weight) VALUES (?,?,?,?)",
                             (s[0], t[0], rel_type, weight))
                    self.conn.commit()
                    return True
            except Exception:
                return False

    def get_relations(self, concept_name=""):
        with self._lock:
            c = self.conn.cursor()
            if concept_name:
                c.execute("""
                    SELECT r.*, s.name as source_name, t.name as target_name
                    FROM relations r
                    JOIN concepts s ON r.source_id = s.id
                    JOIN concepts t ON r.target_id = t.id
                    WHERE s.name=? OR t.name=?
                """, (concept_name, concept_name))
            else:
                c.execute("""
                    SELECT r.*, s.name as source_name, t.name as target_name
                    FROM relations r
                    JOIN concepts s ON r.source_id = s.id
                    JOIN concepts t ON r.target_id = t.id
                """)
            return [dict(r) for r in c.fetchall()]

    def get_relation_count(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    # ── Knowledge Versioning ──────────────────────────────────
    def snapshot_concept(self, concept_id, created_by="system"):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM concepts WHERE id=?", (concept_id,))
            concept = c.fetchone()
            if not concept:
                return None
            c.execute("SELECT MAX(version) FROM knowledge_versions WHERE entity_type='concept' AND entity_id=?",
                     (concept_id,))
            row = c.fetchone()
            version = (row[0] or 0) + 1
            c.execute(
                "INSERT INTO knowledge_versions (entity_type, entity_id, version, snapshot, created_by) VALUES (?,?,?,?,?)",
                ("concept", concept_id, version, json.dumps(dict(concept)), created_by)
            )
            self.conn.commit()
            return version

    def get_concept_history(self, concept_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT * FROM knowledge_versions WHERE entity_type='concept' AND entity_id=? ORDER BY version",
                (concept_id,)
            )
            return [dict(r) for r in c.fetchall()]

    # ── Shared / Organizational Memory ────────────────────────
    def get_organizational_stats(self):
        with self._lock:
            return {
                "concepts": self.get_concept_count(),
                "relations": self.get_relation_count(),
                "semantic_memories": self.conn.execute("SELECT COUNT(*) FROM semantic_memories").fetchone()[0],
                "episodic_memories": self.conn.execute("SELECT COUNT(*) FROM episodic_memories").fetchone()[0],
                "knowledge_versions": self.conn.execute("SELECT COUNT(*) FROM knowledge_versions").fetchone()[0],
            }

    def semantic_search(self, query, limit=10):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT * FROM semantic_memories WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
                (f"%{query}%", limit)
            )
            return [dict(r) for r in c.fetchall()]

    def search(self, query, limit=10):
        results = []
        with self._lock:
            c = self.conn.cursor()
            for table, type_name in [
                ("semantic_memories", "semantic"),
                ("episodic_memories", "episodic"),
            ]:
                try:
                    c.execute(
                        f"SELECT * FROM {table} WHERE content LIKE ? OR summary LIKE ? ORDER BY importance DESC LIMIT ?",
                        (f"%{query}%", f"%{query}%", limit)
                    )
                    for r in c.fetchall():
                        entry = dict(r)
                        entry["type"] = type_name
                        results.append(entry)
                except Exception:
                    pass
            concepts = self.get_concepts(search=query, limit=limit)
            for c_ in concepts:
                c_["type"] = "concept"
                results.append(c_)
        results.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return results[:limit]

    def close(self):
        self.conn.close()
