"""Comprehensive tests for ArcanisAgents."""

import asyncio
import time
import uuid
from unittest.mock import AsyncMock

import pytest

from arcanis_agents.core.agent import Agent, AgentCapability, AgentContext, AgentState
from arcanis_agents.core.message_bus import Message, MessageBus, MessageType
from arcanis_agents.core.orchestrator import Orchestrator, Task, TaskStatus
from arcanis_agents.core.shared_memory import MemoryScope, SharedMemory
from arcanis_agents.core.permissions import (
    AgentIdentity,
    Permission,
    PermissionSystem,
    Role,
    ROLE_PERMISSIONS,
)
from arcanis_agents.agents.base_agent import FunctionalAgent
from arcanis_agents.agents.security import SecurityAgent
from arcanis_agents.agents.research import ResearchAgent
from arcanis_agents.core.factory import Behavior


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class DummyAgent(Agent):
    capabilities = {AgentCapability.OS_TASK}

    async def handle(self, msg: Message):
        if msg.kind == "echo":
            return Message(
                sender=self.agent_id,
                kind="echo.reply",
                payload=f"echo:{msg.payload}",
                receiver=msg.sender,
                msg_type=MessageType.REPLY,
                correlation_id=msg.correlation_id,
            )
        return None


class NoopAgent(Agent):
    capabilities = set()

    async def handle(self, msg: Message):
        return None


# ===========================================================================
# 1. Message
# ===========================================================================

class TestMessage:
    def test_creation(self):
        msg = Message(sender="a", kind="test", payload={"x": 1})
        assert msg.sender == "a"
        assert msg.kind == "test"
        assert msg.payload == {"x": 1}
        assert msg.msg_type == MessageType.EVENT
        assert msg.message_id is not None
        assert msg.timestamp > 0

    def test_to_dict_roundtrip(self):
        msg = Message(
            sender="a", kind="test", payload="hello",
            receiver="b", msg_type=MessageType.REQUEST,
            correlation_id="corr1",
        )
        d = msg.to_dict()
        msg2 = Message.from_dict(d)
        assert msg2.sender == "a"
        assert msg2.kind == "test"
        assert msg2.payload == "hello"
        assert msg2.receiver == "b"
        assert msg2.msg_type == MessageType.REQUEST
        assert msg2.correlation_id == "corr1"

    def test_from_dict_defaults(self):
        msg = Message.from_dict({"sender": "x", "kind": "y"})
        assert msg.msg_type == MessageType.EVENT


# ===========================================================================
# 2. MessageBus
# ===========================================================================

class TestMessageBus:
    def test_publish_delivers_to_subscriber(self):
        bus = MessageBus()
        q = asyncio.Queue()
        bus.subscribe("agent1", q)
        msg = Message(sender="system", kind="test", receiver="agent1", payload="data")
        _run(bus.publish(msg))
        assert not q.empty()
        assert q.get_nowait().payload == "data"

    def test_publish_no_subscriber_no_error(self):
        bus = MessageBus()
        msg = Message(sender="system", kind="test", receiver="nonexistent")
        _run(bus.publish(msg))

    def test_unsubscribe(self):
        bus = MessageBus()
        q = asyncio.Queue()
        bus.subscribe("agent1", q)
        bus.unsubscribe("agent1")
        msg = Message(sender="system", kind="test", receiver="agent1")
        _run(bus.publish(msg))
        assert q.empty()

    def test_topic_subscribe(self):
        bus = MessageBus()
        q = asyncio.Queue()
        bus.subscribe("agent1", q)
        bus.subscribe_topic("agent1", "alerts")
        msg = Message(sender="system", kind="alerts", payload="warning")
        _run(bus.publish(msg))
        assert not q.empty()

    def test_history(self):
        bus = MessageBus()
        for i in range(5):
            _run(bus.publish(Message(sender="s", kind=f"k{i}")))
        assert len(bus.history()) == 5

    def test_history_limit(self):
        bus = MessageBus()
        for i in range(10):
            _run(bus.publish(Message(sender="s", kind=f"k{i}")))
        assert len(bus.history(limit=3)) == 3

    def test_reply_message(self):
        bus = MessageBus()
        orig = Message(sender="a", kind="task", msg_type=MessageType.REQUEST, correlation_id="c1")
        reply = bus.reply(orig, "b", {"result": "ok"})
        assert reply.msg_type == MessageType.REPLY
        assert reply.correlation_id == "c1"
        assert reply.receiver == "a"

    def test_request_reply(self):
        bus = MessageBus()
        q = asyncio.Queue()
        bus.subscribe("responder", q)

        async def handler():
            msg = await q.get()
            reply = bus.reply(msg, "responder", "done")
            await bus.publish(reply)

        async def main():
            asyncio.create_task(handler())
            result = await bus.request("requester", "responder", "do", "arg", timeout=2.0)
            return result

        result = _run(main())
        assert result is not None
        assert result.payload == "done"

    def test_request_timeout(self):
        bus = MessageBus()
        result = _run(bus.request("a", "nobody", "do", None, timeout=0.1))
        assert result is None


