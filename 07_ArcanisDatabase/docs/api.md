# API Reference

## ArcanisDatabase

### Constructor
```python
db = ArcanisDatabase(path=":memory:", encryption_key=None)
```
- `path` — File path for persistent storage, or `":memory:"` for in-memory
- `encryption_key` — Optional encryption key (requires `cryptography`)

### Properties
```python
db.version    # Version string
db.conn       # SQLite connection
```

### Methods
```python
db.info()     # Database statistics
db.close()    # Close connection
```

## StructuredStore (`db.structured`)

| Method | Description |
|--------|-------------|
| `create_collection(name, schema=None)` | Create a collection |
| `list_collections()` | List all collections |
| `insert(collection, data)` | Insert a record |
| `insert_many(collection, records)` | Batch insert |
| `get(collection, id)` | Get record by ID |
| `update(collection, id, data)` | Update record |
| `delete(collection, id)` | Delete record |
| `query(collection, filters=None, limit=100, offset=0)` | Query records |
| `count(collection, filters=None)` | Count records |
| `drop_collection(name)` | Drop collection |

## KeyValueStore (`db.kv`)

| Method | Description |
|--------|-------------|
| `set(collection, key, value)` | Set key-value pair |
| `get(collection, key)` | Get value by key |
| `delete(collection, key)` | Delete key-value pair |
| `exists(collection, key)` | Check if key exists |
| `list_keys(collection)` | List all keys |
| `get_batch(collection, keys)` | Batch get |
| `set_batch(collection, items)` | Batch set |
| `increment(collection, key, amount=1)` | Atomically increment |
| `clear(collection)` | Clear all pairs |

## VectorStore (`db.vectors`)

| Method | Description |
|--------|-------------|
| `insert(collection, vector, metadata_id=None)` | Insert vector |
| `get(id)` | Get vector by ID |
| `delete(id)` | Delete vector |
| `count(collection)` | Count vectors |
| `all_vectors(collection)` | Get all vectors |

## SimilaritySearch (`db.similarity`)

| Method | Description |
|--------|-------------|
| `search(collection, query_vector, top_k=10, metric='cosine')` | Similarity search |

Metrics: `cosine`, `dot`, `euclidean`

## EmbeddingStore (`db.embeddings`)

| Method | Description |
|--------|-------------|
| `store(collection, vector, metadata=None)` | Store embedding |
| `search(collection, query_vector, top_k=10, metric='cosine')` | Search embeddings |
| `delete(id)` | Delete embedding |
| `count(collection)` | Count embeddings |

## KnowledgeRetriever (`db.retrieval`)

| Method | Description |
|--------|-------------|
| `store_knowledge(collection, content, embedding, metadata=None)` | Store knowledge |
| `retrieve(collection, query_vector, top_k=5, min_score=0.0)` | Retrieve by similarity |
| `retrieve_by_metadata(collection, filters, top_k=10)` | Retrieve by metadata |
| `delete_knowledge(id)` | Delete knowledge entry |

## MetadataStore (`db.metadata`)

| Method | Description |
|--------|-------------|
| `set(collection, entity_type, entity_id, key, value)` | Set metadata |
| `get(collection, entity_type, entity_id, key)` | Get metadata value |
| `get_all(collection, entity_type, entity_id)` | Get all metadata |
| `delete(collection, entity_type, entity_id, key)` | Delete metadata key |
| `delete_entity(collection, entity_type, entity_id)` | Delete all entity metadata |
| `find_by_value(collection, key, value)` | Find by metadata value |
| `keys(collection, entity_type, entity_id)` | List metadata keys |
| `set_batch(collection, entity_type, entity_id, metadata_dict)` | Batch set |

## IndexManager (`db.indexes`)

| Method | Description |
|--------|-------------|
| `create_index(collection, field, type='btree')` | Create index |
| `list_indexes()` | List all indexes |
| `drop_index(collection, field)` | Drop index |
| `rebuild_indexes(collection=None)` | Rebuild indexes |

## BackupManager (`db.backup`)

| Method | Description |
|--------|-------------|
| `backup(path=None)` | Create backup |
| `restore(path)` | Restore from backup |
| `info()` | Backup info |

## QueryExecutor (`db.query`)

| Method | Description |
|--------|-------------|
| `execute(query_string)` | Execute ArcanisQL query |

## Context Manager

```python
with ArcanisDatabase("mydb.db") as db:
    db.structured.insert("collection", {"key": "value"})
```
