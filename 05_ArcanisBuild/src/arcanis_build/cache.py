"""Build cache - content-addressable storage for build artifacts."""

import json
import os
import hashlib
import shutil
from typing import Dict, Optional, Any


class CacheEntry:
    def __init__(self, key: str, artifact_path: str, metadata: Dict = None):
        self.key = key
        self.artifact_path = artifact_path
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "artifact_path": self.artifact_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        return cls(data["key"], data["artifact_path"], data.get("metadata", {}))


class BuildCache:
    def __init__(self, cache_dir: str = ".arcanis-cache"):
        self.cache_dir = cache_dir
        self._entries_file = os.path.join(cache_dir, "entries.json")
        self._entries: Dict[str, CacheEntry] = {}
        self._ensure_cache_dir()
        self._load()

    def _ensure_cache_dir(self):
        os.makedirs(self.cache_dir, exist_ok=True)

    def _load(self):
        if os.path.exists(self._entries_file):
            try:
                with open(self._entries_file, "r") as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        self._entries[key] = CacheEntry.from_dict(entry_data)
            except (json.JSONDecodeError, KeyError):
                self._entries = {}

    def _save(self):
        data = {key: entry.to_dict() for key, entry in self._entries.items()}
        with open(self._entries_file, "w") as f:
            json.dump(data, f, indent=2)

    def _make_key(self, target: str, inputs: Dict[str, str]) -> str:
        hasher = hashlib.sha256()
        hasher.update(target.encode())
        for name, content_hash in sorted(inputs.items()):
            hasher.update(f"{name}:{content_hash}".encode())
        return hasher.hexdigest()

    def get(self, target: str, inputs: Dict[str, str]) -> Optional[str]:
        key = self._make_key(target, inputs)
        entry = self._entries.get(key)
        if entry and os.path.exists(entry.artifact_path):
            return entry.artifact_path
        return None

    def put(self, target: str, inputs: Dict[str, str], artifact_path: str, metadata: Dict = None):
        key = self._make_key(target, inputs)
        cache_path = os.path.join(self.cache_dir, key)
        if os.path.exists(artifact_path):
            if os.path.isdir(artifact_path):
                if os.path.exists(cache_path):
                    shutil.rmtree(cache_path)
                shutil.copytree(artifact_path, cache_path)
            else:
                shutil.copy2(artifact_path, cache_path)

        self._entries[key] = CacheEntry(key, cache_path, metadata)
        self._save()

    def clear(self):
        self._entries = {}
        if os.path.exists(self._entries_file):
            os.remove(self._entries_file)
        if os.path.exists(self.cache_dir):
            for item in os.listdir(self.cache_dir):
                item_path = os.path.join(self.cache_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                else:
                    shutil.rmtree(item_path)
            os.rmdir(self.cache_dir)

    def stats(self) -> dict:
        return {
            "entries": len(self._entries),
            "cache_dir": self.cache_dir,
            "size_bytes": sum(
                os.path.getsize(e.artifact_path)
                for e in self._entries.values()
                if os.path.exists(e.artifact_path)
            ),
        }

    def prune(self, max_entries: int = 1000):
        if len(self._entries) <= max_entries:
            return
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].metadata.get("timestamp", 0),
        )
        for key, _ in sorted_entries[:-max_entries]:
            entry = self._entries.pop(key)
            if os.path.exists(entry.artifact_path):
                if os.path.isdir(entry.artifact_path):
                    shutil.rmtree(entry.artifact_path)
                else:
                    os.remove(entry.artifact_path)
        self._save()