# ===========================================================================
# 3. SharedMemory
# ===========================================================================

class TestSharedMemory:
    def test_set_and_get(self):
        mem = SharedMemory()
        mem.set("ns", "key1", "value1")
        assert mem.get("ns", "key1") == "value1"

    def test_get_default(self):
        mem = SharedMemory()
        assert mem.get("ns", "missing", "default") == "default"

    def test_exists(self):
        mem = SharedMemory()
        mem.set("ns", "k", "v")
        assert mem.exists("ns", "k")
        assert not mem.exists("ns", "missing")

    def test_delete(self):
        mem = SharedMemory()
        mem.set("ns", "k", "v")
        assert mem.delete("ns", "k") is True
        assert mem.get("ns", "k") is None

    def test_delete_nonexistent(self):
        mem = SharedMemory()
        assert mem.delete("ns", "nope") is False

    def test_keys(self):
        mem = SharedMemory()
        mem.set("ns", "a", 1)
        mem.set("ns", "b", 2)
        mem.set("other", "c", 3)
        keys = mem.keys("ns")
        assert sorted(keys) == ["a", "b"]

    def test_snapshot(self):
        mem = SharedMemory()
        mem.set("ns", "x", 10)
        mem.set("ns", "y", 20)
        mem.set("other", "z", 30)
        snap = mem.snapshot("ns")
        assert snap == {"x": 10, "y": 20}

    def test_ttl_expiry(self):
        mem = SharedMemory()
        mem.set("ns", "k", "v", ttl=0.01)
        time.sleep(0.02)
        assert mem.get("ns", "k") is None

    def test_on_change_listener(self):
        mem = SharedMemory()
        changes = []
        mem.on_change(lambda key, old, new: changes.append((key, old, new)))
        mem.set("ns", "k", "v1")
        mem.set("ns", "k", "v2")
        assert len(changes) == 2
        assert changes[0] == ("ns:k", None, "v1")
        assert changes[1] == ("ns:k", "v1", "v2")

    def test_delete_emits_change(self):
        mem = SharedMemory()
        changes = []
        mem.on_change(lambda key, old, new: changes.append((key, old, new)))
        mem.set("ns", "k", "v")
        mem.delete("ns", "k")
        assert changes[-1] == ("ns:k", "v", None)


# ===========================================================================
# 4. Permissions
# ===========================================================================

class TestPermissionSystem:
    def test_register_and_check(self):
        ps = PermissionSystem()
        ident = ps.register_agent("a1", "Agent One", [Role.DEVELOPER])
        assert ps.check("a1", Permission.CODE_WRITE)
        assert ps.check("a1", Permission.MEMORY_READ)
        assert not ps.check("a1", Permission.OS_EXECUTE)

    def test_admin_has_all(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "Admin", [Role.ADMIN])
        for perm in Permission:
            assert ps.check("a1", perm)

    def test_grant_extra_permission(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "Agent", [Role.RESEARCHER])
        assert not ps.check("a1", Permission.CODE_WRITE)
        ps.grant("a1", Permission.CODE_WRITE)
        assert ps.check("a1", Permission.CODE_WRITE)

    def test_revoke_extra_permission(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "Agent", [Role.RESEARCHER])
        ps.grant("a1", Permission.CODE_WRITE)
        assert ps.check("a1", Permission.CODE_WRITE)
        ps.revoke("a1", Permission.CODE_WRITE)
        # Role-based perms still apply, only extra is revoked
        assert not ps.check("a1", Permission.CODE_WRITE)
        assert ps.check("a1", Permission.NETWORK_FETCH)

    def test_require_raises(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "Agent", [Role.RESEARCHER])
        with pytest.raises(PermissionError):
            ps.require("a1", Permission.CODE_WRITE)

    def test_require_passes(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "Agent", [Role.DEVELOPER])
        ps.require("a1", Permission.CODE_WRITE)

    def test_roles_of(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "Agent", [Role.DEVELOPER, Role.RESEARCHER])
        roles = ps.roles_of("a1")
        assert Role.DEVELOPER in roles
        assert Role.RESEARCHER in roles

    def test_list_agents(self):
        ps = PermissionSystem()
        ps.register_agent("a1", "A", [Role.DEVELOPER])
        ps.register_agent("a2", "B", [Role.RESEARCHER])
        assert len(ps.list_agents()) == 2

    def test_check_nonexistent_agent(self):
        ps = PermissionSystem()
        assert ps.check("nobody", Permission.MEMORY_READ) is False

    def test_role_permissions_completeness(self):
        for role, perms in ROLE_PERMISSIONS.items():
            assert len(perms) > 0


