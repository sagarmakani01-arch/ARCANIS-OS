# API Reference

## ArcanisBrain

```python
brain = ArcanisBrain(config: BrainConfig)
await brain.initialize()
response = await brain.process(user_input: str, user_id: str = "anonymous")
await brain.shutdown()
```

## BrainConfig

| Field | Type | Default |
|-------|------|---------|
| model | str | `gpt-4` |
| temperature | float | `0.7` |
| max_tokens | int | `4096` |
| memory_ttl_seconds | int | `3600` |
| max_long_term_memories | int | `10000` |
| enable_audit | bool | `True` |
| safety_mode | str | `strict` |
| agent_timeout_seconds | int | `300` |
| storage_backend | str | `json` |
| storage_path | str | `~/.arcanis/brain` |

## REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send message, get response |
| POST | `/api/process` | Alias for chat |
| GET | `/api/status` | Brain health and stats |
| GET | `/api/memory` | Query memory context |
| POST | `/api/preferences` | Update user preferences |
| GET | `/api/agents` | List registered agents |
| GET | `/api/audit` | Recent audit logs |

## Core Types

- `Message`, `Task`, `Context`, `AgentIdentity`
- `MemoryItem`, `ReasoningTrace`, `Permission`
- Enums: `MessageRole`, `TaskStatus`, `MemoryType`, `PermissionLevel`
