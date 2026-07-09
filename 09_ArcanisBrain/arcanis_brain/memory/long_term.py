from typing import Optional
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from arcanis_brain.core.types import MemoryItem, MemoryType


class LongTermMemory:
    def __init__(self, brain, max_items: int = 10000):
        self.brain = brain
        self.max_items = max_items
        self._items: dict[str, MemoryItem] = {}
        self._storage_path = Path(
            os.path.expanduser(self.brain.config.storage_path)
        ) / "long_term_memory.json"

    async def store(self, item: MemoryItem):
        self._items[item.key] = item
        if len(self._items) > self.max_items:
            oldest = min(self._items.keys(), key=lambda k: self._items[k].created_at)
            del self._items[oldest]

    async def search(self, query: str, limit: int = 10) -> list[MemoryItem]:
        query_lower = query.lower()
        scored = []
        for item in self._items.values():
            score = 0.0
            query_words = set(query_lower.split())
            content_words = set(item.content.lower().split())
            overlap = query_words & content_words
            score += len(overlap) / max(len(query_words), 1)
            tag_overlap = [t for t in item.tags if t.lower() in query_lower]
            score += len(tag_overlap) * 0.2
            score += item.importance * 0.3
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    async def get(self, key: str) -> Optional[MemoryItem]:
        item = self._items.get(key)
        if item:
            item.access_count += 1
        return item

    async def delete(self, key: str):
        self._items.pop(key, None)

    async def load(self):
        if self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text())
                for d in data:
                    d["memory_type"] = MemoryType[d["memory_type"]]
                    d["created_at"] = datetime.fromisoformat(d["created_at"])
                    if d.get("expires_at"):
                        d["expires_at"] = datetime.fromisoformat(d["expires_at"])
                    self._items[d["key"]] = MemoryItem(**d)
            except (json.JSONDecodeError, KeyError):
                pass

    async def save(self):
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = []
        for item in self._items.values():
            d = {k: v for k, v in item.__dict__.items()}
            d["memory_type"] = item.memory_type.name
            d["created_at"] = item.created_at.isoformat()
            d["expires_at"] = item.expires_at.isoformat() if item.expires_at else None
            data.append(d)
        self._storage_path.write_text(json.dumps(data, indent=2))