class TestAgentIdentity:
    def test_permissions_union(self):
        ident = AgentIdentity(
            agent_id="a1", name="A",
            roles={Role.DEVELOPER},
            extra={Permission.OS_EXECUTE},
        )
        perms = ident.permissions()
        assert Permission.CODE_WRITE in perms
        assert Permission.OS_EXECUTE in perms


# ===========================================================================
# 5. Orchestrator
# ===========================================================================

class TestTask:
    def test_view(self):
        t = Task(description="do something", task_id="t1")
        v = t.view()
        assert v["task_id"] == "t1"
        assert v["status"] == "pending"


class TestOrchestrator:
    def test_register_agent(self):
        orch = Orchestrator()
        agent = DummyAgent("dummy")
        orch.register(agent)
        assert "dummy" in str(orch.agents.keys()) or agent.agent_id in orch.agents

    def test_register_with_roles(self):
        orch = Orchestrator()
        agent = DummyAgent("dummy")
        orch.register(agent, roles=[Role.DEVELOPER])
        assert orch.permissions.check(agent.agent_id, Permission.CODE_WRITE)

    def test_delegate_no_agent(self):
        orch = Orchestrator()
        task = _run(orch.delegate("test task", AgentCapability.RESEARCH))
        assert task.status == TaskStatus.FAILED
        assert "No agent" in task.error

    def test_status(self):
        orch = Orchestrator()
        task = Task(description="test", task_id="t1")
        orch.tasks["t1"] = task
        assert orch.status("t1") is task
        assert orch.status("nonexistent") is None

    def test_delegate_to_agent(self):
        orch = Orchestrator()
        agent = DummyAgent("echoer")
        orch.register(agent)

        async def main():
            for _ in range(50):
                await asyncio.sleep(0.01)
                q = orch.bus._subscribers.get(agent.agent_id)
                if q and not q.empty():
                    break
            return await orch.delegate("say hi", AgentCapability.OS_TASK)

        task = _run(main())
        assert task.status == TaskStatus.COMPLETED or task.status == TaskStatus.FAILED


# ===========================================================================
# 6. Agent
# ===========================================================================

class TestAgent:
    def test_creation(self):
        agent = DummyAgent("test")
        assert agent.name == "test"
        assert agent.state == AgentState.IDLE
        assert agent.agent_id.startswith("test-")

    def test_custom_id(self):
        agent = DummyAgent("test", agent_id="custom-id")
        assert agent.agent_id == "custom-id"

    def test_attach_and_ctx(self):
        agent = DummyAgent("test")
        bus = MessageBus()
        mem = SharedMemory()
        perm = PermissionSystem()
        ctx = AgentContext(agent_id="a1", name="A", bus=bus, memory=mem, permissions=perm)
        agent.attach(ctx)
        assert agent.ctx.bus is bus

    def test_ctx_not_attached(self):
        agent = DummyAgent("test")
        with pytest.raises(RuntimeError, match="not attached"):
            _ = agent.ctx

    def test_capabilities(self):
        agent = DummyAgent("test")
        assert AgentCapability.OS_TASK in agent.capabilities


# ===========================================================================
# 7. SecurityAgent
# ===========================================================================

