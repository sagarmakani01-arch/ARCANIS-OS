# ArcanisDatabase

A fast, lightweight database designed for AI memory and applications. Built for seamless integration with ArcanisBrain.

## Features

- **Structured Data** — JSON document storage with field-level querying
- **Key-Value Store** — Fast key-value pairs with atomic operations
- **Vector Storage** — High-dimensional vector storage with similarity search
- **Metadata Storage** — Flexible entity metadata tagging
- **Similarity Search** — Cosine, dot product, and Euclidean distance
- **Knowledge Retrieval** — Semantic knowledge lookup by embedding
- **ArcanisQL** — SQL-like query language for all operations
- **Indexing** — B-tree indexing on JSON fields
- **Backup & Restore** — File-based backup system
- **Encryption** — AES-256-GCM encryption
- **REST API** — Optional Flask-based REST API

## Install

```bash
pip install arcanisdb
```

### Optional Dependencies

```bash
pip install arcanisdb[full]    # All extras
pip install arcanisdb[rest]    # REST API support
pip install arcanisdb[encryption]  # Encryption support
```

## Quickstart

```python
from arcanisdb import ArcanisDatabase

# Create database
db = ArcanisDatabase()

# Structured data
db.structured.create_collection("users")
db.structured.insert("users", {"name": "Alice", "age": 30})

# Key-value store
db.kv.set("config", "theme", "dark")

# Vectors and similarity
db.vectors.insert("items", [0.1, 0.2, 0.3])
results = db.similarity.search("items", [0.15, 0.25, 0.35])

# Knowledge retrieval
db.retrieval.store_knowledge("docs", "Python is a language.", [0.1, 0.2, 0.3])
results = db.retrieval.retrieve("docs", [0.15, 0.25, 0.35])

# ArcanisQL
db.query.execute("SELECT * FROM users WHERE age=30")

# Check info
print(db.info())

# Close
db.close()
```

## Documentation

Full documentation is in the `/docs` directory:
- `docs/index.md` — Overview and quickstart
- `docs/api.md` — Full API reference
- `docs/query-language.md` — ArcanisQL reference
- `docs/storage.md` — Storage architecture
- `docs/ai-features.md` — AI capabilities

## Tests

```bash
pip install -e .
python tests/test_engine.py
```

## License

MIT
