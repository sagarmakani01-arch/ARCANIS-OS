from typing import List, Optional, Dict, Any
import numpy as np


class EmbeddingStore:
    def __init__(self, db):
        self.db = db

    def store(self, collection: str, vector: List[float], metadata: Optional[Dict] = None) -> int:
        if metadata:
            meta_id = self.db.metadata.set_batch(
                collection, "embedding", str(hash(str(metadata))), metadata
            )
        metadata_id = None
        if metadata:
            meta_entity_id = str(abs(hash(str(metadata))))
            self.db.metadata.set_batch(collection, "embedding", meta_entity_id, metadata)
            # find the metadata id
            rows = self.db.metadata.find_by_entity_type(collection, "embedding")
            for r in rows:
                if r["entity_id"] == meta_entity_id:
                    metadata_id = r["id"]
                    break

        vector_id = self.db.vectors.insert(collection, vector, metadata_id)
        return vector_id

    def store_many(self, collection: str, vectors: List[List[float]], metadatas: Optional[List[Optional[Dict]]] = None) -> List[int]:
        ids = []
        for i, vec in enumerate(vectors):
            meta = metadatas[i] if metadatas else None
            ids.append(self.store(collection, vec, meta))
        return ids

    def search(self, collection: str, query_vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[Dict]:
        return self.db.similarity.search(collection, query_vector, top_k, metric)

    def delete(self, vector_id: int) -> bool:
        return self.db.vectors.delete(vector_id)

    def count(self, collection: str) -> int:
        return self.db.vectors.count(collection)

    def list_collections(self) -> List[str]:
        return self.db.vectors.list_collections()
