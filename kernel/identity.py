import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime


IDENTITY_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".kernel")
IDENTITY_DB_PATH = os.path.join(IDENTITY_DB_DIR, "identity.db")


class IdentityStore:
    _instance = None
    _lock = threading.RLock()

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
        db_dir = data_dir or IDENTITY_DB_DIR
        db_path = os.path.join(db_dir, "identity.db")
        os.makedirs(db_dir, exist_ok=True)
        import sqlite3
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()
        self._lock = threading.RLock()

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS identities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                entity_type TEXT NOT NULL DEFAULT 'agent',
                public_key TEXT DEFAULT '',
                fingerprint TEXT DEFAULT '',
                role TEXT DEFAULT 'worker',
                status TEXT DEFAULT 'active',
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                last_active TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_id TEXT NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
                resource TEXT NOT NULL,
                action TEXT NOT NULL,
                grant_type TEXT NOT NULL DEFAULT 'allow',
                conditions TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT
            );
            CREATE TABLE IF NOT EXISTS trust_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_id TEXT NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
                score REAL DEFAULT 0.5,
                dimension TEXT DEFAULT 'overall',
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(identity_id, dimension)
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                actor_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT DEFAULT '',
                result TEXT DEFAULT 'allowed',
                details TEXT DEFAULT '{}'
            );
        """)
        self.conn.commit()

    # ── Identity Management ──────────────────────────────────
    def create_identity(self, name, entity_type="agent", role="worker", metadata=None):
        with self._lock:
            c = self.conn.cursor()
            eid = str(uuid.uuid4())
            raw = f"{name}:{eid}:{time.time()}"
            fingerprint = hashlib.sha256(raw.encode()).hexdigest()[:16]
            try:
                c.execute(
                    "INSERT INTO identities (id, name, entity_type, fingerprint, role, metadata) VALUES (?,?,?,?,?,?)",
                    (eid, name, entity_type, fingerprint, role, json.dumps(metadata or {}))
                )
                self.conn.commit()
                self._audit("system", "identity.create", f"identity:{eid}", "allowed",
                           {"name": name, "type": entity_type})
                return {"id": eid, "name": name, "fingerprint": fingerprint}
            except Exception as e:
                return None

    def get_identity(self, identity_id):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM identities WHERE id=?", (identity_id,))
            r = c.fetchone()
            return dict(r) if r else None

    def get_identity_by_name(self, name):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM identities WHERE name=?", (name,))
            r = c.fetchone()
            return dict(r) if r else None

    def list_identities(self, entity_type="", status=""):
        with self._lock:
            c = self.conn.cursor()
            conditions = []
            params = []
            if entity_type:
                conditions.append("entity_type=?")
                params.append(entity_type)
            if status:
                conditions.append("status=?")
                params.append(status)
            sql = "SELECT * FROM identities"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC"
            c.execute(sql, params)
            return [dict(r) for r in c.fetchall()]

    def update_identity(self, identity_id, **kw):
        with self._lock:
            sets = ", ".join(f"{k}=?" for k in kw)
            vals = list(kw.values()) + [identity_id]
            self.conn.execute(f"UPDATE identities SET {sets}, last_active=datetime('now') WHERE id=?", vals)
            self.conn.commit()

    def deactivate_identity(self, identity_id):
        self.update_identity(identity_id, status="deactivated")
        self._audit("system", "identity.deactivate", f"identity:{identity_id}", "allowed")

    # ── Permission Management ────────────────────────────────
    def grant_permission(self, identity_id, resource, action,
                         grant_type="allow", conditions=None, expires_at=None):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO permissions (identity_id, resource, action, grant_type, conditions, expires_at) "
                "VALUES (?,?,?,?,?,?)",
                (identity_id, resource, action, grant_type, json.dumps(conditions or {}), expires_at or "")
            )
            self.conn.commit()
            self._audit("system", "permission.grant", resource, "allowed",
                       {"identity": identity_id, "action": action, "type": grant_type})
            return c.lastrowid

    def check_permission(self, identity_id, resource, action):
        with self._lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT * FROM permissions WHERE identity_id=? AND resource=? AND action=? AND grant_type='allow'",
                (identity_id, resource, action)
            )
            return c.fetchone() is not None

    def list_permissions(self, identity_id=""):
        with self._lock:
            c = self.conn.cursor()
            if identity_id:
                c.execute("SELECT * FROM permissions WHERE identity_id=?", (identity_id,))
            else:
                c.execute("SELECT * FROM permissions")
            return [dict(r) for r in c.fetchall()]

    def revoke_permission(self, perm_id):
        with self._lock:
            self.conn.execute("DELETE FROM permissions WHERE id=?", (perm_id,))
            self.conn.commit()

    # ── Trust Scoring ─────────────────────────────────────────
    def set_trust_score(self, identity_id, score, dimension="overall"):
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO trust_scores (identity_id, score, dimension, updated_at) VALUES (?,?,?,datetime('now'))",
                (identity_id, max(0.0, min(1.0, score)), dimension)
            )
            self.conn.commit()

    def get_trust_score(self, identity_id, dimension="overall"):
        with self._lock:
            c = self.conn.cursor()
            c.execute("SELECT score FROM trust_scores WHERE identity_id=? AND dimension=?",
                     (identity_id, dimension))
            r = c.fetchone()
            return r["score"] if r else 0.5

    # ── Audit Logging ─────────────────────────────────────────
    def _audit(self, actor_id, action, resource, result, details=None):
        try:
            self.conn.execute(
                "INSERT INTO audit_log (actor_id, action, resource, result, details) VALUES (?,?,?,?,?)",
                (actor_id, action, resource, result, json.dumps(details or {}))
            )
            self.conn.commit()
        except Exception:
            pass

    def log_access(self, actor_id, action, resource, result="allowed", details=None):
        self._audit(actor_id, action, resource, result, details)

    def get_audit_log(self, actor_id="", limit=100):
        with self._lock:
            c = self.conn.cursor()
            if actor_id:
                c.execute("SELECT * FROM audit_log WHERE actor_id=? ORDER BY timestamp DESC LIMIT ?",
                         (actor_id, limit))
            else:
                c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_stats(self):
        return {
            "identities": self.conn.execute("SELECT COUNT(*) FROM identities").fetchone()[0],
            "active": self.conn.execute("SELECT COUNT(*) FROM identities WHERE status='active'").fetchone()[0],
            "permissions": self.conn.execute("SELECT COUNT(*) FROM permissions").fetchone()[0],
            "audit_entries": self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0],
        }
