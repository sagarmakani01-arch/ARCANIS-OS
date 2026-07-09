# ArcanisShell Examples

**Version:** 0.1.0

## Interactive Shell

```bash
$ arcanisshell
ArcanisShell 0.1.0 — type 'help' or prefix requests with 'ai '
arcanis ❯ ls
arcanis ❯ sysinfo
system : Windows 10
node   : my-machine
...
arcanis ❯ ai organize my project files

Plan: organize my project files
  I detected an intent to organize project files...
  [0] (low) Create folders under ...
       $ mkdir -p project/src project/docs project/assets
  [1] (medium) Move source files
       $ mv *.py project/src
  [2] (medium) Move docs
       $ mv *.md project/docs
Approve this plan? [y/N] y
```

## Traditional Commands

```bash
# List files
arcanis ❯ ls

# Create nested directories
arcanis ❯ mkdir -p build/logs

# Copy with glob
arcanis ❯ cp *.txt backup/

# Safe removal (recursive required for directories)
arcanis ❯ rm -r old_build

# Search
arcanis ❯ find . --name '*.py'

# Process management
arcanis ❯ ps
arcanis ❯ kill 1234
```

## Natural Language

```bash
# Planning
arcanis ❯ ai organize my project files

# Explanations
arcanis ❯ ai explain rm -r old
Remove files or directories.
Effects:
  - Deletes the target permanently
Risks:
  - Irreversible data loss

# Suggestions
arcanis ❯ ai suggest next steps

# Automation generation
arcanis ❯ ai generate a backup script
# Auto-generated ArcanisShell automation
# Intent: a backup script
mkdir -p backup
cp *.txt backup/
```

## Automation Scripts (`.arc`)

```arc
# deploy.arc — deployment automation
mkdir -p build/release
cp src/*.py build/release/
echo "build complete"
```

Run with:

```bash
arcanis ❯ run deploy.arc
```

## Programmatic Usage

```python
from arcanis_shell import ShellEngine, ShellConfig, PermissionPolicy, RiskLevel
from pathlib import Path

config = ShellConfig(sandbox_root=Path("./work"))
policy = PermissionPolicy(auto_approve_below=RiskLevel.CRITICAL)
engine = ShellEngine(config=config, policy=policy)

# Auto-approve for automation context
engine.approval_fn = lambda plan: True

# Execute natural language
result = engine.execute("ai organize my project files")
if result.success:
    print(result.stdout)

# Generate automation script
script = engine.generate_automation("clean up temp files")
print(script)

# Inspect activity log
for entry in engine.log.recent(10):
    print(entry.timestamp, entry.action, entry.outcome)
```

## Security Configuration

```python
from arcanis_shell import PermissionPolicy, RiskLevel

# Deny destructive commands entirely
policy = PermissionPolicy(
    deny_list={"rm", "kill"},
    auto_approve_below=RiskLevel.SAFE,
    require_approval_for_ai=True,
)

# Restrict AI actions to low-risk operations
engine = ShellEngine(policy=policy)
```

```toml
# ~/.arcanis_shell.toml
sandbox_root = "~/projects"
log_file = "~/.arcanis_shell_activity.log"
auto_approve_ai = false
allow_sandbox_writes = true
enable_network = false
```
