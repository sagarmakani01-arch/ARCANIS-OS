# ArcanisQL — Query Language Reference

## Overview
ArcanisQL is a SQL-like query language designed for ArcanisDatabase, supporting structured data, key-value operations, vector search, and knowledge retrieval.

## Statements

### Collections
```
CREATE COLLECTION <name> [TYPE structured]
```

### CRUD Operations
```
INSERT INTO <collection> <json_object>
SELECT [* | fields] FROM <collection> [WHERE field=value [AND ...]] [LIMIT n] [OFFSET n]
UPDATE <collection> SET <json_object> WHERE id=<id>
DELETE FROM <collection> WHERE id=<id>
```

### Key-Value
```
KV.SET <collection> <key> <value>
KV.GET <collection> <key>
KV.DEL <collection> <key>
```

### Vectors
```
VECTOR.INSERT <collection> <vector_json> [METADATA <json>]
VECTOR.SEARCH <collection> <vector_json> [TOP_K n] [METRIC cosine|dot|euclidean]
```

### Embeddings
```
EMBED.STORE <collection> <vector_json> [METADATA <json>]
EMBED.SEARCH <collection> <vector_json> [TOP_K n] [METRIC cosine|dot|euclidean]
```

### Knowledge Retrieval
```
RETRIEVE <collection> <vector_json> [TOP_K n] [MIN_SCORE score]
```

### Indexing
```
CREATE INDEX ON <collection> (<field>) [TYPE btree]
```

### System
```
BACKUP TO <path>
INFO
```

## Examples

```sql
CREATE COLLECTION users
INSERT INTO users {"name": "Alice", "age": 30}
SELECT * FROM users WHERE age=30 LIMIT 10
UPDATE users {"age": 31} WHERE id=1
DELETE FROM users WHERE id=1

KV.SET config theme dark
KV.GET config theme

VECTOR.INSERT items [0.1, 0.2, 0.3, 0.4, 0.5] METADATA {"label": "test"}
VECTOR.SEARCH items [0.15, 0.25, 0.35] TOP_K 5 METRIC cosine

EMBED.STORE docs [0.1, 0.2, 0.3] METADATA {"content": "hello"}
EMBED.SEARCH docs [0.15, 0.25, 0.35] TOP_K 3

RETRIEVE knowledge [0.5, 0.1, 0.8] TOP_K 3 MIN_SCORE 0.7

CREATE INDEX ON users (name)
BACKUP TO /tmp/backup.db
INFO
```

## Using with Python

```python
db.query.execute('CREATE COLLECTION users')
db.query.execute('INSERT INTO users {"name": "Alice", "age": 30}')
results = db.query.execute('SELECT * FROM users WHERE age=30')
```
