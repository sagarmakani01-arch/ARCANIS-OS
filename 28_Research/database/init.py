"""
ArcanisResearch Database Initialization

Handles setting up the SQLite database, creating tables, and initializing embeddings.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

class ResearchDatabase:
    def __init__(self, db_path="database/arcanis_research.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        """Create all required database tables"""
        self.connect()

        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS research_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT,
            research_area TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            file_path TEXT,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES research_entries(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id),
            UNIQUE(entry_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            embedding BLOB,
            model TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES research_entries(id)
        );
        """)

        self.conn.commit()
        self.close()

    def insert_entry(self, title, entry_type, content, research_area, metadata=None):
        """Insert a new research entry into the database"""
        self.connect()
        created_at = datetime.now().isoformat()
        updated_at = created_at

        metadata_json = json.dumps(metadata) if metadata else None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO research_entries (title, type, content, research_area, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, entry_type, content, research_area, created_at, updated_at, metadata_json)
        )

        entry_id = cursor.lastrowid
        self.conn.commit()
        self.close()

        return entry_id

    def get_entry(self, entry_id):
        """Get a specific research entry by ID"""
        self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM research_entries WHERE id = ?", (entry_id,))
        entry = cursor.fetchone()

        self.close()

        return dict(entry) if entry else None

    def search_entries(self, query, research_area=None):
        """Search entries by title/content with optional research area filter"""
        self.connect()

        sql = "SELECT * FROM research_entries WHERE (title LIKE ? OR content LIKE ?)"
        params = [f"%{query}%", f"%{query}%"]

        if research_area:
            sql += " AND research_area = ?"
            params.append(research_area)

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        entries = cursor.fetchall()

        self.close()

        return [dict(entry) for entry in entries]

    def add_tags(self, entry_id, tag_names):
        """Add tags to an entry"""
        self.connect()

        cursor = self.conn.cursor()

        for tag_name in tag_names:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))

            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag = cursor.fetchone()
            if tag:
                cursor.execute(
                    "INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)",
                    (entry_id, tag['id'])
                )

        self.conn.commit()
        self.close()
