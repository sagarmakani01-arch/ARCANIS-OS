# ArcanisMemory Documentation

**Path:** `docs/README.md`
**Version:** 0.1.0
**Status:** Alpha

ArcanisMemory gives agents (notably ArcanisBrain) the ability to remember information, preferences, projects, and experiences. This document provides an overview of the architecture, usage patterns, and key API concepts.

## Architecture Overview

ArcanisMemory builds on the following principals:

1. **Memory Types** – Five distinct types for different kinds of data
   - `SHORT_TERM`: Volatile conversation memory (session-scoped)
   - `LONG_TERM`: Durable personal memory (user-scoped)
   - `PROJECT`: Project-scoped facts, goals, and state
   - `KNOWLEDGE`: Domain facts and learned concepts
   - `EVENT`: Timestamped history of what happened

2. **Storage Layers** –
   - **ArcanisDatabase** – Production storage with KV, vector, and metadata stores
   - **InMemoryStore** – Fast, ephemeral storage for tests and short-lived sessions
   - **MemoryEngine** – Main facade that manages both stores

3. **AI Integration** – Automatic embedding generation, semantic search, and relationship detection

4. **Security** – Capability-based permissions and optional encryption at rest

## Key Data Models

```python
from arcanis_memory import Memory, MemoryType, MemoryScope, MemoryImportance, MemoryID

memory = Memory(
    content="User prefers dark mode",
    memory_type=MemoryType.LONG_TERM,
    user_id="alice",
    tags=["preferences", "ui"],
    importance=0.9,
)
```

- **MemoryID** – UUID hex string
- **MemoryScope** – Aggregation of where a memory lives (global, user, project, session)
- **MemoryImportance** – Importance band (TRIVIAL, LOW, MEDIUM, HIGH, CRITICAL)

## MemoryAPI Usage Examples

```python
import asyncio
from arcanis_memory import MemoryAPI, MemoryType

async def example():
    api = MemoryAPI()
    await api.initialize()

    # Store a long-term preference
    await api.store(
        content="User prefers dark mode",
        memory_type="LONG_TERM",
        user_id="alice",
        tags=["preferences", "ui"],
        importance=0.9,
    )

    # Store a project fact
    await api.store(
        content="Project uses FastAPI for REST APIs",
        memory_type="PROJECT",
        user_id="alice",
        project_id="web-services",
        tags=["project", "tech"],
        importance=0.8,
    )

    # Search semantically
    results = await api.search("dark mode", user_id="alice", memory_type="LONG_TERM")
    print(results)

    # Get context for a prompt
    context = await api.build_context("user interface preferences", user_id="alice")
    print(context)

    await api.shutdown()

asyncio.run(example())
```

### Batch Operations

```python
# Store many memories at once
memories = [api.store(content=f"Fact {i}", memory_type="KNOWLEDGE") for i in range(10)]

# Recall with filters
results = await api.recall(user_id="alice", memory_type="PROJECT", limit=50)
```

### Integration with ArcanisBrain

```python
from arcanis_memory.integration import BrainAdapter
from arcanis_memory import MemoryEngine

engine = MemoryEngine()
brain_adapter = BrainAdapter(engine)

# ArcanisBrain can delegate directly to engine:
await brain_adapter.store_interaction(
    user_input="Show me my settings",
    response="You prefer dark mode",
    user_id="alice",
)

context = await brain_adapter.get_relevant_context(
    "What are my UI preferences?",
    user_id="alice",
)
```

## CLI Quick Start

### Installation

```bash
pip install arcanis-memory[crypto]    # Include crypto backend
pip install arcanis-memory[dev]       # Include development tools
```

### Environment Setup

```bash
# Initialize a persistent store
export ARCANIS_MEMORY_PATH="~/.arcanis/memory"
export ARCANIS_STORAGE_KEY="your-encryption-key"
```

### Usage

```bash
python -c "
import asyncio
from arcanis_memory import MemoryAPI

async def run():
    api = MemoryAPI()
    await api.initialize()
    m = await api.store('Hello memory!', memory_type='SHORT_TERM', session_id='demo')
    print(f'Stored memory ID: {m.memory_id}')
    await api.shutdown()

asyncio.run(run())
"
```

## Integration Patterns

### ArcanisDatabase Integration

ArcanisMemory integrates with ArcanisDatabase's storage (KV, vector, and metadata stores) for persistent, encrypted storage.

**Enable with:**
```python
from arcanis_memory import MemoryAPI, MemoryConfig

config = MemoryConfig(
    storage_backend="arcanisdb",
    storage_path="~/.arcanis/memory/data.db",
    encryption_key="your-secret-key",
)
api = MemoryAPI(config)
```

### Semantic Search Capabilities

- Automatic embedding generation (text-to-vector)
- Cosine similarity search with configurable metrics (`cosine`, `dot`, `euclidean`)
- Integration with ArcanisDatabase's vector store when available
- Fallback to keyword overlap scoring

### Memory Relationship Management

ArcanisMemory can detect and store relationships between memories:

