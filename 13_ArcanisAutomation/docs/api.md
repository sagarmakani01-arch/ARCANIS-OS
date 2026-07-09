# API Reference

## Python API — `Automation`

```python
from arcanis_automation import Automation

auto = Automation()                       # or Automation(AutomationConfig(...))
wid = auto.create(name, steps, **meta)    # create + persist a workflow
results = auto.run(wid, context={})       # trigger & execute
wf = auto.get(wid)                        # fetch a workflow
wfs = auto.list()                         # list all workflows
wid = auto.generate("description…")       # AI-generated workflow
auto.start() / auto.stop()                # start/stop the scheduler
```

## Engine-level — `AutomationEngine`

| Method | Description |
|---|---|
| `create_workflow(dict)` | Build & persist a workflow from a dict |
| `get_workflow(id)` / `list_workflows()` | Read workflows |
| `update_workflow(id, dict)` / `delete_workflow(id)` | Mutate workflows |
| `trigger(id, event=None)` | Run a workflow now |
| `emit_event(name, data)` | Dispatch all `event` triggers named `name` |
| `register_action(kind, fn)` | Add a custom action handler |
| `on_event(name, fn)` | Subscribe to engine events |
| `generate_workflow(desc)` | AI generate workflow |
| `optimize_workflow(id)` | AI optimize workflow |
| `detect_failures(id)` | Analyze last run results |
| `start()` / `stop()` | Scheduler control |
| `audit.read(limit)` | Read the audit log |

## REST API (Flask, optional)

| Method & Path | Body | Result |
|---|---|---|
| `GET /health` | — | `{status, workflows}` |
| `GET /workflows` | — | list of workflows |
| `POST /workflows` | workflow JSON | created workflow |
| `GET /workflows/<id>` | — | one workflow |
| `DELETE /workflows/<id>` | — | deleted id |
| `POST /workflows/<id>/trigger` | context JSON | execution results |
| `POST /generate` | `{description}` | AI-generated workflow |
| `POST /workflows/<id>/optimize` | — | optimized workflow |
| `GET /workflows/<id>/failures` | — | failure report |
| `POST /events` | `{name, data}` | dispatched event |
| `GET /audit?limit=200` | — | audit log lines |

## CLI

```bash
arcanis-automation list
arcanis-automation create workflow.json
arcanis-automation run <id> --context '{}'
arcanis-automation generate "organize downloads and notify me"
arcanis-automation optimize <id>
arcanis-automation failures <id>
arcanis-automation serve
```
