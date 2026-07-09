"""
ArcanisQL - Query Language for ArcanisDatabase

STATEMENTS:
  CREATE COLLECTION <name> [TYPE <type>]
  INSERT INTO <collection> <json_data>
  SELECT [<fields>] FROM <collection> [WHERE <conditions>] [LIMIT n] [OFFSET n]
  UPDATE <collection> SET <json_data> WHERE id=<id>
  DELETE FROM <collection> WHERE id=<id>
  KV.SET <collection> <key> <value>
  KV.GET <collection> <key>
  KV.DEL <collection> <key>
  VECTOR.INSERT <collection> <vector_json> [METADATA <json>]
  VECTOR.SEARCH <collection> <vector_json> [TOP_K n] [METRIC <metric>]
  EMBED.STORE <collection> <vector_json> [METADATA <json>]
  EMBED.SEARCH <collection> <vector_json> [TOP_K n] [METRIC <metric>]
  RETRIEVE <collection> <query_vector> [TOP_K n] [MIN_SCORE <s>]
  CREATE INDEX ON <collection> (<field>) [TYPE <type>]
  BACKUP TO <path>
  INFO

EXAMPLES:
  CREATE COLLECTION users TYPE structured
  INSERT INTO users {"name": "Alice", "age": 30}
  SELECT * FROM users WHERE age=30 LIMIT 10
  VECTOR.SEARCH items [0.1, 0.2, 0.3] TOP_K 5 METRIC cosine
  RETRIEVE knowledge [0.5, 0.1, ...] TOP_K 3 MIN_SCORE 0.7
  INFO
"""

COMMANDS = {
    "CREATE COLLECTION": "create_collection",
    "INSERT INTO": "insert",
    "SELECT": "select",
    "UPDATE": "update",
    "DELETE FROM": "delete",
    "KV.SET": "kv_set",
    "KV.GET": "kv_get",
    "KV.DEL": "kv_del",
    "VECTOR.INSERT": "vector_insert",
    "VECTOR.SEARCH": "vector_search",
    "EMBED.STORE": "embed_store",
    "EMBED.SEARCH": "embed_search",
    "RETRIEVE": "retrieve",
    "CREATE INDEX": "create_index",
    "BACKUP TO": "backup",
    "INFO": "info",
}
