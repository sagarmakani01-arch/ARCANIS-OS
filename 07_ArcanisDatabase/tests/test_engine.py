import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arcanisdb import ArcanisDatabase


def test_create_in_memory():
    db = ArcanisDatabase()
    assert db.path == ":memory:"
    info = db.info()
    assert info["version"] == "0.1.0"
    assert info["path"] == ":memory:"
    db.close()


def test_create_file_based():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    from pathlib import Path
    resolved = str(Path(path).resolve())
    db = ArcanisDatabase(path)
    assert db.path == resolved

    info = db.info()
    assert info["path"] == resolved
    db.close()
    os.remove(path)


def test_context_manager():
    with ArcanisDatabase() as db:
        assert db.info()["version"] == "0.1.0"


def test_info():
    db = ArcanisDatabase()
    info = db.info()
    assert "version" in info
    assert "collections" in info
    assert "structured_records" in info
    assert "kv_items" in info
    assert "vectors" in info
    assert "encrypted" in info
    db.close()


def test_structured_crud():
    db = ArcanisDatabase()
    db.structured.create_collection("test")
    collections = db.structured.list_collections()
    assert "test" in collections

    rid = db.structured.insert("test", {"name": "hello", "value": 42})
    assert rid > 0

    record = db.structured.get("test", rid)
    assert record is not None
    assert record["data"]["name"] == "hello"

    updated = db.structured.update("test", rid, {"name": "world", "value": 99})
    assert updated

    record = db.structured.get("test", rid)
    assert record["data"]["name"] == "world"

    deleted = db.structured.delete("test", rid)
    assert deleted

    record = db.structured.get("test", rid)
    assert record is None

    db.close()


def test_structured_query():
    db = ArcanisDatabase()
    db.structured.create_collection("test")
    db.structured.insert("test", {"name": "Alice", "age": 30})
    db.structured.insert("test", {"name": "Bob", "age": 25})

    results = db.structured.query("test", {"age": 30})
    assert len(results) == 1
    assert results[0]["data"]["name"] == "Alice"

    all_results = db.structured.query("test")
    assert len(all_results) == 2

    count = db.structured.count("test")
    assert count == 2

    db.close()


def test_kv_store():
    db = ArcanisDatabase()
    db.kv.set("config", "theme", "dark")
    db.kv.set("config", "port", 8080)

    assert db.kv.get("config", "theme") == "dark"
    assert db.kv.get("config", "port") == 8080
    assert db.kv.exists("config", "theme") is True
    assert db.kv.exists("config", "nope") is False

    keys = db.kv.list_keys("config")
    assert sorted(keys) == ["port", "theme"]

    db.kv.delete("config", "theme")
    assert db.kv.get("config", "theme") is None

    db.kv.increment("config", "counter")
    db.kv.increment("config", "counter")
    assert db.kv.get("config", "counter") == 2

    db.close()


def test_vectors():
    db = ArcanisDatabase()
    v1 = [0.1, 0.2, 0.3]
    v2 = [0.9, 0.8, 0.7]

    id1 = db.vectors.insert("test", v1)
    id2 = db.vectors.insert("test", v2)

    assert id1 != id2
    assert db.vectors.count("test") == 2

    vec = db.vectors.get(id1)
    assert vec is not None
    assert vec["vector"] == v1

    results = db.similarity.search("test", [0.15, 0.25, 0.35], top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == id1  # closer to v1

    db.close()


def test_similarity_metrics():
    db = ArcanisDatabase()
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    db.vectors.insert("test", v1)
    db.vectors.insert("test", v2)

    cos_results = db.similarity.search("test", [1.0, 0.0, 0.0], metric="cosine")
    assert cos_results[0]["id"] == 1  # v1 has cosine=1

    dot_results = db.similarity.search("test", [1.0, 0.0, 0.0], metric="dot")
    assert dot_results[0]["id"] == 1

    euc_results = db.similarity.search("test", [1.0, 0.0, 0.0], metric="euclidean")
    assert euc_results[0]["id"] == 1

    db.close()


def test_metadata():
    db = ArcanisDatabase()
    db.metadata.set("assets", "image", "logo.png", "format", "PNG")
    db.metadata.set("assets", "image", "logo.png", "size", 42)

    assert db.metadata.get("assets", "image", "logo.png", "format") == "PNG"
    assert db.metadata.get("assets", "image", "logo.png", "size") == 42

    all_meta = db.metadata.get_all("assets", "image", "logo.png")
    assert all_meta["format"] == "PNG"
    assert all_meta["size"] == 42

    keys = db.metadata.keys("assets", "image", "logo.png")
    assert sorted(keys) == ["format", "size"]

    db.metadata.delete("assets", "image", "logo.png", "format")
    assert db.metadata.get("assets", "image", "logo.png", "format") is None

    db.close()


def test_knowledge_retrieval():
    db = ArcanisDatabase()
    db.retrieval.store_knowledge(
        "knowledge", "Python is a programming language.", [0.1, 0.2, 0.3]
    )
    db.retrieval.store_knowledge(
        "knowledge", "SQLite is a database engine.", [0.4, 0.5, 0.6]
    )

    results = db.retrieval.retrieve("knowledge", [0.15, 0.25, 0.35], top_k=2)
    assert len(results) == 2

    db.close()


def test_arcanisql():
    db = ArcanisDatabase()
    db.structured.create_collection("test")
    db.structured.insert("test", {"name": "Alice"})

    result = db.query.execute('SELECT * FROM test LIMIT 10')
    assert len(result) == 1
    assert result[0]["data"]["name"] == "Alice"

    info = db.query.execute("INFO")
    assert info["version"] == "0.1.0"

    db.close()


def test_indexing():
    db = ArcanisDatabase()
    db.structured.create_collection("test")
    db.structured.insert("test", {"name": "Alice"})

    db.indexes.create_index("test", "name")
    indexes = db.indexes.list_indexes()
    assert len(indexes) > 0
    assert indexes[0]["field"] == "name"

    db.close()


def test_drop_collection():
    db = ArcanisDatabase()
    db.structured.create_collection("test")
    db.structured.insert("test", {"val": 1})
    assert db.structured.count("test") == 1
    db.structured.drop_collection("test")
    assert "test" not in db.structured.list_collections()

    db.close()


if __name__ == "__main__":
    test_create_in_memory()
    test_create_file_based()
    test_context_manager()
    test_info()
    test_structured_crud()
    test_structured_query()
    test_kv_store()
    test_vectors()
    test_similarity_metrics()
    test_metadata()
    test_knowledge_retrieval()
    test_arcanisql()
    test_indexing()
    test_drop_collection()
    print("All tests passed!")
