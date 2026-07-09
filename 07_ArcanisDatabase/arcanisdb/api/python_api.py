from typing import List, Dict, Optional, Any, Union
from arcanisdb import ArcanisDatabase


class ArcanisAPI:
    def __init__(self, path: str = ":memory:", encryption_key: Optional[str] = None):
        self._db = ArcanisDatabase(path, encryption_key)

    @property
    def db(self) -> ArcanisDatabase:
        return self._db

    # --- Collections ---
    def create_collection(self, name: str, schema: Optional[Dict] = None) -> str:
        return self._db.structured.create_collection(name, schema)

    def list_collections(self) -> List[str]:
        return self._db.structured.list_collections()

    def drop_collection(self, name: str) -> None:
        self._db.structured.drop_collection(name)

    # --- Structured Data ---
    def insert(self, collection: str, data: Dict) -> int:
        return self._db.structured.insert(collection, data)

    def insert_many(self, collection: str, records: List[Dict]) -> List[int]:
        return self._db.structured.insert_many(collection, records)

    def get(self, collection: str, record_id: int) -> Optional[Dict]:
        return self._db.structured.get(collection, record_id)

    def update(self, collection: str, record_id: int, data: Dict) -> bool:
        return self._db.structured.update(collection, record_id, data)

    def delete(self, collection: str, record_id: int) -> bool:
        return self._db.structured.delete(collection, record_id)

    def query(self, collection: str, filters: Optional[Dict] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._db.structured.query(collection, filters, limit, offset)

    def count(self, collection: str, filters: Optional[Dict] = None) -> int:
        return self._db.structured.count(collection, filters)

    # --- Key-Value ---
    def kv_set(self, collection: str, key: str, value: Any) -> None:
        return self._db.kv.set(collection, key, value)

    def kv_get(self, collection: str, key: str) -> Optional[Any]:
        return self._db.kv.get(collection, key)

    def kv_delete(self, collection: str, key: str) -> bool:
        return self._db.kv.delete(collection, key)

    def kv_keys(self, collection: str) -> List[str]:
        return self._db.kv.list_keys(collection)

    def kv_exists(self, collection: str, key: str) -> bool:
        return self._db.kv.exists(collection, key)

    def kv_increment(self, collection: str, key: str, amount: int = 1) -> int:
        return self._db.kv.increment(collection, key, amount)

    # --- Vectors ---
    def vector_insert(self, collection: str, vector: List[float], metadata: Optional[Dict] = None) -> int:
        if metadata:
            return self._db.embeddings.store(collection, vector, metadata)
        return self._db.vectors.insert(collection, vector)

    def vector_search(self, collection: str, query_vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[Dict]:
        return self._db.similarity.search(collection, query_vector, top_k, metric)

    def vector_delete(self, vector_id: int) -> bool:
        return self._db.vectors.delete(vector_id)

    def vector_count(self, collection: str) -> int:
        return self._db.vectors.count(collection)

    # --- Embeddings ---
    def embed_store(self, collection: str, vector: List[float], metadata: Optional[Dict] = None) -> int:
        return self._db.embeddings.store(collection, vector, metadata)

    def embed_search(self, collection: str, query_vector: List[float], top_k: int = 10, metric: str = "cosine") -> List[Dict]:
        return self._db.embeddings.search(collection, query_vector, top_k, metric)

    # --- Knowledge Retrieval ---
    def store_knowledge(self, collection: str, content: str, embedding: List[float], metadata: Optional[Dict] = None) -> int:
        return self._db.retrieval.store_knowledge(collection, content, embedding, metadata)

    def retrieve(self, collection: str, query_vector: List[float], top_k: int = 5, min_score: float = 0.0) -> List[Dict]:
        return self._db.retrieval.retrieve(collection, query_vector, top_k, min_score)

    def retrieve_by_metadata(self, collection: str, metadata_filter: Dict, top_k: int = 10) -> List[Dict]:
        return self._db.retrieval.retrieve_by_metadata(collection, metadata_filter, top_k)

    # --- Metadata ---
    def meta_set(self, collection: str, entity_type: str, entity_id: str, key: str, value: Any) -> None:
        return self._db.metadata.set(collection, entity_type, entity_id, key, value)

    def meta_get(self, collection: str, entity_type: str, entity_id: str, key: str) -> Optional[Any]:
        return self._db.metadata.get(collection, entity_type, entity_id, key)

    def meta_get_all(self, collection: str, entity_type: str, entity_id: str) -> Dict:
        return self._db.metadata.get_all(collection, entity_type, entity_id)

    # --- Indexing ---
    def create_index(self, collection: str, field: str, index_type: str = "btree") -> str:
        return self._db.indexes.create_index(collection, field, index_type)

    def list_indexes(self) -> List[Dict]:
        return self._db.indexes.list_indexes()

    def rebuild_indexes(self, collection: Optional[str] = None) -> int:
        return self._db.indexes.rebuild_indexes(collection)

    # --- Backup ---
    def backup(self, path: Optional[str] = None) -> str:
        return self._db.backup.backup(path)

    def restore(self, path: str) -> str:
        return self._db.backup.restore(path)

    # --- Query ---
    def query_ql(self, query: str) -> Any:
        return self._db.query.execute(query)

    # --- System ---
    def info(self) -> Dict:
        return self._db.info()

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
