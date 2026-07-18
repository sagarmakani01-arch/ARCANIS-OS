import sqlite3
import os
import json
from datetime import datetime
from threading import Lock


DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".ecosystem")
DB_PATH = os.path.join(DB_DIR, "arcanis.db")


class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()
        self._lock = Lock()

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                target_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                relation_type TEXT NOT NULL DEFAULT 'related',
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(source_id, target_id, relation_type)
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL DEFAULT 'system',
                content TEXT NOT NULL,
                context TEXT DEFAULT '',
                level TEXT DEFAULT 'info',
                timestamp TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                priority TEXT DEFAULT 'medium',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                assignee TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT DEFAULT 'worker',
                status TEXT DEFAULT 'idle',
                capabilities TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now')),
                last_active TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS agent_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL REFERENCES agents(id),
                type TEXT DEFAULT 'log',
                content TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                timestamp TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS ecosystem_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
        self.conn.commit()

    # ── Concepts ──────────────────────────────────────────────
    def add_concept(self, name, description="", category="general"):
        with self._lock:
            try:
                c = self.conn.cursor()
                c.execute("INSERT OR IGNORE INTO concepts (name, description, category) VALUES (?, ?, ?)",
                         (name, description, category))
                self.conn.commit()
                return c.lastrowid
            except Exception as e:
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

    # ── Memories ──────────────────────────────────────────────
    def add_memory(self, content, source="system", context="", level="info"):
        with self._lock:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO memories (source, content, context, level) VALUES (?,?,?,?)",
                         (source, content, context, level))
                self.conn.commit()
                return c.lastrowid
            except Exception:
                return None

    def get_memories(self, limit=50):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_memory_count(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    # ── Projects ──────────────────────────────────────────────
    def add_project(self, name, description="", status="active", priority="medium"):
        with self._lock:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO projects (name, description, status, priority) VALUES (?,?,?,?)",
                         (name, description, status, priority))
                self.conn.commit()
                return c.lastrowid
            except Exception as e:
                return None

    def get_projects(self, status=""):
        with self._lock:
            c = self.conn.cursor()
            if status:
                c.execute("SELECT * FROM projects WHERE status=? ORDER BY updated_at DESC", (status,))
            else:
                c.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [dict(r) for r in c.fetchall()]

    def get_project_count(self, status=""):
        with self._lock:
            if status:
                return self.conn.execute("SELECT COUNT(*) FROM projects WHERE status=?", (status,)).fetchone()[0]
            return self.conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]

    def update_project(self, pid, **kw):
        with self._lock:
            sets = ", ".join(f"{k}=?" for k in kw)
            vals = list(kw.values()) + [pid]
            self.conn.execute(f"UPDATE projects SET {sets}, updated_at=datetime('now') WHERE id=?", vals)
            self.conn.commit()

    # ── Tasks ─────────────────────────────────────────────────
    def add_task(self, project_id, title, description="", priority="medium"):
        with self._lock:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO tasks (project_id, title, description, priority) VALUES (?,?,?,?)",
                         (project_id, title, description, priority))
                self.conn.commit()
                return c.lastrowid
            except Exception:
                return None

    def get_tasks(self, project_id=-1, status=""):
        with self._lock:
            c = self.conn.cursor()
            q = "SELECT * FROM tasks"
            params = []
            clauses = []
            if project_id >= 0:
                clauses.append("project_id=?")
                params.append(project_id)
            if status:
                clauses.append("status=?")
                params.append(status)
            if clauses:
                q += " WHERE " + " AND ".join(clauses)
            q += " ORDER BY updated_at DESC"
            c.execute(q, params)
            return [dict(r) for r in c.fetchall()]

    def get_task_count(self, status=""):
        with self._lock:
            if status:
                return self.conn.execute("SELECT COUNT(*) FROM tasks WHERE status=?", (status,)).fetchone()[0]
            return self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    def update_task(self, tid, **kw):
        with self._lock:
            sets = ", ".join(f"{k}=?" for k in kw)
            vals = list(kw.values()) + [tid]
            self.conn.execute(f"UPDATE tasks SET {sets}, updated_at=datetime('now') WHERE id=?", vals)
            self.conn.commit()

    # ── Agents ────────────────────────────────────────────────
    def add_agent(self, name, role="worker", capabilities=None):
        with self._lock:
            try:
                caps = json.dumps(capabilities or [])
                c = self.conn.cursor()
                c.execute("INSERT OR IGNORE INTO agents (name, role, capabilities) VALUES (?,?,?)",
                         (name, role, caps))
                self.conn.commit()
                return c.lastrowid
            except Exception:
                return None

    def get_agents(self, status=""):
        with self._lock:
            c = self.conn.cursor()
            if status:
                c.execute("SELECT * FROM agents WHERE status=? ORDER BY last_active DESC", (status,))
            else:
                c.execute("SELECT * FROM agents ORDER BY last_active DESC")
            return [dict(r) for r in c.fetchall()]

    def get_agent_count(self, status=""):
        with self._lock:
            if status:
                return self.conn.execute("SELECT COUNT(*) FROM agents WHERE status=?", (status,)).fetchone()[0]
            return self.conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]

    def update_agent_status(self, agent_id, status):
        with self._lock:
            self.conn.execute("UPDATE agents SET status=?, last_active=datetime('now') WHERE id=?", (status, agent_id))
            self.conn.commit()

    def add_agent_message(self, agent_id, type, content, payload=None):
        with self._lock:
            try:
                pl = json.dumps(payload or {})
                c = self.conn.cursor()
                c.execute("INSERT INTO agent_messages (agent_id, type, content, payload) VALUES (?,?,?,?)",
                         (agent_id, type, content, pl))
                self.conn.commit()
                return c.lastrowid
            except Exception:
                return None

    def get_agent_messages(self, agent_id=-1, limit=50):
        with self._lock:
            c = self.conn.cursor()
            if agent_id >= 0:
                c.execute("SELECT * FROM agent_messages WHERE agent_id=? ORDER BY timestamp DESC LIMIT ?", (agent_id, limit))
            else:
                c.execute("SELECT * FROM agent_messages ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(r) for r in c.fetchall()]

    # ── Ecosystem State ───────────────────────────────────────
    def set_state(self, key, value):
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO ecosystem_state (key, value, updated_at) VALUES (?,?,datetime('now'))",
                             (key, str(value)))
            self.conn.commit()

    def get_state(self, key, default=None):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT value FROM ecosystem_state WHERE key=?", (key,))
            r = c.fetchone()
            return r["value"] if r else default

    # ── Stats ─────────────────────────────────────────────────
    def get_stats(self):
        return {
            "concepts": self.get_concept_count(),
            "relations": self.conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0],
            "memories": self.get_memory_count(),
            "projects": self.get_project_count(),
            "tasks": self.get_task_count(),
            "tasks_pending": self.get_task_count("pending"),
            "agents": self.get_agent_count(),
            "agents_active": self.get_agent_count("active"),
        }

    def close(self):
        self.conn.close()
