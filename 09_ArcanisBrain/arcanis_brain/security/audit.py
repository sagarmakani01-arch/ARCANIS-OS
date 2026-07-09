from typing import Any, Optional
from datetime import datetime, timezone
import json
import os
from pathlib import Path


class AuditLogger:
    def __init__(self, brain):
        self.brain = brain
        self._log: list[dict] = []
        self._storage_path = Path(
            os.path.expanduser(self.brain.config.storage_path)
        ) / "audit.jsonl"

    def log(self, event_type: str, data: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "session_id": self.brain.context.session_id,
            "user_id": self.brain.context.user_id,
            **data,
        }
        self._log.append(entry)
        self.brain.event_bus.emit("audit.logged", entry)
        if self.brain.config.enable_audit:
            self._persist(entry)

    def _persist(self, entry: dict):
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._storage_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def query(self, event_type: Optional[str] = None, user_id: Optional[str] = None, limit: int = 100) -> list[dict]:
        results = self._log
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        if user_id:
            results = [e for e in results if e["user_id"] == user_id]
        return results[-limit:]

    def get_recent(self, n: int = 10) -> list[dict]:
        return self._log[-n:]

    def clear(self):
        self._log.clear()
