import json
from typing import List, Dict, Optional, Any


class StructuredStore:
    def __init__(self, db):
        self.db = db

    def create_collection(self, name: str, schema: Optional[Dict] = None) -> str:
        self.db.conn.execute(
            "INSERT OR IGNORE INTO _arcanis_collections (name, type, config) VALUES (?, ?, ?)",
            (name, "structured", json.dumps(schema or {})),
        )
        self.db.conn.commit()
        return name

    def list_collections(self) -> List[str]:
        cur = self.db.conn.execute(
            "SELECT name FROM _arcanis_collections WHERE type='structured'"
        )
        return [row["name"] for row in cur.fetchall()]

    def insert(self, collection: str, data: Dict) -> int:
        self.db.conn.execute(
            "INSERT INTO _arcanis_structured (collection, data) VALUES (?, ?)",
            (collection, json.dumps(data)),
        )
        self.db.conn.commit()
        return self.db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def insert_many(self, collection: str, records: List[Dict]) -> List[int]:
        ids = []
        for record in records:
            ids.append(self.insert(collection, record))
        return ids

    def get(self, collection: str, record_id: int) -> Optional[Dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM _arcanis_structured WHERE collection=? AND id=?",
            (collection, record_id),
        )
        row = cur.fetchone()
        if row:
            result = dict(row)
            result["data"] = json.loads(result["data"])
            return result
        return None

    def update(self, collection: str, record_id: int, data: Dict) -> bool:
        cur = self.db.conn.execute(
            "UPDATE _arcanis_structured SET data=?, updated_at=datetime('now') WHERE collection=? AND id=?",
            (json.dumps(data), collection, record_id),
        )
        self.db.conn.commit()
        return cur.rowcount > 0

    def delete(self, collection: str, record_id: int) -> bool:
        cur = self.db.conn.execute(
            "DELETE FROM _arcanis_structured WHERE collection=? AND id=?",
            (collection, record_id),
        )
        self.db.conn.commit()
        return cur.rowcount > 0

    def query(self, collection: str, filters: Optional[Dict] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        sql = "SELECT * FROM _arcanis_structured WHERE collection=?"
        params = [collection]
        if filters:
            for key, value in filters.items():
                sql += f" AND json_extract(data, '$.{key}') = ?"
                params.append(value)
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = self.db.conn.execute(sql, params)
        results = []
        for row in cur.fetchall():
            r = dict(row)
            r["data"] = json.loads(r["data"])
            results.append(r)
        return results

    def count(self, collection: str, filters: Optional[Dict] = None) -> int:
        sql = "SELECT COUNT(*) as c FROM _arcanis_structured WHERE collection=?"
        params = [collection]
        if filters:
            for key, value in filters.items():
                sql += f" AND json_extract(data, '$.{key}') = ?"
                params.append(value)
        cur = self.db.conn.execute(sql, params)
        return cur.fetchone()["c"]

    def drop_collection(self, name: str):
        self.db.conn.execute("DELETE FROM _arcanis_structured WHERE collection=?", (name,))
        self.db.conn.execute("DELETE FROM _arcanis_collections WHERE name=? AND type='structured'", (name,))
        self.db.conn.commit()
