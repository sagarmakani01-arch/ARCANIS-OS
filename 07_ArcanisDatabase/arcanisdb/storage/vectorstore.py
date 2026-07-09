import json
import struct
from typing import List, Optional, Tuple, Any
import numpy as np


class VectorStore:
    def __init__(self, db):
        self.db = db

    def insert(self, collection: str, vector: List[float], metadata_id: Optional[int] = None) -> int:
        blob = self._vector_to_blob(vector)
        self.db.conn.execute(
            "INSERT INTO _arcanis_vectors (collection, vector, metadata_id) VALUES (?, ?, ?)",
            (collection, blob, metadata_id),
        )
        self.db.conn.commit()
        return self.db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def insert_many(self, collection: str, vectors: List[List[float]], metadata_ids: Optional[List[Optional[int]]] = None) -> List[int]:
        ids = []
        for i, vec in enumerate(vectors):
            mid = metadata_ids[i] if metadata_ids else None
            ids.append(self.insert(collection, vec, mid))
        return ids

    def get(self, vector_id: int) -> Optional[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM _arcanis_vectors WHERE id=?", (vector_id,)
        )
        row = cur.fetchone()
        if row:
            result = dict(row)
            result["vector"] = self._blob_to_vector(result["vector"])
            return result
        return None

    def delete(self, vector_id: int) -> bool:
        cur = self.db.conn.execute(
            "DELETE FROM _arcanis_vectors WHERE id=?", (vector_id,)
        )
        self.db.conn.commit()
        return cur.rowcount > 0

    def count(self, collection: str) -> int:
        cur = self.db.conn.execute(
            "SELECT COUNT(*) as c FROM _arcanis_vectors WHERE collection=?", (collection,)
        )
        return cur.fetchone()["c"]

    def list_collections(self) -> List[str]:
        cur = self.db.conn.execute(
            "SELECT DISTINCT collection FROM _arcanis_vectors ORDER BY collection"
        )
        return [row["collection"] for row in cur.fetchall()]

    def all_vectors(self, collection: str) -> List[Tuple[int, List[float], Optional[int]]]:
        cur = self.db.conn.execute(
            "SELECT id, vector, metadata_id FROM _arcanis_vectors WHERE collection=? ORDER BY id",
            (collection,),
        )
        results = []
        for row in cur.fetchall():
            results.append((row["id"], self._blob_to_vector(row["vector"]), row["metadata_id"]))
        return results

    def _vector_to_blob(self, vector: List[float]) -> bytes:
        return struct.pack(f"{len(vector)}d", *vector)

    def _blob_to_vector(self, blob: bytes) -> List[float]:
        n = len(blob) // 8
        return list(struct.unpack(f"{n}d", blob))
