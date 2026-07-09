from typing import Any, Dict
from arcanisdb.query.parser import ArcanisQLParser


class QueryExecutor:
    def __init__(self, db):
        self.db = db
        self.parser = ArcanisQLParser()

    def execute(self, query: str) -> Any:
        parsed = self.parser.parse(query)
        command = parsed["command"]

        handlers = {
            "create_collection": self._handle_create_collection,
            "insert": self._handle_insert,
            "select": self._handle_select,
            "update": self._handle_update,
            "delete": self._handle_delete,
            "kv_set": self._handle_kv_set,
            "kv_get": self._handle_kv_get,
            "kv_del": self._handle_kv_del,
            "vector_insert": self._handle_vector_insert,
            "vector_search": self._handle_vector_search,
            "embed_store": self._handle_embed_store,
            "embed_search": self._handle_embed_search,
            "retrieve": self._handle_retrieve,
            "create_index": self._handle_create_index,
            "backup": self._handle_backup,
            "info": self._handle_info,
        }

        handler = handlers.get(command)
        if not handler:
            raise ValueError(f"Unknown command: {command}")
        return handler(parsed)

    def _handle_create_collection(self, parsed: Dict) -> str:
        if parsed["type"] == "structured":
            self.db.structured.create_collection(parsed["name"])
        return f"Collection '{parsed['name']}' created"

    def _handle_insert(self, parsed: Dict) -> int:
        return self.db.structured.insert(parsed["collection"], parsed["data"])

    def _handle_select(self, parsed: Dict) -> list:
        return self.db.structured.query(
            parsed["collection"],
            filters=parsed.get("filters"),
            limit=parsed.get("limit", 100),
            offset=parsed.get("offset", 0),
        )

    def _handle_update(self, parsed: Dict) -> bool:
        return self.db.structured.update(parsed["collection"], parsed["id"], parsed["data"])

    def _handle_delete(self, parsed: Dict) -> bool:
        if parsed.get("id"):
            return self.db.structured.delete(parsed["collection"], parsed["id"])
        self.db.structured.drop_collection(parsed["collection"])
        return True

    def _handle_kv_set(self, parsed: Dict) -> None:
        self.db.kv.set(parsed["collection"], parsed["key"], parsed["value"])

    def _handle_kv_get(self, parsed: Dict) -> Any:
        return self.db.kv.get(parsed["collection"], parsed["key"])

    def _handle_kv_del(self, parsed: Dict) -> bool:
        return self.db.kv.delete(parsed["collection"], parsed["key"])

    def _handle_vector_insert(self, parsed: Dict) -> int:
        return self.db.vectors.insert(parsed["collection"], parsed["vector"])

    def _handle_vector_search(self, parsed: Dict) -> list:
        return self.db.similarity.search(
            parsed["collection"],
            parsed["vector"],
            top_k=parsed.get("top_k", 10),
            metric=parsed.get("metric", "cosine"),
        )

    def _handle_embed_store(self, parsed: Dict) -> int:
        return self.db.embeddings.store(
            parsed["collection"],
            parsed["vector"],
            parsed.get("metadata"),
        )

    def _handle_embed_search(self, parsed: Dict) -> list:
        return self.db.embeddings.search(
            parsed["collection"],
            parsed["vector"],
            top_k=parsed.get("top_k", 10),
            metric=parsed.get("metric", "cosine"),
        )

    def _handle_retrieve(self, parsed: Dict) -> list:
        return self.db.retrieval.retrieve(
            parsed["collection"],
            parsed["vector"],
            top_k=parsed.get("top_k", 5),
            min_score=parsed.get("min_score", 0.0),
        )

    def _handle_create_index(self, parsed: Dict) -> str:
        self.db.indexes.create_index(
            parsed["collection"],
            parsed["field"],
            parsed.get("type", "btree"),
        )
        return f"Index created on {parsed['collection']}({parsed['field']})"

    def _handle_backup(self, parsed: Dict) -> str:
        self.db.backup.backup(parsed["path"])
        return f"Backup saved to {parsed['path']}"

    def _handle_info(self, parsed: Dict) -> dict:
        return self.db.info()
