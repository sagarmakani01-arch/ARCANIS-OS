"""Shared memory.

A scoped, namespaced key/value store with TTL and change events.
"""

from __future__ import annotations

import enum
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class MemoryScope(enum.Enum):
    GLOBAL = "global"
    AGENT = "agent"
    TASK = "task"


@dataclass
class MemoryEntry:
    value: Any
    owner: str
    scope: MemoryScope
    expires_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


_SENTINEL = object()


class SharedMemory:
    """Thread-safe shared memory with namespaces, TTL and change events."""

    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._listeners: list[Callable[[str, Any, Any], None]] = []

    def _key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        owner: str = "system",
        scope: MemoryScope = MemoryScope.GLOBAL,
        ttl: Optional[float] = None,
    ) -> str:
        full = self._key(namespace, key)
        expires_at = time.time() + ttl if ttl else None
        with self._lock:
            old = self._store.get(full)
            entry = MemoryEntry(value=value, owner=owner, scope=scope, expires_at=expires_at)
            self._store[full] = entry
        self._emit(full, old.value if old else None, value)
        return full

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        full = self._key(namespace, key)
        with self._lock:
            entry = self._store.get(full)
            if entry is None:
                return default
            if entry.expires_at and time.time() > entry.expires_at:
                self._store.pop(full, None)
                return default
            return entry.value

    def exists(self, namespace: str, key: str) -> bool:
        return self.get(namespace, key, _SENTINEL) is not _SENTINEL

    def delete(self, namespace: str, key: str) -> bool:
        full = self._key(namespace, key)
        with self._lock:
            entry = self._store.pop(full, None)
        if entry:
            self._emit(full, entry.value, None)
        return entry is not None

    def keys(self, namespace: str) -> list[str]:
        prefix = f"{namespace}:"
        with self._lock:
            return [k[len(prefix):] for k in self._store if k.startswith(prefix)]

    def snapshot(self, namespace: str) -> dict[str, Any]:
        prefix = f"{namespace}:"
        out: dict[str, Any] = {}
        with self._lock:
            for k, entry in self._store.items():
                if k.startswith(prefix):
                    if entry.expires_at and time.time() > entry.expires_at:
                        continue
                    out[k[len(prefix):]] = entry.value
        return out

    def on_change(self, fn: Callable[[str, Any, Any], None]) -> None:
        self._listeners.append(fn)

    def _emit(self, key: str, old: Any, new: Any) -> None:
        for fn in self._listeners:
            try:
                fn(key, old, new)
            except Exception:
                pass