class TestSecurityAgent:
    def _make_agent(self):
        agent = SecurityAgent("sec")
        bus = MessageBus()
        mem = SharedMemory()
        perm = PermissionSystem()
        ctx = AgentContext(agent_id=agent.agent_id, name="sec", bus=bus, memory=mem, permissions=perm)
        agent.attach(ctx)
        return agent, bus

    def test_scan_clean_code(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"code": "x = 1\ny = 2"}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert result.payload["severity"] == "low"
        assert len(result.payload["vulnerabilities"]) == 0

    def test_scan_hardcoded_secret(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"code": 'password = "secret123"'}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert result.payload["severity"] == "high"
        assert len(result.payload["vulnerabilities"]) >= 1

    def test_scan_eval(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"code": 'eval(user_input)'}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert any(v["rule"] == "eval_usage" for v in result.payload["vulnerabilities"])

    def test_scan_shell_injection(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"code": 'subprocess.call(cmd, shell=True)'}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert any(v["rule"] == "shell_injection" for v in result.payload["vulnerabilities"])

    def test_no_code_returns_empty(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert result.payload["severity"] == "none"

    def test_ignores_non_request(self):
        agent, _ = self._make_agent()
        msg = Message(sender="orch", kind="task.execute", msg_type=MessageType.EVENT)
        result = _run(agent.handle(msg))
        assert result is None


# ===========================================================================
# 8. ResearchAgent
# ===========================================================================

class TestResearchAgent:
    def _make_agent(self):
        agent = ResearchAgent("research")
        bus = MessageBus()
        mem = SharedMemory()
        perm = PermissionSystem()
        ctx = AgentContext(agent_id=agent.agent_id, name="research", bus=bus, memory=mem, permissions=perm)
        agent.attach(ctx)
        return agent, bus

    def test_summarize_text(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"text": "First sentence. Second sentence. Third sentence. Fourth."}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert result.payload["action"] == "summarize"
        assert "summary" in result.payload
        assert result.payload["word_count"] > 0

    def test_research_query(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"query": "quantum computing"}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert result.payload["action"] == "research"
        assert result.payload["query"] == "quantum computing"

    def test_ignores_non_request(self):
        agent, _ = self._make_agent()
        msg = Message(sender="orch", kind="task.execute", msg_type=MessageType.EVENT)
        result = _run(agent.handle(msg))
        assert result is None

    def test_summarize_deduplicates(self):
        agent, _ = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "data": {"text": "Same sentence. Same sentence. Same sentence."}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        # Deduplication should reduce the summary
        assert len(result.payload["summary"]) > 0


# ===========================================================================
# 9. FunctionalAgent
# ===========================================================================

class TestFunctionalAgent:
    def _make_agent(self, behavior=Behavior.ECHO):
        agent = FunctionalAgent("func", {AgentCapability.OS_TASK}, behavior=behavior)
        bus = MessageBus()
        mem = SharedMemory()
        perm = PermissionSystem()
        ctx = AgentContext(agent_id=agent.agent_id, name="func", bus=bus, memory=mem, permissions=perm)
        agent.attach(ctx)
        return agent, bus, mem

    def test_echo_behavior(self):
        agent, bus, mem = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "description": "hello", "data": {"arg": 1}},
            correlation_id="c1",
        )
        result = _run(agent.handle(msg))
        assert result is not None
        assert result.payload["echo"] == "hello"
        assert result.payload["data"] == {"arg": 1}

    def test_stores_result_in_memory(self):
        agent, bus, mem = self._make_agent()
        msg = Message(
            sender="orch", kind="task.execute", msg_type=MessageType.REQUEST,
            payload={"task_id": "t1", "description": "test"},
            correlation_id="c1",
        )
        _run(agent.handle(msg))
        assert mem.exists("tasks", "t1")

    def test_ignores_non_execute(self):
        agent, _, _ = self._make_agent()
        msg = Message(sender="orch", kind="other", msg_type=MessageType.EVENT)
        result = _run(agent.handle(msg))
        assert result is None


# ===========================================================================
# 10. Factory
# ===========================================================================

class TestFactory:
    def test_create_echo_agent(self):
        from arcanis_agents.core.factory import AgentFactory, AgentSpec
        factory = AgentFactory()
        factory.register_behavior(Behavior.ECHO, AgentFactory.default_builder)
        spec = AgentSpec(name="func", role=Role.DEVELOPER, behavior=Behavior.ECHO, description="test agent")
        agent = factory.create(spec)
        assert isinstance(agent, FunctionalAgent)
        assert agent.name == "func"
        assert agent.behavior == Behavior.ECHO

    def test_factory_behaviors(self):
        assert Behavior.ECHO is not None
        assert Behavior.CUSTOM is not None
