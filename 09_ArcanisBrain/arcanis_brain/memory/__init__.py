from arcanis_brain.memory.short_term import ShortTermMemory
from arcanis_brain.memory.long_term import LongTermMemory
from arcanis_brain.memory.preferences import UserPreferences
from arcanis_brain.memory.knowledge import KnowledgeBase
from arcanis_brain.core.types import MemoryItem, MemoryType


class MemoryModule:
    def __init__(self, brain):
        self.brain = brain
        self.short_term = ShortTermMemory(brain)
        self.long_term = LongTermMemory(brain)
        self.preferences = UserPreferences(brain)
        self.knowledge = KnowledgeBase(brain)

    async def initialize(self):
        await self.long_term.load()
        await self.preferences.load()
        await self.knowledge.load()

    async def get_relevant_context(self, query: str) -> dict:
        stm = self.short_term.recall(query)
        ltm = await self.long_term.search(query)
        prefs = self.preferences.get_all()
        kls = await self.knowledge.query(query)
        return {
            "short_term": stm,
            "long_term": ltm[:5],
            "preferences": prefs,
            "knowledge": kls[:3],
        }

    async def store_interaction(self, user_input: str, response: str, user_id: str):
        item = MemoryItem(content=f"User: {user_input}\nAssistant: {response}", tags=["interaction"])
        self.short_term.remember(item)
        await self.long_term.store(item)

    async def persist(self):
        await self.long_term.save()
        await self.preferences.save()
        await self.knowledge.save()


__all__ = ["MemoryModule", "ShortTermMemory", "LongTermMemory", "UserPreferences", "KnowledgeBase"]
