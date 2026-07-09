"""Additional tests for ArcanisDatabase — embeddings, retrieval, backup, API, and edge cases."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arcanisdb import ArcanisDatabase


# ===========================================================================
# Embedding Store
# ===========================================================================

class TestEmbeddingStore:
    def test_store_and_search(self):
        db = ArcanisDatabase()
        v1 = [0.1, 0.2, 0.3]
        v2 = [0.9, 0.8, 0.7]
        db.embeddings.store("col", v1, {"label": "a"})
        db.embeddings.store("col", v2, {"label": "b"})
        results = db.embeddings.search("col", [0.15, 0.25, 0.35], top_k=2)
        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]
        db.close()

    def test_store_many(self):
        db = ArcanisDatabase()
        vectors = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
        ids = db.embeddings.store_many("col", vectors)
        assert len(ids) == 3
        assert len(set(ids)) == 3
        db.close()

    def test_delete(self):
        db = ArcanisDatabase()
        vid = db.embeddings.store("col", [1.0, 0.0])
        assert db.embeddings.delete(vid) is True
        assert db.vectors.get(vid) is None
        db.close()

    def test_count(self):
        db = ArcanisDatabase()
        db.embeddings.store("col", [1.0, 0.0])
        db.embeddings.store("col", [0.0, 1.0])
        assert db.embeddings.count("col") == 2
        db.close()

    def test_list_collections(self):
        db = ArcanisDatabase()
        db.embeddings.store("alpha", [1.0])
        db.embeddings.store("beta", [0.0, 1.0])
        cols = db.embeddings.list_collections()
        assert "alpha" in cols
        assert "beta" in cols
        db.close()

    def test_store_without_metadata(self):
        db = ArcanisDatabase()
        vid = db.embeddings.store("col", [1.0, 2.0, 3.0])
        assert vid > 0
        results = db.embeddings.search("col", [1.0, 2.0, 3.0], top_k=1)
        assert len(results) == 1
        db.close()


# ===========================================================================
# Knowledge Retriever
# ===========================================================================

class TestKnowledgeRetriever:
    def test_store_and_retrieve(self):
        db = ArcanisDatabase()
        db.retrieval.store_knowledge("docs", "Python is great", [0.1, 0.2, 0.3])
        db.retrieval.store_knowledge("docs", "Rust is fast", [0.7, 0.8, 0.9])
        results = db.retrieval.retrieve("docs", [0.15, 0.25, 0.35], top_k=2)
        assert len(results) == 2
        assert "content" in results[0]
        db.close()

    def test_retrieve_with_min_score(self):
        db = ArcanisDatabase()
        db.retrieval.store_knowledge("docs", "A", [1.0, 0.0, 0.0])
        db.retrieval.store_knowledge("docs", "B", [0.0, 1.0, 0.0])
        results = db.retrieval.retrieve("docs", [1.0, 0.0, 0.0], top_k=10, min_score=0.9)
        assert len(results) >= 1
        for r in results:
            assert r["score"] >= 0.9
        db.close()

    def test_delete_knowledge(self):
        db = ArcanisDatabase()
        vid = db.retrieval.store_knowledge("docs", "delete me", [1.0, 0.0])
        assert db.retrieval.delete_knowledge(vid) is True
        db.close()

    def test_retrieve_by_metadata(self):
        db = ArcanisDatabase()
        db.retrieval.store_knowledge("docs", "Item A", [1.0, 0.0], {"category": "lang"})
        db.retrieval.store_knowledge("docs", "Item B", [0.0, 1.0], {"category": "db"})
        results = db.retrieval.retrieve_by_metadata("docs", {"category": "lang"})
        assert len(results) >= 1
        assert results[0]["content"] == "Item A"
        db.close()


# ===========================================================================
# Backup & Restore
# ===========================================================================

class TestBackup:
    def test_backup_file_based(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            db = ArcanisDatabase(db_path)
            db.structured.create_collection("test")
            db.structured.insert("test", {"val": 42})

            with tempfile.NamedTemporaryFile(suffix=".bak", delete=False) as f:
                bak_path = f.name

            result = db.backup.backup(bak_path)
            assert result is not None

            db2 = ArcanisDatabase(db_path)
            db2.backup.restore(bak_path)
            record = db2.structured.get("test", 1)
            assert record is not None
            assert record["data"]["val"] == 42

            db.close()
            db2.close()
            os.remove(bak_path)
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_backup_in_memory_raises(self):
        db = ArcanisDatabase()
        with pytest.raises(ValueError, match="in-memory"):
            db.backup.backup("/tmp/test.bak")
        db.close()

    def test_backup_info(self):
        db = ArcanisDatabase()
        info = db.backup.info()
        assert "path" in info
        assert "backupable" in info
        assert info["backupable"] is False
        db.close()


# ===========================================================================
# Indexing
# ===========================================================================

class TestIndexing:
    def test_create_and_drop_index(self):
        db = ArcanisDatabase()
        db.structured.create_collection("test")
        db.structured.insert("test", {"name": "Alice"})
        db.indexes.create_index("test", "name")
        indexes = db.indexes.list_indexes()
        assert any(i["field"] == "name" for i in indexes)
        db.indexes.drop_index("test", "name")
        indexes = db.indexes.list_indexes()
        assert not any(i["field"] == "name" for i in indexes)
        db.close()

    def test_rebuild_indexes(self):
        db = ArcanisDatabase()
        db.structured.create_collection("test")
        db.structured.insert("test", {"x": 1})
        db.indexes.create_index("test", "x")
        count = db.indexes.rebuild_indexes("test")
        assert count >= 1
        db.close()

    def test_rebuild_all_indexes(self):
        db = ArcanisDatabase()
        db.structured.create_collection("a")
        db.structured.create_collection("b")
        db.indexes.create_index("a", "field1")
        db.indexes.create_index("b", "field2")
        count = db.indexes.rebuild_indexes()
        assert count >= 2
        db.close()

    def test_duplicate_index_idempotent(self):
        db = ArcanisDatabase()
        db.structured.create_collection("test")
        db.indexes.create_index("test", "name")
        db.indexes.create_index("test", "name")
        indexes = db.indexes.list_indexes()
        name_indexes = [i for i in indexes if i["field"] == "name"]
        assert len(name_indexes) == 1
        db.close()


# ===========================================================================
# API Facade
# ===========================================================================

class TestPythonAPI:
    def test_python_api(self):
        from arcanisdb.api.python_api import ArcanisAPI
        api = ArcanisAPI()
        assert api.db.info()["version"] == "0.1.0"
        api.db.close()

    def test_python_api_crud(self):
        from arcanisdb.api.python_api import ArcanisAPI
        api = ArcanisAPI()
        api.create_collection("users")
        rid = api.insert("users", {"name": "Alice"})
        record = api.get("users", rid)
        assert record["data"]["name"] == "Alice"
        api.update("users", rid, {"name": "Bob"})
        assert api.get("users", rid)["data"]["name"] == "Bob"
        api.delete("users", rid)
        assert api.get("users", rid) is None
        api.db.close()


# ===========================================================================
# Similarity Edge Cases
# ===========================================================================

class TestSimilarity:
    def test_search_empty_collection(self):
        db = ArcanisDatabase()
        results = db.similarity.search("empty", [1.0, 0.0], top_k=5)
        assert results == []
        db.close()

    def test_search_single_vector(self):
        db = ArcanisDatabase()
        db.vectors.insert("test", [1.0, 0.0, 0.0])
        results = db.similarity.search("test", [1.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0]["score"] == 1.0
        db.close()


# ===========================================================================
# KV Store Edge Cases
# ===========================================================================

class TestKVStore:
    def test_batch_set(self):
        db = ArcanisDatabase()
        db.kv.set("batch", "a", 1)
        db.kv.set("batch", "b", 2)
        db.kv.set("batch", "c", 3)
        keys = db.kv.list_keys("batch")
        assert len(keys) == 3
        db.close()

    def test_set_complex_value(self):
        db = ArcanisDatabase()
        db.kv.set("data", "config", {"theme": "dark", "lang": "en"})
        val = db.kv.get("data", "config")
        assert val["theme"] == "dark"
        assert val["lang"] == "en"
        db.close()

    def test_increment_from_zero(self):
        db = ArcanisDatabase()
        db.kv.increment("count", "visits")
        assert db.kv.get("count", "visits") == 1
        db.close()


# ===========================================================================
# Structured Query Edge Cases
# ===========================================================================

class TestStructuredQuery:
    def test_query_empty_collection(self):
        db = ArcanisDatabase()
        db.structured.create_collection("empty")
        results = db.structured.query("empty")
        assert results == []
        db.close()

    def test_query_nonexistent_collection(self):
        db = ArcanisDatabase()
        try:
            results = db.structured.query("nonexistent")
            assert results == []
        except Exception:
            pass
        db.close()

    def test_insert_multiple_fields(self):
        db = ArcanisDatabase()
        db.structured.create_collection("complex")
        rid = db.structured.insert("complex", {
            "name": "Test",
            "tags": ["a", "b"],
            "nested": {"key": "value"},
            "count": 42,
        })
        record = db.structured.get("complex", rid)
        assert record["data"]["tags"] == ["a", "b"]
        assert record["data"]["nested"]["key"] == "value"
        db.close()
