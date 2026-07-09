"""Example: communication protocol (direct RPC)."""

import asyncio
from arcanis_agents import API, ResearchAgent

async def main():
    api = API()
    api.spawn_default_agents()
    api.start()

    research_id = next(a.agent_id for a in api.orchestrator.agents.values() if isinstance(a, ResearchAgent))
    reply = await api.send_message("user", research_id, "research.query", {"query": "vector databases"})
    print("Researcher replied:", reply.payload if reply else None)
    await api.stop()

asyncio.run(main())
