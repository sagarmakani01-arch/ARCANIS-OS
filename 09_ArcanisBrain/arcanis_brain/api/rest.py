from typing import Any
import json


class RestAPI:
    def __init__(self, brain):
        self.brain = brain
        self._routes: dict[str, dict] = {}

    def register_route(self, method: str, path: str, handler: callable):
        key = f"{method.upper()}:{path}"
        self._routes[key] = {"handler": handler, "method": method.upper(), "path": path}

    async def handle_request(self, method: str, path: str, body: Any = None, headers: dict = None) -> dict:
        key = f"{method.upper()}:{path}"
        route = self._routes.get(key)
        if not route:
            key = f"{method.upper()}:/{path.split('/')[1]}/*" if '/' in path else key
            route = self._routes.get(key)

        if not route:
            return {"status": 404, "body": {"error": "Not found"}}

        try:
            result = await route["handler"](body, headers or {})
            return {"status": 200, "body": result}
        except Exception as e:
            return {"status": 500, "body": {"error": str(e)}}

    def register_default_routes(self):
        self.register_route("POST", "/api/chat", self._chat_handler)
        self.register_route("POST", "/api/process", self._process_handler)
        self.register_route("GET", "/api/status", self._status_handler)
        self.register_route("GET", "/api/memory", self._memory_handler)
        self.register_route("POST", "/api/preferences", self._preferences_handler)
        self.register_route("GET", "/api/agents", self._agents_handler)
        self.register_route("GET", "/api/audit", self._audit_handler)

    async def _chat_handler(self, body: dict, headers: dict) -> dict:
        message = body.get("message", "")
        user_id = headers.get("X-User-Id", "anonymous")
        response = await self.brain.process(message, user_id)
        return {"response": response}

    async def _process_handler(self, body: dict, headers: dict) -> dict:
        return await self._chat_handler(body, headers)

    async def _status_handler(self, body: dict, headers: dict) -> dict:
        return {
            "status": "running",
            "initialized": self.brain._initialized,
            "agents": len(self.brain.agents.registry.list()),
            "memory_items": 0,
            "session": self.brain.context.session_id,
        }

    async def _memory_handler(self, body: dict, headers: dict) -> dict:
        query = body.get("query", "") if body else ""
        context = await self.brain.memory.get_relevant_context(query)
        return {"context": context}

    async def _preferences_handler(self, body: dict, headers: dict) -> dict:
        user_id = headers.get("X-User-Id", "anonymous")
        if body and "preferences" in body:
            self.brain.memory.preferences.update(user_id, body["preferences"])
            return {"status": "updated"}
        return {"preferences": self.brain.memory.preferences.get_all(user_id)}

    async def _agents_handler(self, body: dict, headers: dict) -> dict:
        return {"agents": [a.__dict__ for a in self.brain.agents.registry.list()]}

    async def _audit_handler(self, body: dict, headers: dict) -> dict:
        return {"logs": self.brain.security.audit.get_recent(50)}
