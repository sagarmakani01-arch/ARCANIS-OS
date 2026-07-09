from typing import Any


class UserAdaptation:
    def __init__(self, brain):
        self.brain = brain
        self._default_profile = {
            "expertise_level": "intermediate",
            "preferred_language": "en",
            "communication_pace": "normal",
            "topics_of_interest": [],
        }

    def get_profile(self, user_id: str) -> dict:
        prefs = self.brain.memory.preferences.get_all(user_id)
        return {
            "expertise_level": prefs.get("expertise_level", self._default_profile["expertise_level"]),
            "preferred_language": prefs.get("preferred_language", self._default_profile["preferred_language"]),
            "communication_pace": prefs.get("communication_pace", self._default_profile["communication_pace"]),
            "topics_of_interest": prefs.get("topic_interests", {}),
        }

    def adapt_input(self, user_input: str, profile: dict) -> str:
        return user_input

    def learn(self, user_id: str, interaction: dict):
        self.brain.memory.preferences.learn_from_interaction(user_id, interaction)

    def estimate_expertise(self, user_id: str, query: str) -> str:
        profile = self.get_profile(user_id)
        topics = profile.get("topics_of_interest", {})
        topic_depth = sum(topics.values()) if isinstance(topics, dict) else 0
        if topic_depth > 50:
            return "expert"
        elif topic_depth > 10:
            return "intermediate"
        return "beginner"
