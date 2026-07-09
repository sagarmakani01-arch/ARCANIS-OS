import json
import os
from typing import Any, Optional
from pathlib import Path


class UserPreferences:
    def __init__(self, brain):
        self.brain = brain
        self._prefs: dict[str, dict] = {}
        self._storage_path = Path(
            os.path.expanduser(self.brain.config.storage_path)
        ) / "preferences.json"

    async def load(self):
        if self._storage_path.exists():
            try:
                self._prefs = json.loads(self._storage_path.read_text())
            except json.JSONDecodeError:
                self._prefs = {}

    async def save(self):
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(json.dumps(self._prefs, indent=2))

    def get(self, user_id: str, key: str, default: Any = None) -> Any:
        return self._prefs.get(user_id, {}).get(key, default)

    def get_all(self, user_id: str = "") -> dict:
        if user_id:
            return self._prefs.get(user_id, {})
        return self._prefs

    def set(self, user_id: str, key: str, value: Any):
        if user_id not in self._prefs:
            self._prefs[user_id] = {}
        self._prefs[user_id][key] = value
        self.brain.event_bus.emit("preferences.updated", {"user_id": user_id, "key": key})

    def update(self, user_id: str, prefs: dict):
        if user_id not in self._prefs:
            self._prefs[user_id] = {}
        self._prefs[user_id].update(prefs)

    def learn_from_interaction(self, user_id: str, interaction: dict):
        current = self._prefs.get(user_id, {})
        if "sentiment" in interaction:
            sentiment = interaction["sentiment"]
            current.setdefault("sentiment_history", []).append(sentiment)
        if "topics" in interaction:
            current.setdefault("topic_interests", {})
            for topic in interaction["topics"]:
                current["topic_interests"][topic] = current["topic_interests"].get(topic, 0) + 1
        self._prefs[user_id] = current
