# ArcanisShell

**Version:** 0.1.0  
**Status:** Alpha  
**Project ID:** 12-ArcanisShell

A next-generation shell that combines traditional command execution with natural-language AI control. ArcanisShell lets you work with familiar shell commands or describe your intent in plain English.

## Quick Start

```bash
# Install from source
pip install -e .

# Launch interactive shell
arcanisshell

# Or run a single command
arcanisshell -c "ls -la"

# Use natural language
arcanisshell -c "ai organize my project files"
```

## Features

### Traditional Shell
- **File commands**: `ls`, `cat`, `mkdir`, `rm`, `cp`, `mv`, `find`, `tree`
- **Process management**: `ps`, `kill`
- **System info**: `sysinfo`, `pwd`, `echo`, `cd`, `which`, `env`
- **Script execution**: `run` executes `.arc` automation scripts

### AI Shell
- **Natural language commands**: `ai organize my project files`
- **Task planning**: AI generates a safe, reviewable plan before executing
- **Command suggestions**: Get context-aware suggestions
- **Explanations**: `ai explain rm -r` shows effects and risks
- **Automation generation**: Generate `.arc` scripts from descriptions

### Security
- **Permission system**: Configurable allow/deny lists and risk levels
- **Sandboxing**: Filesystem operations restricted to a root directory
- **Activity logs**: All actions are logged for audit

## Architecture

```
arcanis_shell/
├── __init__.py      # Public API
├── main.py          # CLI entry point
├── config.py        # Runtime configuration
├── errors.py        # Exception hierarchy
├── types.py         # Data models (plans, results, etc.)
├── parser.py        # Input routing (traditional vs NL)
├── commands.py      # Traditional command implementations
├── script.py        # .arc script execution
├── ai_interface.py  # NL understanding, planning, suggestions
├── integration.py   # ArcanisBrain/Agents/OS adapters
└── security/
    ├── __init__.py
    ├── permissions.py  # Policy enforcement
    ├── sandbox.py      # Filesystem boundaries
    └── activity_log.py # Audit trail
```

### Execution Flow

**Traditional command:**
```
user input → parser → permission check → sandbox check → execute → log
```

**Natural language:**
```
user input → parser → AI.understand() → build plan → request approval → execute steps → log
```

Each step in an AI-generated plan is re-checked against permissions and sandbox before execution.

## Command Reference

### Traditional Commands

| Command | Description | Risk |
|---------|-------------|------|
| `ls [path]` | List directory contents | safe |
| `cat file` | Print file contents | safe |
| `mkdir -p path` | Create directories | low |
| `rm [-r] path` | Remove files/directories | medium |
| `cp src dst` | Copy files | low |
| `mv src dst` | Move/rename files | low |
| `find [--name pattern]` | Search files | safe |
| `tree [path]` | Show directory tree | safe |
| `ps` | List processes | safe |
| `kill pid` | Terminate process | high |
| `sysinfo` | System information | safe |
| `pwd` | Print working directory | safe |
| `cd path` | Change directory | safe |
| `run script.arc` | Execute automation script | medium |

### Natural Language

Prefix any request with `ai ` or use `:` to force NL routing:

```
ai organize my project files
ai explain what does rm -r do
ai suggest next steps
ai generate a deployment script
```

## Configuration

Create `~/.arcanis_shell.toml`:

```toml
sandbox_root = "~/projects"
log_file = "~/.arcanis_shell_activity.log"
ai_backend = "arcanis_brain"
prompt = "arcanis ❯"
auto_approve_ai = false
allow_sandbox_writes = true
enable_network = false
```

## Integration with Arcanis Ecosystem

ArcanisShell integrates with:
- **ArcanisBrain**: For advanced planning and intent understanding
- **ArcanisAgents**: For task delegation
- **ArcanisOS**: For filesystem and security services

When the real backends are unavailable, the shell uses local adapters that provide deterministic offline behavior.

## Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=arcanis_shell
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black src/ tests/

# Type check
mypy src/

# Lint
ruff check src/ tests/
```

## License

All rights reserved. ArcanisLabs — Sagar Makani.