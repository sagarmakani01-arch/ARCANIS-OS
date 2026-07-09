from collections import OrderedDict
from typing import Optional
from datetime import datetime, timezone
from arcanis_brain.core.types import MemoryItem, MemoryType


class ShortTermMemory:
    def __init__(self, brain, capacity: int = 100, ttl_seconds: int = 3600):
        self.brain = brain
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._items: OrderedDict[str, MemoryItem] = OrderedDict()

    def remember(self, item: MemoryItem):
        if item.expires_at is None:
            from datetime import timedelta
            item.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)
        self._items[item.key] = item
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def recall(self, query: str, limit: int = 10) -> list[MemoryItem]:
        self._evict_expired()
        query_lower = query.lower()
        scored = []
        for item in self._items.values():
            score = 0.0
            for tag in item.tags:
                if tag.lower() in query_lower:
                    score += 0.3
            if any(w in item.content.lower() for w in query_lower.split()):
                score += 0.5
            score += item.importance * 0.2
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def forget(self, key: str):
        self._items.pop(key, None)

    def clear(self):
        self._items.clear()

    def _evict_expired(self):
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._items.items() if v.expires_at and v.expires_at < now]
        for k in expired:
            del self._items[k]
