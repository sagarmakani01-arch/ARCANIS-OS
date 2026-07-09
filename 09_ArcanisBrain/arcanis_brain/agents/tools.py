from typing import Any, Callable, Optional
import inspect


class ToolRegistry:
    def __init__(self, brain):
        self.brain = brain
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, handler: Callable):
        self._tools[name] = handler

    async def execute(self, name: str, params: dict, context: Any = None) -> Any:
        handler = self._tools.get(name)
        if not handler:
            if name in self._builtins():
                return await self._builtins()[name](params, context)
            raise ValueError(f"Unknown tool: {name}")
        if inspect.iscoroutinefunction(handler):
            return await handler(params, context)
        return handler(params, context)

    def _builtins(self) -> dict:
        return {
            "reason": self._tool_reason,
            "memory": self._tool_memory,
            "search": self._tool_search,
            "analyze": self._tool_analyze,
            "compose": self._tool_compose,
            "generation": self._tool_generation,
            "computation": self._tool_computation,
            "retrieval": self._tool_retrieval,
        }

    async def _tool_reason(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "output": f"Reasoned about: {params.get('description', '')}"}

    async def _tool_memory(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "context": "Memory context retrieved"}

    async def _tool_search(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "results": [f"Result for {params.get('description', 'query')}"]}

    async def _tool_analyze(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "analysis": f"Analysis complete for: {params.get('description', '')}"}

    async def _tool_compose(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "response": "Response composed"}

    async def _tool_generation(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "generated": f"Generated content for: {params.get('description', '')}"}

    async def _tool_computation(self, params: dict, context: Any) -> dict:
        return {"status": "ok", "result": "Computation complete"}

    async def _tool_retrieval(self, params: dict, context: Any) -> dict:
        return await self._tool_search(params, context)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys()) + list(self._builtins().keys())
