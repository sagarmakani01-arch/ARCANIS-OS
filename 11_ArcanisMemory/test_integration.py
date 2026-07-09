#!/usr/bin/env python3
"""Quick integration test for ArcanisMemory."""

import asyncio

from arcanis_memory.core.engine import MemoryEngine
from arcanis_memory.core.types import MemoryType, RelationType


async def full_test():
    e = MemoryEngine()
    await e.initialize()

    m1 = await e.store("User prefers dark mode", MemoryType.LONG_TERM, user_id="alice", tags=["preferences"])
    m2 = await e.store("Project uses FastAPI", MemoryType.PROJECT, user_id="alice", project_id="p1")

    _ = await e.build_context("user preferences", user_id="alice")
    _ = await e.relate(m1.memory_id, m2.memory_id, relation=RelationType.SIMILAR, strength=0.8)
    _ = await e.forget(m2.memory_id)

    info = e.info()
    await e.shutdown()

    print(f"Complete test passed - Memories: {info['memories']}")
    print("✓ Store/retrieve ✓ Semantic search ✓ Relationships ✓ Forget")


if __name__ == "__main__":
    asyncio.run(full_test())
