"""ArcanisDatabase Quickstart Guide"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from arcanisdb import ArcanisDatabase

# Create an in-memory database
db = ArcanisDatabase()

# --- Structured Data ---
print("=== Structured Data ===")
db.structured.create_collection("users")
alice_id = db.structured.insert("users", {"name": "Alice", "age": 30, "role": "engineer"})
bob_id = db.structured.insert("users", {"name": "Bob", "age": 25, "role": "designer"})
print(f"Inserted Alice (id={alice_id}), Bob (id={bob_id})")

users = db.structured.query("users")
for u in users:
    print(f"  User {u['id']}: {u['data']}")

# --- Key-Value Store ---
print("\n=== Key-Value Store ===")
db.kv.set("config", "theme", "dark")
db.kv.set("config", "language", "python")
print(f"theme = {db.kv.get('config', 'theme')}")
print(f"All keys: {db.kv.list_keys('config')}")

# --- Vector Storage ---
print("\n=== Vector Storage ===")
vec1 = [0.1, 0.2, 0.3, 0.4, 0.5]
vec2 = [0.9, 0.8, 0.7, 0.6, 0.5]
vec3 = [0.15, 0.25, 0.35, 0.45, 0.55]

db.vectors.insert("items", vec1)
db.vectors.insert("items", vec2)
db.vectors.insert("items", vec3)

# Similarity search
results = db.similarity.search("items", [0.12, 0.22, 0.32, 0.42, 0.52], top_k=3)
print(f"Similarity search results:")
for r in results:
    print(f"  id={r['id']}, score={r['score']:.4f}")

# --- Knowledge Retrieval ---
print("\n=== Knowledge Retrieval ===")
knowledge = [
    ("Python is a programming language.", [0.1, 0.2, 0.3]),
    ("SQLite is an embedded database engine.", [0.4, 0.5, 0.6]),
    ("Vectors represent data in high-dimensional space.", [0.7, 0.8, 0.9]),
]
for content, emb in knowledge:
    db.retrieval.store_knowledge("docs", content, emb, {"source": "manual"})

results = db.retrieval.retrieve("docs", [0.15, 0.25, 0.35], top_k=2)
print("Knowledge retrieval results:")
for r in results:
    print(f"  content='{r.get('content', '')}', score={r['score']:.4f}")

# --- ArcanisQL ---
print("\n=== ArcanisQL ===")
result = db.query.execute('SELECT * FROM users LIMIT 10')
print(f"Query result: {result}")

# --- Metadata ---
print("\n=== Metadata ===")
db.metadata.set("assets", "image", "logo.png", "format", "PNG")
db.metadata.set("assets", "image", "logo.png", "size_kb", 42)
meta = db.metadata.get_all("assets", "image", "logo.png")
print(f"Metadata for logo.png: {meta}")

# --- Backup ---
print("\n=== Backup ===")
db2 = ArcanisDatabase("example_backup.db")
db2.structured.create_collection("test")
db2.structured.insert("test", {"msg": "hello"})
backup_path = db2.backup.backup()
print(f"Backup created at: {backup_path}")
db2.close()

# Clean up
import os
os.remove("example_backup.db")
os.remove(backup_path)

print("\nArcanisDatabase quickstart complete!")
