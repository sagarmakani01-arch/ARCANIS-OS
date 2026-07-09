from typing import List, Dict, Optional, Tuple
import numpy as np


class SimilaritySearch:
    def __init__(self, db):
        self.db = db
        self._cache = {}

    def search(self, collection: str, query_vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[Dict]:
        all_vecs = self.db.vectors.all_vectors(collection)
        if not all_vecs:
            return []

        q = np.array(query_vector, dtype=np.float64)
        ids = []
        vectors = []
        meta_ids = []
        for vid, vec, mid in all_vecs:
            ids.append(vid)
            vectors.append(vec)
            meta_ids.append(mid)

        matrix = np.array(vectors, dtype=np.float64)

        if metric == "cosine":
            q_norm = np.linalg.norm(q)
            if q_norm == 0:
                return []
            q = q / q_norm
            norms = np.linalg.norm(matrix, axis=1)
            norms[norms == 0] = 1
            matrix = matrix / norms[:, np.newaxis]
            scores = np.dot(matrix, q)
        elif metric == "dot":
            scores = np.dot(matrix, q)
        elif metric == "euclidean":
            scores = -np.linalg.norm(matrix - q, axis=1)
        else:
            raise ValueError(f"Unknown metric: {metric}. Use 'cosine', 'dot', or 'euclidean'.")

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            result = {
                "id": ids[idx],
                "score": score,
                "vector": vectors[idx],
            }
            if meta_ids[idx] is not None:
                cur = self.db.conn.execute(
                    "SELECT entity_id FROM _arcanis_metadata WHERE id=?",
                    (meta_ids[idx],),
                )
                row = cur.fetchone()
                if row:
                    meta = self.db.metadata.get_all(collection, "embedding", row["entity_id"])
                    if meta:
                        result["metadata"] = meta
            results.append(result)

        return results

    def clear_cache(self):
        self._cache.clear()
