from typing import Any


class ContextAwareness:
    def __init__(self, brain):
        self.brain = brain

    def enrich(self, user_input: str, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "session_id": self.brain.context.session_id,
            "input_length": len(user_input),
            "topics": self._extract_topics(user_input),
            "interaction_count": len(self.brain.context.conversation_history),
        }

    def _extract_topics(self, text: str) -> list[str]:
        topics = []
        keywords = {
            "code": ["code", "function", "class", "api", "program"],
            "data": ["data", "database", "storage", "memory"],
            "security": ["security", "permission", "safe", "protect"],
            "ai": ["ai", "model", "learning", "neural"],
            "system": ["system", "config", "deploy", "infra"],
        }
        text_lower = text.lower()
        for topic, words in keywords.items():
            if any(w in text_lower for w in words):
                topics.append(topic)
        return topics

    def get_conversation_summary(self) -> str:
        history = self.brain.context.conversation_history
        if not history:
            return "No prior conversation."
        recent = history[-5:]
        return f"Last {len(recent)} messages. Recent topics: {self._extract_topics(' '.join(m.content for m in recent))}"
