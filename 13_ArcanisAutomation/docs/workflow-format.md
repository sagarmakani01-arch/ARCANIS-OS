# Workflow Format

A workflow is a JSON document validated by `arcanis_automation.core.models`.

## Top-level fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Auto-generated if omitted (`wf_…`) |
| `name` | string | **Required** |
| `description` | string | Human description |
| `status` | enum | `draft` / `active` / `paused` / `archived` |
| `triggers` | list[Trigger] | What may start the workflow |
| `steps` | list[Step] | Ordered action nodes |
| `schedule` | Schedule | Time-based firing (usually with a `schedule` trigger) |
| `permissions` | list[Permission] | Allowed action scopes |
| `owner` | string | Owning user / agent |
| `tags` | list[string] | Free-form labels |
| `metadata` | object | Arbitrary extra data |

## Trigger

```json
{ "type": "schedule | manual | event | webhook | condition", "spec": {} }
```

- `schedule` — paired with a `schedule` block.
- `event` — `spec.name` matches `engine.emit_event(name, data)`.
- `condition` — `spec.expression` evaluated at poll time (reserved).

## Schedule

```json
{ "cron": "0 2 * * *", "interval_seconds": 60, "at_timestamp": 1700000000, "timezone": "UTC" }
```

At least one of `cron`, `interval_seconds`, or `at_timestamp` may be set.
`cron` requires the optional `croniter` dependency; otherwise it falls back to
+60s so the engine remains dependency-free.

## Step

```json
{
  "id": "organize",
  "name": "Organize files",
  "action": { "action": "file.organize", "params": { "source": "~/Downloads" }, "timeout": 30, "retries": 0 },
  "run_after": ["previous_step"],
  "on_failure": "stop | continue | retry",
  "condition": null,
  "captures": { "path": "map.downloads" }
}
```

- `run_after` — step ids that must succeed first (dependency chaining).
- `captures` — map of variable name → dot-path into the step output, made
  available to later steps via `{{var}}` interpolation.
- `on_failure` — `stop` aborts downstream; `continue` proceeds; `retry`
  re-runs up to `action.retries` times.

## Permission

```json
{ "level": "deny | read | execute | admin", "scope": "file.*" }
```

`scope` supports exact (`app.launch`) or prefix (`file.*`) matching.
`DENY` always wins.

## Built-in Action Kinds

| Kind | Purpose |
|---|---|
| `file.organize` / `file.move` / `file.copy` / `file.delete` | File organization |
| `app.launch` / `app.kill` / `app.focus` | Application control |
| `data.transform` / `data.aggregate` | Data processing |
| `research.query` / `research.fetch` | Research workflows |
| `shell` / `http` / `notify` | Generic utilities |
