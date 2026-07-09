# ArcanisBrain

The intelligence layer of the Arcanis ecosystem — a modular AI system framework with reasoning, memory, multi-agent orchestration, personality adaptation, and security.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ArcanisBrain                       │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│ Reasoning │  Memory  │  Agents  │Personality│ Security │
│ ┌──────┐ │ ┌──────┐ │ ┌──────┐ │ ┌──────┐ │ ┌──────┐ │
│ │Planner│ │ │ STM  │ │ │Registry│ │Context│ │ │Perms │ │
│ │Decision│ │ │ LTM  │ │ │Comm   │ │ Style │ │ │Sandbox│ │
│ │ Solver │ │ │Prefs │ │ │Delegat│ │Adapt  │ │ │Audit │ │
│ │       │ │ │Knowl.│ │ │ Tools │ │       │ │ │      │ │
│ └──────┘ │ └──────┘ │ └──────┘ │ └──────┘ │ └──────┘ │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

## Modules

- **Reasoning** — Task planning, decision scoring, multi-strategy problem solving
- **Memory** — Short-term (episodic buffer), long-term (persistent JSON), user preferences, knowledge base
- **Agents** — Agent registry, inter-agent messaging, task delegation, extensible tool system
- **Personality** — Context awareness, configurable communication style, user adaptation learning
- **Security** — Input safety filtering, permission-based access control, sandboxed execution, full audit logging

## Quick Start

```python
import asyncio
from arcanis_brain import ArcanisBrain, BrainConfig

async def main():
    config = BrainConfig(storage_path="~/.arcanis/brain")
    brain = ArcanisBrain(config)
    await brain.initialize()

    response = await brain.process("Hello, what can you do?")
    print(response)

    await brain.shutdown()

asyncio.run(main())
```

## API

The `APILayer` provides REST, GraphQL, and WebSocket interfaces:

```python
from arcanis_brain.api import RestAPI, GraphQLAPI, WebSocketAPI
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | `gpt-4` | LLM model identifier |
| `temperature` | `0.7` | Response creativity |
| `memory_ttl_seconds` | `3600` | Short-term memory expiry |
| `safety_mode` | `strict` | Execution safety level |
| `storage_backend` | `json` | Persistence backend |
| `max_concurrent_agents` | `10` | Max parallel agents |
