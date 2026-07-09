import json
from typing import Dict, List, Optional
import sqlite3


class IndexManager:
    def __init__(self, db):
        self.db = db

    def create_index(self, collection: str, field: str, index_type: str = "btree") -> str:
        index_name = f"idx_{collection}_{field}"

        existing = self.db.conn.execute(
            "SELECT id FROM _arcanis_indexes WHERE collection=? AND field=? AND type=?",
            (collection, field, index_type),
        ).fetchone()
        if existing:
            return index_name

        if index_type == "btree":
            try:
                self.db.conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON _arcanis_structured(json_extract(data, '$."{field}"'))
                """)
            except sqlite3.OperationalError:
                pass

        self.db.conn.execute(
            "INSERT INTO _arcanis_indexes (collection, field, type) VALUES (?, ?, ?)",
            (collection, field, index_type),
        )
        self.db.conn.commit()
        return index_name

    def list_indexes(self) -> List[Dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM _arcanis_indexes ORDER BY collection, field"
        )
        return [dict(row) for row in cur.fetchall()]

    def drop_index(self, collection: str, field: str) -> bool:
        index_name = f"idx_{collection}_{field}"
        try:
            self.db.conn.execute(f"DROP INDEX IF EXISTS {index_name}")
        except sqlite3.OperationalError:
            pass
        cur = self.db.conn.execute(
            "DELETE FROM _arcanis_indexes WHERE collection=? AND field=?",
            (collection, field),
        )
        self.db.conn.commit()
        return cur.rowcount > 0

    def rebuild_indexes(self, collection: Optional[str] = None) -> int:
        if collection:
            indexes = self.db.conn.execute(
                "SELECT * FROM _arcanis_indexes WHERE collection=?", (collection,)
            ).fetchall()
        else:
            indexes = self.db.conn.execute("SELECT * FROM _arcanis_indexes").fetchall()

        count = 0
        for idx in indexes:
            try:
                idx_name = f"idx_{idx['collection']}_{idx['field']}"
                self.db.conn.execute(f"DROP INDEX IF EXISTS {idx_name}")
                self.db.conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name}
                    ON _arcanis_structured(json_extract(data, '$."{idx['field']}"'))
                """)
                count += 1
            except sqlite3.OperationalError:
                pass
        self.db.conn.commit()
        return count
