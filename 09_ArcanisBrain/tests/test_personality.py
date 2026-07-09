import pytest
from arcanis_brain import ArcanisBrain, BrainConfig
from arcanis_brain.personality.context import ContextAwareness
from arcanis_brain.personality.style import CommunicationStyle
from arcanis_brain.personality.adaptation import UserAdaptation


@pytest.fixture
def brain():
    return ArcanisBrain(BrainConfig())


class TestContextAwareness:
    def test_enrich(self, brain):
        ctx = ContextAwareness(brain)
        enriched = ctx.enrich("Write Python code for a function", "user1")
        assert enriched["user_id"] == "user1"
        assert "code" in enriched["topics"]

    def test_empty_conversation_summary(self, brain):
        ctx = ContextAwareness(brain)
        summary = ctx.get_conversation_summary()
        assert summary == "No prior conversation."


class TestCommunicationStyle:
    def test_default_style(self, brain):
        style = CommunicationStyle(brain)
        result = style.apply("Hello world. This is a test.", {})
        assert len(result) > 0

    def test_concise_verbosity(self, brain):
        style = CommunicationStyle(brain)
        result = style.apply("Sentence one. Sentence two. Sentence three. Sentence four.", {"verbosity": "concise"})
        assert len(result.split(". ")) <= 3


class TestUserAdaptation:
    def test_default_profile(self, brain):
        adapt = UserAdaptation(brain)
        profile = adapt.get_profile("unknown_user")
        assert profile["expertise_level"] == "intermediate"

    def test_learn(self, brain):
        adapt = UserAdaptation(brain)
        adapt.learn("user1", {"sentiment": "positive", "topics": ["AI"]})
        profile = adapt.get_profile("user1")
        assert "topics_of_interest" in profile
