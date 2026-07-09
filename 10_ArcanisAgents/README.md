# ArcanisAgents

A multi-agent collaboration framework for building specialized AI agents that **communicate**, **delegate tasks**, **share memory**, and enforce **permissions**.

## Quick Start

```bash
pip install -e .
python examples/basic_collaboration.py
```

## Architecture

```
            ┌─────────────────────────────┐
            │           API               │
            └───────────────┬─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  ┌─────┴─────┐      ┌──────┴──────┐     ┌──────┴──────┐
  │ MessageBus│<────>│ Orchestrator│<--->│ SharedMemory│
  └───────────┘      └──────┬──────┘     └─────────────┘
                            │
                    ┌───────┴───────────────────┐
                    │  PermissionSystem (enforces)│
        ┌───────────┼───────────┬───────────┬───────────┐
        │           │           │           │           │
   Developer    Research    Automation   Security    System
```

## Components

| Component | Module | Description |
|-----------|--------|-------------|
| `Agent` | `core.agent` | Base class; run loop + messaging |
| `MessageBus` | `core.message_bus` | Pub/sub + request/reply protocol |
| `SharedMemory` | `core.shared_memory` | Scoped key/value store with TTL |
| `PermissionSystem` | `core.permissions` | Capability-based access control |
| `Orchestrator` | `core.orchestrator` | Task delegation and routing |
| `AgentFactory` | `core.factory` | Declarative agent creation |
| `API` | `api` | High-level entry point |

## Built-in Agents

| Agent | Role | Capabilities |
|-------|------|-------------|
| **DeveloperAgent** | developer | Write, review, debug code |
| **ResearchAgent** | researcher | Fetch info, summarize knowledge |
| **AutomationAgent** | automator | Control and run workflows |
| **SecurityAgent** | security | Scan code for vulnerabilities |
| **SystemAgent** | system | Manage OS tasks and status |

## Core Concepts

### Communication Protocol

Agents exchange `Message` objects over the `MessageBus`. Messages have a `kind`, optional `receiver`, a `msg_type` (`EVENT`/`REQUEST`/`REPLY`/`BROADCAST`) and `correlation_id` for request/reply.

```python
reply = await bus.request(sender, to, kind, payload, timeout=10.0)
```

### Task Delegation

`Orchestrator.delegate()` finds a capable agent by `AgentCapability`, sends it a task, and reads the result:

```python
task = await api.run_task("Write login", capability=AgentCapability.WRITE_CODE, data={...})
print(task.result)
```

### Shared Memory

Namespaced key/value store with TTL and change events:

```python
api.remember("ns", "key", value, ttl=300)
value = api.recall("ns", "key")
```

### Permission System

Each agent gets `Role`s granting `Permission`s. Sensitive operations call `require()`:

```python
api.permissions.require(agent_id, Permission.CODE_WRITE)
```

## Creating Custom Agents

```python
from arcanis_agents import Agent, AgentCapability
from arcanis_agents.core.message_bus import Message, MessageType

class MyAgent(Agent):
    capabilities = {AgentCapability.RESEARCH}

    async def handle(self, msg: Message):
        if msg.msg_type is MessageType.REQUEST:
            result = {"done": msg.payload}
            return Message(sender=self.agent_id, receiver=msg.sender,
                          kind="task.result", payload=result)
```

## Agent Creation Framework

Build agents from data:

```python
from arcanis_agents import API, AgentSpec, Behavior, Role, AgentCapability

api = API()
spec = AgentSpec(
    name="Notifier",
    role=Role.AUTOMATOR,
    capabilities=[AgentCapability.AUTOMATE],
    behavior=Behavior.ECHO,
)
agent = api.factory.create(spec)
api.add_agent(agent, roles=[Role.AUTOMATOR])
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/
```

## Project Structure

```
arcanis_agents/
├── __init__.py          # Public API exports
├── api.py               # High-level API facade
├── core/
│   ├── agent.py         # Base Agent class
│   ├── message_bus.py   # Communication protocol
│   ├── shared_memory.py # Shared memory store
│   ├── permissions.py   # Permission system
│   ├── orchestrator.py  # Task delegation
│   └── factory.py       # Agent creation framework
├── agents/
│   ├── base_agent.py    # FunctionalAgent (factory)
│   ├── developer.py     # DeveloperAgent
│   ├── research.py      # ResearchAgent
│   ├── automation.py    # AutomationAgent
│   ├── security.py      # SecurityAgent
│   └── system.py        # SystemAgent
examples/
├── basic_collaboration.py
├── agent_factory.py
└── communication_protocol.py
tests/
└── test_framework.py
```
