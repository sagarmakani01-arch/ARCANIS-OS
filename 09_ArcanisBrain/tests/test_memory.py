import pytest
from arcanis_brain import ArcanisBrain, BrainConfig
from arcanis_brain.memory.short_term import ShortTermMemory
from arcanis_brain.memory.long_term import LongTermMemory
from arcanis_brain.memory.preferences import UserPreferences
from arcanis_brain.memory.knowledge import KnowledgeBase
from arcanis_brain.core.types import MemoryItem, MemoryType


@pytest.fixture
def brain():
    return ArcanisBrain(BrainConfig())


class TestShortTermMemory:
    def test_remember_and_recall(self, brain):
        stm = ShortTermMemory(brain, capacity=10)
        item = MemoryItem(content="test memory", tags=["test"])
        stm.remember(item)
        results = stm.recall("test")
        assert len(results) == 1
        assert results[0].content == "test memory"

    def test_capacity_eviction(self, brain):
        stm = ShortTermMemory(brain, capacity=3)
        for i in range(5):
            stm.remember(MemoryItem(content=f"item {i}"))
        assert len(stm._items) <= 3

    def test_forget(self, brain):
        stm = ShortTermMemory(brain)
        item = MemoryItem(content="forget me")
        stm.remember(item)
        stm.forget(item.key)
        assert len(stm._items) == 0


class TestLongTermMemory:
    @pytest.mark.asyncio
    async def test_store_and_search(self, brain):
        ltm = LongTermMemory(brain)
        item = MemoryItem(content="Python is a programming language", tags=["python", "programming"])
        await ltm.store(item)
        results = await ltm.search("python")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_persistence(self, brain, tmp_path):
        brain.config.storage_path = str(tmp_path)
        ltm = LongTermMemory(brain)
        item = MemoryItem(content="persist test")
        await ltm.store(item)
        await ltm.save()

        ltm2 = LongTermMemory(brain)
        await ltm2.load()
        results = await ltm2.search("persist")
        assert len(results) >= 1


class TestUserPreferences:
    @pytest.mark.asyncio
    async def test_set_and_get(self, brain):
        prefs = UserPreferences(brain)
        prefs.set("user1", "theme", "dark")
        assert prefs.get("user1", "theme") == "dark"
        assert prefs.get("user1", "nonexistent", "default") == "default"

    @pytest.mark.asyncio
    async def test_learn_from_interaction(self, brain):
        prefs = UserPreferences(brain)
        prefs.learn_from_interaction("user1", {"sentiment": "positive", "topics": ["python", "AI"]})
        profile = prefs.get_all("user1")
        assert "sentiment_history" in profile
        assert profile["topic_interests"]["python"] == 1


class TestKnowledgeBase:
    @pytest.mark.asyncio
    async def test_store_and_query(self, brain):
        kb = KnowledgeBase(brain)
        await kb.store("python_intro", "Python is versatile", tags=["python"])
        results = await kb.query("python")
        assert len(results) >= 1
