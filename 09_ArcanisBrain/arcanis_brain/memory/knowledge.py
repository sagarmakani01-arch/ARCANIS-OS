import json
import os
from typing import Any, Optional
from pathlib import Path


class KnowledgeBase:
    def __init__(self, brain):
        self.brain = brain
        self._entries: dict[str, dict] = {}
        self._storage_path = Path(
            os.path.expanduser(self.brain.config.storage_path)
        ) / "knowledge.json"

    async def load(self):
        if self._storage_path.exists():
            try:
                self._entries = json.loads(self._storage_path.read_text())
            except json.JSONDecodeError:
                self._entries = {}

    async def save(self):
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(json.dumps(self._entries, indent=2))

    async def store(self, key: str, data: Any, tags: list[str] = None, source: str = ""):
        self._entries[key] = {
            "data": data,
            "tags": tags or [],
            "source": source,
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }

    async def query(self, query: str, limit: int = 5) -> list[dict]:
        query_lower = query.lower()
        scored = []
        for key, entry in self._entries.items():
            score = 0.0
            if query_lower in key.lower():
                score += 1.0
            for tag in entry.get("tags", []):
                if query_lower in tag.lower():
                    score += 0.5
            if isinstance(entry.get("data"), str) and query_lower in entry["data"].lower():
                score += 0.3
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    async def get(self, key: str) -> Optional[Any]:
        entry = self._entries.get(key)
        return entry["data"] if entry else None

    async def delete(self, key: str):
        self._entries.pop(key, None)

    async def search_by_tag(self, tag: str) -> list[dict]:
        return [e for e in self._entries.values() if tag in e.get("tags", [])]
