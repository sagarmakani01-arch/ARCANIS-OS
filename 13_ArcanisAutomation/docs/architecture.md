# Architecture

ArcanisAutomation is built around a single orchestrator, `AutomationEngine`,
surrounded by focused subsystems.

## Components

| Component | Module | Responsibility |
|---|---|---|
| **Engine** | `core/engine.py` | Orchestrates create/trigger/run, dependency chaining, persistence |
| **Models** | `core/models.py` | Workflow format: `Workflow`, `Step`, `Trigger`, `Schedule`, `Permission` |
| **Scheduler** | `scheduler/loop.py` | Background thread firing workflows by cron/interval/timestamp |
| **Security** | `security/guard.py` | Permission checks, path sandboxing, safe shell, audit log |
| **Actions** | `actions/builtins.py` | Built-in handlers (file, app, data, research, shell, http) |
| **AI** | `ai/capabilities.py` | Generate, optimize, and failure-detect workflows |
| **API** | `api/` | Python facade + Flask REST API |
| **CLI** | `cli.py` | `arcanis-automation` command |

## Execution Model

1. A workflow is triggered (manual, schedule, event, webhook, or condition).
2. Steps are executed in dependency waves honoring `run_after`.
3. Each step is permission-checked, then dispatched to its handler.
4. Results are collected, captured values interpolated into later steps,
   and the outcome is recorded in the audit log.
5. `on_failure` controls whether a failure stops, continues, or retries.

## Data Flow

```
trigger ─▶ Engine.run ─▶ dependency waves ─▶ handler(s) ─▶ ExecutionResult
                              │                      │
                       interpolate {{vars}}    permission check (Security)
                              │
                       AuditLogger.record
```

## Security Model

- Every action carries a permission `scope` (e.g. `file.*`, `app.launch`).
- `DENY` rules take precedence over grants.
- In `safe_mode`, filesystem paths are confined to allowed roots and shell
  operators (`;`, `&&`, `|`, `>`, `$`, backticks) are blocked.
- All decisions and executions are written to an append-only `audit.log`.

## Extensibility

- Register custom actions: `engine.register_action("my.action", handler)`.
- Subscribe to engine events: `engine.on_event("workflow.finished", cb)`.
- Plug in an AI provider via `config.ai_provider` (local / openai / custom).
