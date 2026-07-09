import json
from typing import Optional, Dict, Any, List


class MetadataStore:
    def __init__(self, db):
        self.db = db

    def set(self, collection: str, entity_type: str, entity_id: str, key: str, value: Any) -> None:
        self.db.conn.execute(
            "INSERT OR REPLACE INTO _arcanis_metadata (collection, entity_type, entity_id, key, value) VALUES (?, ?, ?, ?, ?)",
            (collection, entity_type, entity_id, key, self._serialize(value)),
        )
        self.db.conn.commit()

    def get(self, collection: str, entity_type: str, entity_id: str, key: str) -> Optional[Any]:
        cur = self.db.conn.execute(
            "SELECT value FROM _arcanis_metadata WHERE collection=? AND entity_type=? AND entity_id=? AND key=?",
            (collection, entity_type, entity_id, key),
        )
        row = cur.fetchone()
        return self._deserialize(row["value"]) if row else None

    def get_all(self, collection: str, entity_type: str, entity_id: str) -> Dict[str, Any]:
        cur = self.db.conn.execute(
            "SELECT key, value FROM _arcanis_metadata WHERE collection=? AND entity_type=? AND entity_id=?",
            (collection, entity_type, entity_id),
        )
        return {row["key"]: self._deserialize(row["value"]) for row in cur.fetchall()}

    def delete(self, collection: str, entity_type: str, entity_id: str, key: str) -> bool:
        cur = self.db.conn.execute(
            "DELETE FROM _arcanis_metadata WHERE collection=? AND entity_type=? AND entity_id=? AND key=?",
            (collection, entity_type, entity_id, key),
        )
        self.db.conn.commit()
        return cur.rowcount > 0

    def delete_entity(self, collection: str, entity_type: str, entity_id: str) -> None:
        self.db.conn.execute(
            "DELETE FROM _arcanis_metadata WHERE collection=? AND entity_type=? AND entity_id=?",
            (collection, entity_type, entity_id),
        )
        self.db.conn.commit()

    def find_by_value(self, collection: str, key: str, value: Any) -> List[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM _arcanis_metadata WHERE collection=? AND key=? AND value=?",
            (collection, key, self._serialize(value)),
        )
        return [dict(row) for row in cur.fetchall()]

    def find_by_entity_type(self, collection: str, entity_type: str) -> List[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM _arcanis_metadata WHERE collection=? AND entity_type=?",
            (collection, entity_type),
        )
        return [dict(row) for row in cur.fetchall()]

    def keys(self, collection: str, entity_type: str, entity_id: str) -> List[str]:
        cur = self.db.conn.execute(
            "SELECT key FROM _arcanis_metadata WHERE collection=? AND entity_type=? AND entity_id=?",
            (collection, entity_type, entity_id),
        )
        return [row["key"] for row in cur.fetchall()]

    def set_batch(self, collection: str, entity_type: str, entity_id: str, metadata: Dict[str, Any]) -> None:
        for key, value in metadata.items():
            self.set(collection, entity_type, entity_id, key, value)

    def _serialize(self, value: Any) -> str:
        return json.dumps(value)

    def _deserialize(self, value: str) -> Any:
        return json.loads(value)
