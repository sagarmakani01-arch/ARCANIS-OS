"""Tests for the ArcanisAgents framework."""

import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arcanis_agents import (
    API, AgentCapability, Permission, Role,
    SharedMemory, MessageBus, Message, MessageType,
)
from arcanis_agents.core.permissions import PermissionSystem
from arcanis_agents.agents.developer import DeveloperAgent
from arcanis_agents.agents.security import SecurityAgent


def run(coro):
    return asyncio.run(coro)


def test_shared_memory_ttl():
    mem = SharedMemory()
    mem.set("ns", "k", "v", ttl=0.01)
    assert mem.get("ns", "k") == "v"
    time.sleep(0.02)
    assert mem.get("ns", "k") is None


def test_permissions_enforced():
    ps = PermissionSystem()
    ps.register_agent("a1", "A1", [Role.DEVELOPER])
    assert ps.check("a1", Permission.CODE_WRITE)
    assert not ps.check("a1", Permission.OS_EXECUTE)
    with pytest.raises(PermissionError):
        ps.require("a1", Permission.OS_EXECUTE)


def test_message_bus_request_reply():
    async def _t():
        bus = MessageBus()
        queue = asyncio.Queue()
        bus.subscribe("svc", queue)

        async def worker():
            msg = await queue.get()
            reply = Message(
                sender="svc",
                receiver=msg.sender,
                kind=msg.kind + ".reply",
                payload={"ok": True},
                msg_type=MessageType.REPLY,
                correlation_id=msg.correlation_id,
            )
            await bus.publish(reply)

        task = asyncio.ensure_future(worker())
        rep = await bus.request("cli", "svc", "ping", {})
        await task
        return rep

    rep = run(_t())
    assert rep is not None
    assert rep.payload == {"ok": True}


def test_full_collaboration():
    async def _t():
        api = API()
        api.spawn_default_agents()
        api.start()
        dev = await api.run_task("write fn", AgentCapability.WRITE_CODE, {"action": "write_code"})
        sec = await api.run_task(
            "scan", AgentCapability.SECURITY_SCAN, {"code": "password = 'x'\neval(y)"}
        )
        await api.stop()
        return dev, sec

    dev, sec = run(_t())
    assert dev.result["action"] == "write_code"
    assert sec.result["severity"] == "high"
    assert len(sec.result["vulnerabilities"]) >= 2


def test_agent_factory():
    async def _t():
        api = API()
        from arcanis_agents import AgentSpec, Behavior, Role

        spec = AgentSpec(
            name="X", role=Role.AUTOMATOR,
            capabilities=[AgentCapability.AUTOMATE],
            behavior=Behavior.ECHO,
        )
        agent = api.factory.create(spec)
        api.add_agent(agent, roles=[Role.AUTOMATOR])
        api.start()
        task = await api.run_task("do", AgentCapability.AUTOMATE)
        await api.stop()
        return task

    task = run(_t())
    assert task.result["agent"] == "X"
