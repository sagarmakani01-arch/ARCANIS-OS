# ArcanisDatabase

A fast, lightweight database designed for AI memory and applications. Integrates with ArcanisBrain.

## Features

### Storage
- **Structured Data** — Store and query JSON records
- **Key-Value Storage** — Simple key-value pairs
- **Vector Storage** — High-dimensional vector storage
- **Metadata Storage** — Flexible metadata tagging

### AI Capabilities
- **Embedding Storage** — Store and manage embeddings
- **Similarity Search** — Cosine, dot product, and euclidean search
- **Knowledge Retrieval** — Retrieve knowledge by content similarity

### System
- **Query Engine** — ArcanisQL query language
- **Indexing** — B-tree indexing on JSON fields
- **Backup System** — File-based backup and restore
- **Encryption** — AES-256-GCM encryption support

## Quickstart

```python
from arcanisdb import ArcanisDatabase

db = ArcanisDatabase()

# Structured data
db.structured.create_collection("users")
db.structured.insert("users", {"name": "Alice", "age": 30})

# Key-value store
db.kv.set("config", "theme", "dark")

# Vectors
db.vectors.insert("items", [0.1, 0.2, 0.3])

# Similarity search
results = db.similarity.search("items", [0.15, 0.25, 0.35])

# Query with ArcanisQL
db.query.execute('SELECT * FROM users WHERE age=30')
```
