import sqlite3
import os
import json
import threading
from pathlib import Path
from typing import Optional, Any

from arcanisdb.storage.structured import StructuredStore
from arcanisdb.storage.kvstore import KeyValueStore
from arcanisdb.storage.vectorstore import VectorStore
from arcanisdb.storage.metadatastore import MetadataStore
from arcanisdb.ai.embeddings import EmbeddingStore
from arcanisdb.ai.similarity import SimilaritySearch
from arcanisdb.ai.retrieval import KnowledgeRetriever
from arcanisdb.query.executor import QueryExecutor
from arcanisdb.system.indexing import IndexManager
from arcanisdb.system.backup import BackupManager
from arcanisdb.system.crypto import CryptoEngine


class ArcanisDatabase:
    def __init__(self, path: str = ":memory:", encryption_key: Optional[str] = None):
        self.path = str(Path(path).resolve()) if path != ":memory:" else ":memory:"
        self._local = threading.local()
        self._lock = threading.Lock()

        if path != ":memory:":
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)

        self.crypto = CryptoEngine(encryption_key) if encryption_key else None
        self._init_schema()

        self.structured = StructuredStore(self)
        self.kv = KeyValueStore(self)
        self.vectors = VectorStore(self)
        self.metadata = MetadataStore(self)
        self.embeddings = EmbeddingStore(self)
        self.similarity = SimilaritySearch(self)
        self.retrieval = KnowledgeRetriever(self)
        self.indexes = IndexManager(self)
        self.backup = BackupManager(self)
        self.query = QueryExecutor(self)

    @property
    def conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_schema(self):
        c = self.conn
        c.executescript("""
            CREATE TABLE IF NOT EXISTS _arcanis_config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS _arcanis_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                config TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS _arcanis_structured (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS _arcanis_kv (
                collection TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (collection, key)
            );
            CREATE TABLE IF NOT EXISTS _arcanis_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                vector BLOB NOT NULL,
                metadata_id INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS _arcanis_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _arcanis_indexes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                field TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_structured_collection ON _arcanis_structured(collection);
            CREATE INDEX IF NOT EXISTS idx_vectors_collection ON _arcanis_vectors(collection);
            CREATE INDEX IF NOT EXISTS idx_metadata_lookup ON _arcanis_metadata(collection, entity_type, entity_id);
        """)
        c.commit()

    @property
    def version(self) -> str:
        return __import__("arcanisdb").__version__

    def info(self) -> dict:
        cur = self.conn.execute("SELECT COUNT(*) as c FROM _arcanis_collections")
        collections = cur.fetchone()["c"]
        cur = self.conn.execute("SELECT COUNT(*) as c FROM _arcanis_structured")
        records = cur.fetchone()["c"]
        cur = self.conn.execute("SELECT COUNT(*) as c FROM _arcanis_kv")
        kv_items = cur.fetchone()["c"]
        cur = self.conn.execute("SELECT COUNT(*) as c FROM _arcanis_vectors")
        vectors = cur.fetchone()["c"]
        return {
            "version": self.version,
            "path": self.path,
            "collections": collections,
            "structured_records": records,
            "kv_items": kv_items,
            "vectors": vectors,
            "encrypted": self.crypto is not None,
        }

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
