# ArcanisShell Architecture

**Version:** 0.1.0  
**Last Updated:** 2026-07-08

## Overview

ArcanisShell is a dual-mode shell that unifies traditional command-line interaction with natural-language AI control. The architecture prioritizes safety through a permission system, sandboxing, and audit logging.

## Core Components

### 1. ShellEngine (`engine.py`)

The orchestrator that owns all subsystems and exposes the `execute(raw_input)` API.

**Responsibilities:**
- Parse user input via `CommandParser`
- Route to traditional or NL execution path
- Enforce permission policy and sandbox boundaries
- Execute commands or AI-generated plans
- Log all activity

**Key methods:**
- `execute(raw: str) -> CommandResult`
- `explain(command: str) -> str`
- `suggest() -> list[str]`
- `generate_automation(request: str) -> str`

### 2. CommandParser (`parser.py`)

Routes input to either traditional commands or natural-language processing.

**Routing rules:**
- Input starting with `ai ` or `:` → NL
- Input with known command name → traditional
- Multi-word input without known verb → NL
- Single unknown token → ParseError (unknown command)

### 3. Command Registry (`commands.py`)

Holds traditional command implementations. Each command is a pure function:

```python
def cmd_ls(args: list[str], flags: dict, ctx: CommandContext) -> CommandResult:
    ...
```

**Command categories:**
- File: `ls`, `cat`, `mkdir`, `rm`, `cp`, `mv`, `find`, `tree`
- Process: `ps`, `kill`
- System: `sysinfo`, `pwd`, `echo`, `cd`, `which`, `env`
- Script: `run`

### 4. AI Interface (`ai_interface.py`)

Wraps ArcanisBrain to provide NL capabilities:

- `understand(request, context) -> ExecutionPlan`
- `explain(command) -> Explanation`
- `suggest(context) -> list[str]`
- `generate_automation(request, context) -> str`
- `delegate_to_agents(plan) -> dict`

### 5. Security Subsystem (`security/`)

**PermissionPolicy (`permissions.py`):**
- Auto-approve actions below risk threshold
- Deny/allow lists for specific commands
- Require explicit approval for AI-generated actions

**Sandbox (`sandbox.py`):**
- Filesystem operations restricted to `sandbox_root`
- Optional network and subprocess controls
- Raises `SandboxViolationError` on boundary escape

**ActivityLog (`activity_log.py`):**
- Append-only JSON Lines audit trail
- Records: timestamp, source, action, risk, approval, outcome

### 6. Integration (`integration.py`)

Adapters for Arcanis ecosystem:

- `BrainAdapter`: Plan generation and intent understanding
- `AgentsAdapter`: Task delegation
- `OSAdapter`: Filesystem and security services

Local fallback adapters provide offline behavior when backends are unavailable.

## Data Flow

### Traditional Command Execution

```
User Input
    ↓
CommandParser.parse()
    ↓
PermissionPolicy.check() → PermissionDeniedError
    ↓
PermissionPolicy.needs_approval() → user approval
    ↓
Sandbox.guard_subprocess() → SandboxViolationError
    ↓
Command.fn(args, flags, ctx)
    ↓
ActivityLog.record()
    ↓
CommandResult
```

### Natural Language Execution

```
User Input ("ai organize my project files")
    ↓
CommandParser.parse() → NaturalLanguageRequest
    ↓
AIInterface.understand() → ExecutionPlan
    ↓
ActivityLog.record("planned")
    ↓
User approval (if requires_approval)
    ↓
For each step in plan:
    ├─ PermissionPolicy.check()
    ├─ Sandbox.guard_subprocess()
    ├─ Command.fn()
    └─ ActivityLog.record()
    ↓
CommandResult (combined stdout)
```

## Risk Levels

| Level | Description | Examples |
|-------|-------------|----------|
| `safe` | No side effects | `ls`, `cat`, `pwd`, `sysinfo` |
| `low` | Reversible changes | `mkdir`, `cp`, `mv`, `cd` |
| `medium` | Potentially destructive | `rm`, `run` |
| `high` | System impact | `kill`, `chmod` |
| `critical` | Irreversible | (reserved for future) |

## Configuration

`ShellConfig` fields:
- `sandbox_root`: Filesystem boundary (default: cwd)
- `log_file`: Activity log path (default: `~/.arcanis_shell_activity.log`)
- `ai_backend`: Backend name (`arcanis_brain`, `brain`, or custom)
- `prompt`: REPL prompt string
- `auto_approve_ai`: Skip AI plan approval (default: false)
- `allow_sandbox_writes`: Enable file writes (default: true)
- `enable_network`: Enable network access (default: false)

## Extension Points

### Adding a New Command

1. Implement `cmd_<name>(args, flags, ctx) -> CommandResult`
2. Register in `build_registry()`:
   ```python
   reg.register(Command(
       name="mycmd",
       fn=cmd_mycmd,
       description="...",
       category="...",
       risk=RiskLevel.LOW,
       examples=["mycmd arg1"]
   ))
   ```

### Custom Permission Policy

Subclass `PermissionPolicy` and override `needs_approval()` or `is_denied()`.

### Custom AI Backend

Implement `BrainAdapter` interface and pass to `AIInterface`.

## Security Considerations

1. **Sandbox boundaries** are enforced at the filesystem layer, not just by convention.
2. **AI-generated plans** always require approval unless `auto_approve_ai` is set.
3. **Globs** in commands are expanded safely within the sandbox.
4. **Activity logs** are append-only and include approval status.
5. **No secrets** are stored or logged; sensitive data should be passed via environment.

## Future Work

- Network command sandboxing
- Interactive command editing (history navigation)
- Plugin system for custom commands
- Integration with ArcanisOS security tokens
- Property-based tests for parser and commands