# ARCANIS Ecosystem Platform

> **v2.0.0** — Intelligence Surface Environment · Python · PySide6

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

### Intelligence Surfaces (12 total)
- **Intelligence Core** — real-time ecosystem metrics and agent status
- **Knowledge Graph** — persistent concept/relation storage with live search
- **Memory Timeline** — chronological event history from database
- **Agent Network** — live agent monitoring with message stream
- **Mission Control** — project and task tracking with progress
- **System Health** — real CPU, memory, disk monitoring via psutil
- **Event Stream** — live feed of all system events and agent messages
- **Project Explorer** — hierarchical tree browser for missions, projects, modules
- **Capability Library** — browse and activate ecosystem capabilities
- **Workspace Map** — zone navigation and workspace overview
- **Project Workspace** — file tree + code editor with syntax highlighting
- **Surface-to-Surface Messaging** — all surfaces communicate via EventBus

### Backend Intelligence
- **SQLite Knowledge Engine** — 10-table persistent database with workspace layout and surface state
- **Multi-Agent System** — 3 agents (Researcher, Analyst, Monitor) with real command processing, autonomous analysis, anomaly detection, and report generation
- **Task Engine** — queue-based work execution with Code, Research, System, Project workers
- **Project Manager** — full project CRUD with tasks, status tracking
- **Agent Intelligence** — agents respond to PA commands (`research`, `analyze`, `report`, `correlate`, `explore`, `status`, `watch`) with real knowledge base operations

### Personal Assistant Mode
- Full-screen command interface with voice input (microphone button)
- Execute system commands, read/write files, generate code
- Learn new concepts, search knowledge, create projects
- Route commands to intelligent agents (`research`, `analyze`, `report`)
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
- `analyze <target>` — Analyze concepts/relations/projects
- `report` — Generate system report from Monitor agent
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
│   ├── database.py         # SQLite persistence layer (10 tables)
│   ├── knowledge.py        # Knowledge engine
│   ├── projects.py         # Project manager
│   ├── agents.py           # Intelligent agent system (3 agents)
│   ├── tasks.py            # Task execution engine (4 workers)
│   └── coordinator.py      # Central coordinator
└── surfaces/
    ├── framework/          # Surface framework
    │   ├── base.py         # BaseSurface, SurfaceFlags, DockPosition
    │   ├── controller.py   # SurfaceController, WorkspaceManager
    │   ├── event_bus.py    # EventBus with 25+ event types
    │   ├── theme.py        # SurfaceTheme
    │   └── plugin_loader.py # Dynamic plugin discovery
    └── library/            # 11 intelligence surface implementations
plugins/                    # Dynamically loaded surface plugins
```

---

## v2.0.0 Release Notes

### Phase 1 — Foundation
- Persistent SQLite database with 8 tables
- 3 background agents with real thread-based execution
- Task engine with 4 worker types
- 10 intelligence surfaces connected to live data
- System monitoring via psutil (CPU, memory, disk)
- Personal Assistant with command execution
- Premium SaaS-style UI with dark sidebar
- PA mode with shutdown persistence

### Phase 2 — Intelligence Ecosystem
- **Agent Intelligence** — 3 agents respond to real commands (`research`, `analyze`, `report`, `correlate`, `explore`, `status`, `watch`) with autonomous background discovery, anomaly detection, and report generation
- **Surface Persistence** — workspace layout, pinning, and surface state saved/restored via SQLite with auto-save and JSON fallback
- **Surface-to-Surface Messaging** — all 11 surfaces emit and react to EventBus events; 17 event types; Workspace Map opens zones on click
- **Project Workspace** — file tree + code editor surface with syntax highlighting, save/new/delete via context menu
- **Voice Input** — microphone button in PA overlay with speech_recognition / Windows SAPI fallback
- **Plugin System** — dynamic discovery and loading of surface plugins from `plugins/` directory
- **12 intelligence surfaces** (11 built-in + dynamic plugins)

---

*Built with PySide6 · Python 3.11 · Windows*
