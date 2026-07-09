from typing import Optional, Dict, Any, List


class KeyValueStore:
    def __init__(self, db):
        self.db = db

    def set(self, collection: str, key: str, value: Any) -> None:
        self.db.conn.execute(
            "INSERT OR REPLACE INTO _arcanis_kv (collection, key, value) VALUES (?, ?, ?)",
            (collection, key, self._serialize(value)),
        )
        self.db.conn.commit()

    def get(self, collection: str, key: str) -> Optional[Any]:
        cur = self.db.conn.execute(
            "SELECT value FROM _arcanis_kv WHERE collection=? AND key=?",
            (collection, key),
        )
        row = cur.fetchone()
        return self._deserialize(row["value"]) if row else None

    def delete(self, collection: str, key: str) -> bool:
        cur = self.db.conn.execute(
            "DELETE FROM _arcanis_kv WHERE collection=? AND key=?",
            (collection, key),
        )
        self.db.conn.commit()
        return cur.rowcount > 0

    def exists(self, collection: str, key: str) -> bool:
        cur = self.db.conn.execute(
            "SELECT 1 FROM _arcanis_kv WHERE collection=? AND key=?",
            (collection, key),
        )
        return cur.fetchone() is not None

    def list_keys(self, collection: str) -> List[str]:
        cur = self.db.conn.execute(
            "SELECT key FROM _arcanis_kv WHERE collection=? ORDER BY key",
            (collection,),
        )
        return [row["key"] for row in cur.fetchall()]

    def list_collections(self) -> List[str]:
        cur = self.db.conn.execute(
            "SELECT DISTINCT collection FROM _arcanis_kv ORDER BY collection"
        )
        return [row["collection"] for row in cur.fetchall()]

    def get_batch(self, collection: str, keys: List[str]) -> Dict[str, Any]:
        placeholders = ",".join("?" for _ in keys)
        cur = self.db.conn.execute(
            f"SELECT key, value FROM _arcanis_kv WHERE collection=? AND key IN ({placeholders})",
            [collection] + keys,
        )
        return {row["key"]: self._deserialize(row["value"]) for row in cur.fetchall()}

    def set_batch(self, collection: str, items: Dict[str, Any]) -> None:
        for key, value in items.items():
            self.set(collection, key, value)

    def increment(self, collection: str, key: str, amount: int = 1) -> int:
        current = self.get(collection, key)
        if current is None:
            current = 0
        new_value = int(current) + amount
        self.set(collection, key, new_value)
        return new_value

    def clear(self, collection: str) -> None:
        self.db.conn.execute("DELETE FROM _arcanis_kv WHERE collection=?", (collection,))
        self.db.conn.commit()

    def _serialize(self, value: Any) -> str:
        import json
        return json.dumps(value)

    def _deserialize(self, value: str) -> Any:
        import json
        return json.loads(value)
