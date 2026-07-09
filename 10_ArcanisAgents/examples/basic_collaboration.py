"""Example: basic multi-agent collaboration."""

import asyncio
from arcanis_agents import API, AgentCapability

async def main():
    api = API()
    api.spawn_default_agents()
    api.start()
    print("== Basic Collaboration ==\n")

    dev = await api.run_task("Implement login", AgentCapability.WRITE_CODE, {"action": "write_code"})
    print("Developer:", dev.result)

    sec = await api.run_task("Scan code", AgentCapability.SECURITY_SCAN, {"code": "password='x'\neval(y)"})
    print("Security:", sec.result)

    res = await api.run_task("Research OAuth2", AgentCapability.RESEARCH, {"action": "research"})
    print("Research:", res.result)

    auto = await api.run_task("Deploy pipeline", AgentCapability.AUTOMATE, {"steps": ["build", "test", "deploy"]})
    print("Automation:", auto.result)

    sys_task = await api.run_task("Health check", AgentCapability.OS_TASK)
    print("System:", sys_task.result)

    print("\nStatus:", api.status())
    await api.stop()

asyncio.run(main())
