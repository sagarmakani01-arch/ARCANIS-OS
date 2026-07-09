from arcanis_brain.personality.context import ContextAwareness
from arcanis_brain.personality.style import CommunicationStyle
from arcanis_brain.personality.adaptation import UserAdaptation


class PersonalityModule:
    def __init__(self, brain):
        self.brain = brain
        self.context = ContextAwareness(brain)
        self.style = CommunicationStyle(brain)
        self.adaptation = UserAdaptation(brain)

    def get_profile(self, user_id: str) -> dict:
        return {
            "style": self.style.get_style(user_id),
            "adaptation": self.adaptation.get_profile(user_id),
            "context": {},
        }

    def adapt_input(self, user_input: str, profile: dict) -> str:
        return self.adaptation.adapt_input(user_input, profile)

    def style_response(self, response: str, profile: dict) -> str:
        return self.style.apply(response, profile.get("style", {}))


__all__ = ["PersonalityModule", "ContextAwareness", "CommunicationStyle", "UserAdaptation"]
