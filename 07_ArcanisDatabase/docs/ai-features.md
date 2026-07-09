# AI Features

## Embedding Storage
Store embeddings with associated metadata:
```python
vector = [0.1, 0.2, 0.3, 0.4, 0.5]  # 5-dimensional embedding
db.embeddings.store("my_collection", vector, {"label": "example"})
```

## Similarity Search

### Supported Metrics
- **Cosine** — Measures cosine of angle between vectors (range: -1 to 1)
- **Dot Product** — Raw dot product (higher = more similar)
- **Euclidean** — Negative Euclidean distance (higher = more similar)

```python
results = db.similarity.search("my_collection", query_vec, top_k=10, metric="cosine")
```

Results include:
- `id` — Vector ID
- `score` — Similarity score
- `vector` — The stored vector
- `metadata` — Associated metadata (if any)

## Knowledge Retrieval
Store and retrieve knowledge by semantic similarity:
```python
# Store knowledge
db.retrieval.store_knowledge(
    "docs",
    "Python is a programming language.",
    [0.1, 0.2, 0.3],
    {"source": "wikipedia", "topic": "programming"}
)

# Retrieve by similarity
results = db.retrieval.retrieve("docs", query_vec, top_k=5, min_score=0.5)

# Retrieve by metadata filter
results = db.retrieval.retrieve_by_metadata("docs", {"source": "wikipedia"})
```

## Integration with ArcanisBrain
ArcanisDatabase is designed to work with ArcanisBrain for:
- Memory storage and retrieval
- Context-aware knowledge lookup
- Embedding management for LLM applications
