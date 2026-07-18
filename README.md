# ARCANIS Ecosystem Platform

> **v1** — Intelligence Surface Environment · Python · PySide6

```
     _                _                 ____   ___   ____
    / \   _ __   __ _| |_ ___  _ __   |  _ \ / _ \ / ___|
   / _ \ | '_ \ / _` | __/ _ \| '__|  | |_) | | | | |
  / ___ \| | | | (_| | || (_) | |     |  __/| |_| | |___
 /_/   \_\_| |_|\__,_|\__\___/|_|     |_|    \___/ \____|
```

ARCANIS is an **intelligence surface environment** — not an OS, not a dashboard, not an AI app. A premium SaaS-style ecosystem platform with real persistent intelligence, multi-agent coordination, knowledge management, and project tracking.

---

## Features

### Ecosystem Desktop
- Premium SaaS-style interface with header navigation, desktop icons, and status bar
- **Personal Assistant** mode — voice-inspired command interface with full system access
- Dark sidebar workspace navigation with enterprise branding

### Intelligence Surfaces
- **Intelligence Core** — real-time ecosystem metrics and agent status
- **Knowledge Graph** — persistent concept/relation storage with live search
- **Memory Timeline** — chronological event history from database
- **Agent Network** — live agent monitoring with message stream
- **Mission Control** — project and task tracking with progress
- **System Health** — real CPU, memory, disk monitoring via psutil
- **Event Stream** — live feed of all system events and agent messages

### Backend Intelligence
- **SQLite Knowledge Engine** — 8-table persistent database with concepts, relations, memories
- **Multi-Agent System** — 3 background agents (Researcher, Analyst, Monitor) doing real work
- **Task Engine** — queue-based work execution with Code, Research, System, Project workers
- **Project Manager** — full project CRUD with tasks, status tracking

### Personal Assistant Mode
- Full-screen command interface
- Execute system commands, read/write files, generate code
- Learn new concepts, search knowledge, create projects
- Background agents process tasks asynchronously
- Persistent across shutdowns — resumes automatically

---

## Quick Start

```bash
# Requirements
pip install PySide6 psutil

# Launch
python demo.py
```

Commands available in desktop:
- `python demo.py` — Launch the ecosystem

From the Personal Assistant (click ⚡PA in status bar or press Ctrl+Shift+P):
- `stats` — Show ecosystem statistics
- `agents` — List running agents
- `projects` — Show project status
- `learn <concept>` — Teach the knowledge base
- `search <query>` — Search concepts
- `generate <type> <name>` — Generate files (script/html/markdown)
- `research <topic>` — Research a topic via background agent
- `code read/write <path>` — Read/write files via agent
- `system info/run <cmd>` — System information or command execution
- `open <file>` — Open a file or application

---

## Project Structure

```
experience/
├── desktop.py              # Main ecosystem desktop UI
├── engine.py               # Launch bridge
├── ecosystem/
│   ├── database.py         # SQLite persistence layer
│   ├── knowledge.py        # Knowledge engine
│   ├── projects.py         # Project manager
│   ├── agents.py           # Background agent system
│   ├── tasks.py            # Task execution engine
│   └── coordinator.py      # Central coordinator
└── surfaces/
    ├── framework/          # Surface framework (BaseSurface, EventBus, WorkspaceManager)
    └── library/            # 10 intelligence surface implementations
```

---

## v1 Release Notes

- Persistent SQLite database with 8 tables
- 3 background agents with real thread-based execution
- Task engine with 4 worker types
- 10 intelligence surfaces connected to live data
- System monitoring via psutil (CPU, memory, disk)
- Personal Assistant with command execution
- Premium SaaS-style UI with dark sidebar
- PA mode with shutdown persistence

---

*Built with PySide6 · Python 3.11 · Windows*
