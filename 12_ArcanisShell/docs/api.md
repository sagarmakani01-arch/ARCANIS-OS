# ArcanisShell API Reference

**Version:** 0.1.0

## Public API (`arcanis_shell`)

### `ShellEngine`

The main runtime class.

```python
class ShellEngine:
    def __init__(
        self,
        config: ShellConfig | None = None,
        registry: Registry | None = None,
        policy: PermissionPolicy | None = None,
        ai: AIInterface | None = None,
        approval_fn: Callable[[ExecutionPlan], bool] | None = None,
    ) -> None: ...
```

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `execute` | `(raw: str)` | `CommandResult` | Run a command or NL request |
| `explain` | `(command: str)` | `str` | Explain a command's effects/risks |
| `suggest` | `()` | `list[str]` | Context-aware suggestions |
| `generate_automation` | `(request: str)` | `str` | Generate `.arc` script |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `config` | `ShellConfig` | Runtime configuration |
| `registry` | `Registry` | Available commands |
| `policy` | `PermissionPolicy` | Permission policy |
| `sandbox` | `Sandbox` | Filesystem boundary |
| `log` | `ActivityLog` | Audit trail |
| `cwd` | `Path` | Current working directory |
| `ai` | `AIInterface` | AI front end |

### `CommandResult`

```python
@dataclass
class CommandResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
```

### `ExecutionPlan`

```python
class ExecutionPlan(BaseModel):
    intent: str
    summary: str
    steps: list[PlanStep]
    requires_approval: bool = True

    @property
    def max_risk(self) -> RiskLevel: ...
```

### `RiskLevel`

```python
class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### `AIInterface`

```python
class AIInterface:
    def understand(self, request: str, context: dict) -> ExecutionPlan: ...
    def explain(self, command: str) -> Explanation: ...
    def suggest(self, context: dict) -> list[str]: ...
    def generate_automation(self, request: str, context: dict) -> str: ...
    def delegate_to_agents(self, plan: ExecutionPlan) -> dict: ...
```

### `PermissionPolicy`

```python
@dataclass
class PermissionPolicy:
    auto_approve_below: RiskLevel = RiskLevel.LOW
    require_explicit_approval: set[RiskLevel] = {MEDIUM, HIGH, CRITICAL}
    deny_list: set[str] = set()
    allow_list: set[str] = set()
    require_approval_for_ai: bool = True

    def needs_approval(self, command, risk, source) -> bool: ...
    def check(self, command, risk, source) -> None: ...  # raises PermissionDeniedError
```

### `Sandbox`

```python
class Sandbox:
    def __init__(
        self,
        root: Path,
        allow_network: bool = False,
        allow_subprocess: bool = True,
        allow_write: bool = True,
    ) -> None: ...

    def is_inside(self, path: Path) -> bool: ...
    def require_inside(self, path: Path) -> Path: ...  # raises SandboxViolationError
    def guard_write(self) -> None: ...
    def guard_network(self) -> None: ...
    def guard_subprocess(self, source, risk) -> None: ...
```

### `ActivityLog`

```python
class ActivityLog:
    def __init__(self, path: Path | None = None) -> None: ...
    def record(self, source, action, risk, approved, outcome, detail="") -> ActivityEntry: ...
    def recent(self, limit: int = 50) -> list[ActivityEntry]: ...
```

### `CommandParser`

```python
class CommandParser:
    def __init__(
        self,
        known_commands: set[str] | None = None,
        aliases: dict[str, str] | None = None,
    ) -> None: ...

    def parse(self, raw: str) -> TraditionalCommand | NaturalLanguageRequest: ...
    def register(self, name: str) -> None: ...
```

### `ShellConfig`

```python
@dataclass
class ShellConfig:
    sandbox_root: Path = Path.cwd()
    history_file: Path = Path.home() / ".arcanis_shell_history"
    log_file: Path | None = Path.home() / ".arcanis_shell_activity.log"
    ai_backend: str = "arcanis_brain"
    prompt: str = "arcanis ❯"
    auto_approve_ai: bool = False
    allow_sandbox_writes: bool = True
    enable_network: bool = False

    @classmethod
    def default(cls) -> "ShellConfig": ...
    @classmethod
    def from_file(cls, path: Path) -> "ShellConfig": ...
```

### Errors

| Error | Raised when |
|-------|-------------|
| `PermissionDeniedError` | Action on deny list |
| `SandboxViolationError` | Filesystem access outside sandbox |
| `CommandNotFoundError` | Unknown command |
| `ParseError` | Input cannot be parsed |
| `PlanRejectedError` | User rejects AI plan |
| `AIUnavailableError` | AI backend unreachable |
| `ShellRuntimeError` | Generic internal failure |

## CLI

```bash
arcanisshell [options]

Options:
  -c, --command CMD    Execute a single command and exit
  --config PATH        Path to TOML config file
  --sandbox-root PATH  Restrict filesystem to directory
  --version            Show version
```

### Programmatic Usage

```python
from arcanis_shell import ShellEngine, ShellConfig, PermissionPolicy, RiskLevel

config = ShellConfig(sandbox_root=Path("./work"))
policy = PermissionPolicy(auto_approve_below=RiskLevel.CRITICAL)
engine = ShellEngine(config=config, policy=policy)
engine.approval_fn = lambda plan: True  # auto-approve for automation

result = engine.execute("ai organize my project files")
print(result.stdout)

script = engine.generate_automation("deploy to staging")
print(script)
```