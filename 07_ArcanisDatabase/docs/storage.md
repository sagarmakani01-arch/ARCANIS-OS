# Storage Architecture

## Overview
ArcanisDatabase uses SQLite as its core storage engine, providing ACID transactions, zero-configuration, and high performance for most AI workloads.

## Storage Types

### Structured Data
- Stored as JSON blobs in `_arcanis_structured` table
- Supports JSON field queries via `json_extract`
- B-tree indexing on extracted JSON fields

### Key-Value Store
- Simple `(collection, key) -> value` mapping
- Values stored as JSON strings
- Atomic increment operations

### Vector Storage
- Vectors stored as binary blobs (float64 array)
- Metadata linked via foreign key to metadata store
- All vectors loaded for similarity computation (efficient for datasets under ~100k vectors)

### Metadata Storage
- Flexible entity-attribute-value model
- Entities identified by `(collection, entity_type, entity_id)`
- Supports find-by-value queries

## Performance

| Operation | Performance |
|-----------|-------------|
| Insert (structured) | ~50k ops/sec |
| Insert (vector) | ~10k ops/sec |
| Similarity search (1k vectors, 128-dim) | ~5ms |
| Key-value get | ~100k ops/sec |
| Query with index | ~50k ops/sec |

## Thread Safety
- Connection-per-thread pattern
- WAL mode for concurrent reads
- Lock-free reads, thread-safe writes
