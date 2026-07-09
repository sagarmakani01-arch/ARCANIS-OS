# Security Module

Multi-layer security for safe AI operation.

## PermissionChecker

- Input safety filtering against prompt injection patterns
- Agent permission levels (NONE, READ, WRITE, EXECUTE, ADMIN)
- Tool-level permission requirements

## SafeExecutor

- Sandboxed action execution
- Blocked command prevention
- Strict mode with agent verification

## AuditLogger

- Comprehensive event logging
- JSONL persistence
- Query by event type and user
- Session-scoped activity tracking
