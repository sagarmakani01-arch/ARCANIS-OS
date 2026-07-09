import pytest
from arcanis_brain import ArcanisBrain, BrainConfig
from arcanis_brain.agents.registry import AgentRegistry
from arcanis_brain.agents.communicator import AgentCommunicator
from arcanis_brain.agents.tools import ToolRegistry
from arcanis_brain.core.types import AgentIdentity, PermissionLevel, Message, MessageRole


@pytest.fixture
def brain():
    return ArcanisBrain(BrainConfig())


class TestAgentRegistry:
    def test_register_and_get(self, brain):
        reg = AgentRegistry(brain)
        agent = AgentIdentity(name="test-agent", capabilities=["search"])
        reg.register(agent)
        assert reg.get("test-agent") is not None
        assert reg.get("nonexistent") is None

    def test_select_for_tool(self, brain):
        reg = AgentRegistry(brain)
        reg.register(AgentIdentity(name="searcher", capabilities=["search"]))
        reg.register(AgentIdentity(name="writer", capabilities=["compose"]))
        selected = reg.select_for_tool("search")
        assert selected.name == "searcher"


class TestAgentCommunicator:
    @pytest.mark.asyncio
    async def test_send_and_receive(self, brain):
        comm = AgentCommunicator(brain)
        msg = Message(role=MessageRole.AGENT, content="hello", agent_id="agent1")
        sent = await comm.send("agent1", msg)
        assert sent is True
        inbox = await comm.receive("agent1")
        assert len(inbox) == 1


class TestToolRegistry:
    @pytest.mark.asyncio
    async def test_builtin_tools(self, brain):
        tools = ToolRegistry(brain)
        result = await tools.execute("reason", {"description": "test"})
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_custom_tool(self, brain):
        tools = ToolRegistry(brain)
        tools.register("custom", lambda p, c: {"result": "custom_result"})
        result = await tools.execute("custom", {})
        assert result["result"] == "custom_result"