```python
from arcanis_memory import MemoryAPI

# Get relevant memories for relationship detection
candidates = await api.recall(user_id="alice", limit=50)
memory = ... # existing memory

# Detect relationships
relationships = await api.ai.detect_relationships(memory, candidates)
for related, rel_type, strength in relationships:
    await api.relate(memory.memory_id, related.memory_id, rel_type, strength)
```

### Permission Management

Control access to memories through capability-based permissions:

```python
from arcanis_memory import MemoryAPI

# Grant an agent WRITE permission on user's memories
api.grant("agent-1", "user:alice", "WRITE")

# Check if operation is allowed
if api.security.can_write("agent-1", MemoryScope.USER, "alice"):
    await api.store(content="New memory", user_id="alice")
```

## Migration Guide

### From InMemoryStore to DatabaseBackedStore

1. **Configuration:** Ensure `storage_backend="arcanisdb"` and set `storage_path`
2. **Security:** Add `encryption_key` for encrypted persistence
3. **Data Migration:** Data is stored as-is; integrity maintained through ArcanisDatabase's transaction system

### From Old Storage Format

If migrating from an older version of ArcanisMemory:

```python
from arcanis_memory.storage.store import DatabaseBackedStore

# Old data converted to new format
# Use ArcanisDatabaseMigrationHelper (TBD)
```

## Performance Considerations

### Cache Usage

- **Similarity Search:** In-memory cache (max 5000 recent vectors) when using ArcanisDatabase
- **Query Result Cache:** Results cached for up to 5 minutes (configurable)
- **Embedding Cache:** Embeddings cached to avoid recomputation

### Bandwidth Optimization

- **Lazy Loading:** Memories fetched only when accessed
- **Batch Operations:** Use `insert_many`, `store_many` for high-throughput scenarios
- **Compression:** Memory content can be compressed (configurable)

## Testing Strategies

### Unit Tests

Use Python's `unittest` or `pytest` with coverage targeting:

```python
import unittest
from arcanis_memory import MemoryEngine
from arcanis_memory.core.types import MemoryType

class TestMemoryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MemoryEngine()

    def test_store_recall(self):
        memory = self.engine.store_sync(
            content="Test memory",
            memory_type=MemoryType.LONG_TERM,
        )
        recalled = self.engine.recall_sync(user_id=memory.user_id)
        self.assertEqual(memory.memory_id, recalled[0].memory_id)
```

### Integration Tests

Test end-to-end scenarios:

```python
import asyncio
from arcanis_memory.integration import DatabaseAdapter

async def database_integration():
    adapter = DatabaseAdapter(path="test.db")
    store = adapter.store()

    # Test full persistence roundtrip
    memory = Memory(
        content="Integration test",
        memory_type=MemoryType.EVENT,
    )
    memory_id = store.insert(memory)
    retrieved = store.get(memory_id)

    assert retrieved.content == memory.content
    adapter.close()
```

### Functional Tests

Test through the public API:

```python
from arcanis_memory import MemoryAPI

async def functional_test():
    api = MemoryAPI()
    await api.initialize()

    # Test complete workflow
    stored = await api.store("Functional test content", memory_type="SHORT_TERM")
    searched = await api.search("test content")
    context = await api.build_context("functional")

    await api.shutdown()
```

## Troubleshooting

### Module Not Found Errors

```bash
pip install arcanis-memory[crypto,dev]
```

### Encryption Key Issues

```python
# Ensure you have the same encryption key across sessions
config = MemoryConfig(encryption_key="your-secret-key")
```

### Semantic Search Failures

```python
# Check embedding dimension consistency
config = MemoryConfig(embedding_dim=1536)
```

### MemoryExpiration

Configure TTL per memory type or globally:

```python
config = MemoryConfig(default_ttl_seconds={
    "SHORT_TERM": 3600,
    "EVENT": 31536000,
})
```

## Contributing

### Standards Compliance

- Follow [Testing Standards](00_Documentation/standards/testing-standards.md)
- Follow [Documentation Standards](00_Documentation/standards/documentation-standards.md)

### Code Guidelines

- Maintain ≥90% unit test coverage
- Write docstrings in Google style
- Preserve separation of concerns (engine, manager, store, AI)

### Running Tests

```bash
# Install dev dependencies
pip install arcanis-memory[dev]

# Run unit tests
cd tests
pytest unit/

# Run integration tests  
pytest integration/

# Run all tests
pytest
```

## References

- [ArcanisDatabase API](https://github.com/arcanisdb/arcanisdb)
- [ArcanisBrain Architecture](https://github.com/arcanisbrain/arcanisbrain)
- [ArcanisProject Documentation Structure](00_Documentation/standards/repository-structure.md)
- [AI Features](ai/features.py) – Semantic search, context building, summarization, relationships
- [Security Layer](security/policy.py) – Permissions and encryption
- [Storage Layer](storage/store.py) – DatabaseBackedStore and InMemoryStore implementations

---

*ArcanisMemory is built for intelligence, autonomy, and scale. It trusts the AI to remember what matters, forgets what should fade, and learns from what is forgotten.*
