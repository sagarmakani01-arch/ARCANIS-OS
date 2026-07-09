from typing import List, Dict, Optional, Any


class KnowledgeRetriever:
    def __init__(self, db):
        self.db = db

    def store_knowledge(self, collection: str, content: str, embedding: List[float], metadata: Optional[Dict] = None) -> int:
        meta = {"content": content, **(metadata or {})}
        return self.db.embeddings.store(collection, embedding, meta)

    def retrieve(self, collection: str, query_vector: List[float], top_k: int = 5, min_score: float = 0.0) -> List[Dict]:
        results = self.db.embeddings.search(collection, query_vector, top_k)
        filtered = [r for r in results if r["score"] >= min_score]
        for r in filtered:
            if "metadata" in r and "content" in r["metadata"]:
                r["content"] = r["metadata"].pop("content")
        return filtered

    def retrieve_by_metadata(self, collection: str, metadata_filter: Dict[str, Any], top_k: int = 10) -> List[Dict]:
        all_vecs = self.db.vectors.all_vectors(collection)
        results = []
        for vid, vec, mid in all_vecs:
            if mid is not None:
                meta = self.db.metadata.get_all(
                    collection, "embedding", str(mid)
                )
                if not meta:
                    cur = self.db.conn.execute(
                        "SELECT entity_id FROM _arcanis_metadata WHERE id=?", (mid,)
                    )
                    row = cur.fetchone()
                    if row:
                        meta = self.db.metadata.get_all(collection, "embedding", row["entity_id"])

                if meta:
                    match = all(meta.get(k) == v for k, v in metadata_filter.items())
                    if match:
                        content = meta.pop("content", "")
                        results.append({
                            "id": vid,
                            "content": content,
                            "metadata": meta,
                            "vector": vec,
                        })
        return results[:top_k]

    def delete_knowledge(self, vector_id: int) -> bool:
        return self.db.embeddings.delete(vector_id)
