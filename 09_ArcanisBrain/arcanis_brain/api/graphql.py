from typing import Any


class GraphQLAPI:
    def __init__(self, brain):
        self.brain = brain
        self._schema = {
            "Query": {
                "status": self._resolve_status,
                "memory": self._resolve_memory,
                "preferences": self._resolve_preferences,
                "agents": self._resolve_agents,
                "audit": self._resolve_audit,
            },
            "Mutation": {
                "chat": self._resolve_chat,
                "process": self._resolve_process,
                "updatePreferences": self._resolve_update_preferences,
            },
        }

    async def execute(self, query: str, variables: dict = None) -> dict:
        if "chat" in query or "process" in query:
            return await self._resolve_chat(variables or {})
        if "status" in query:
            return await self._resolve_status()
        if "memory" in query:
            return await self._resolve_memory(variables or {})
        if "preferences" in query and "update" not in query:
            return await self._resolve_preferences(variables or {})
        if "updatePreferences" in query:
            return await self._resolve_update_preferences(variables or {})
        if "agents" in query:
            return await self._resolve_agents()
        if "audit" in query:
            return await self._resolve_audit()
        return {"error": "Unknown query"}

    async def _resolve_status(self, args: dict = None) -> dict:
        return {
            "status": "running",
            "initialized": self.brain._initialized,
            "sessionId": self.brain.context.session_id,
        }

    async def _resolve_memory(self, args: dict = None) -> dict:
        query = (args or {}).get("query", "")
        context = await self.brain.memory.get_relevant_context(query)
        return {"context": context}

    async def _resolve_preferences(self, args: dict = None) -> dict:
        user_id = (args or {}).get("userId", "anonymous")
        return {"preferences": self.brain.memory.preferences.get_all(user_id)}

    async def _resolve_agents(self, args: dict = None) -> list:
        return [a.__dict__ for a in self.brain.agents.registry.list()]

    async def _resolve_audit(self, args: dict = None) -> list:
        return self.brain.security.audit.get_recent((args or {}).get("limit", 50))

    async def _resolve_chat(self, args: dict = None) -> dict:
        args = args or {}
        message = args.get("message", "")
        user_id = args.get("userId", "anonymous")
        response = await self.brain.process(message, user_id)
        return {"response": response}

    async def _resolve_process(self, args: dict = None) -> dict:
        return await self._resolve_chat(args)

    async def _resolve_update_preferences(self, args: dict = None) -> dict:
        args = args or {}
        user_id = args.get("userId", "anonymous")
        prefs = args.get("preferences", {})
        self.brain.memory.preferences.update(user_id, prefs)
        return {"status": "updated"}
