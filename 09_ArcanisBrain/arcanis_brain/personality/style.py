from typing import Any


class CommunicationStyle:
    def __init__(self, brain):
        self.brain = brain
        self._default_style = {
            "tone": "professional",
            "verbosity": "balanced",
            "formality": "moderate",
            "use_emoji": False,
        }

    def get_style(self, user_id: str) -> dict:
        prefs = self.brain.memory.preferences.get_all(user_id)
        return {
            "tone": prefs.get("tone", self._default_style["tone"]),
            "verbosity": prefs.get("verbosity", self._default_style["verbosity"]),
            "formality": prefs.get("formality", self._default_style["formality"]),
            "use_emoji": prefs.get("use_emoji", self._default_style["use_emoji"]),
        }

    def apply(self, response: str, style: dict) -> str:
        merged = {**self._default_style, **style}
        result = response
        if merged["verbosity"] == "concise":
            sentences = result.split(". ")
            result = ". ".join(sentences[:min(3, len(sentences))])
        if merged["formality"] == "high":
            result = result.replace("gonna", "going to").replace("wanna", "want to")
        return result

    def set_style(self, user_id: str, style_updates: dict):
        current = self.get_style(user_id)
        current.update(style_updates)
        self.brain.memory.preferences.set(user_id, "tone", current.get("tone"))
        self.brain.memory.preferences.set(user_id, "verbosity", current.get("verbosity"))
        self.brain.memory.preferences.set(user_id, "formality", current.get("formality"))
        self.brain.memory.preferences.set(user_id, "use_emoji", current.get("use_emoji"))
