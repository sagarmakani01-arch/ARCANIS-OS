"""Example: agent factory — declarative agent creation."""

import asyncio
from arcanis_agents import API, AgentSpec, AgentCapability, Role, Behavior

async def main():
    api = API()
    spec = AgentSpec(name="Notifier", role=Role.AUTOMATOR, capabilities=[AgentCapability.AUTOMATE], behavior=Behavior.ECHO)
    agent = api.factory.create(spec)
    api.add_agent(agent, roles=[Role.AUTOMATOR])
    api.start()
    task = await api.run_task("Send notification", AgentCapability.AUTOMATE)
    print("Factory agent result:", task.result)
    await api.stop()

asyncio.run(main())
