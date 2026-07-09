# ArcanisBuild Overview

ArcanisBuild is a modern build automation system designed for Arcanis projects. It manages the full lifecycle: compilation, testing, packaging, and deployment.

## Architecture

```
┌─────────────────────────────────────────────┐
│                 CLI Interface                │
├─────────────────────────────────────────────┤
│              Build Engine                    │
│  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Depend. │ │ Parallel │ │    Cache     │  │
│  │  Graph  │ │ Executor │ │   Subsystem  │  │
│  └─────────┘ └──────────┘ └──────────────┘  │
├─────────────────────────────────────────────┤
│         Developer Features                   │
│  ┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐ │
│  │ Logger │ │ Errors │ │Tests │ │  Docs  │ │
│  └────────┘ └────────┘ └──────┘ └────────┘ │
└─────────────────────────────────────────────┘
```

## Core Concepts

- **Target**: A buildable unit (executable, library, or object)
- **Dependency Graph**: Directs build order and detects changes
- **Build Cache**: Content-addressable cache for incremental builds
- **Parallel Execution**: Automatic multi-threaded compilation
- **Configuration**: JSON or YAML build specification

## Key Features

| Feature | Description |
|---------|-------------|
| Incremental Builds | Only rebuilds changed files and their dependents |
| Parallel Compilation | Uses all available CPU cores by default |
| Build Caching | SHA-256 based content-addressable cache |
| Dependency Tracking | Automatic topological sort of build graph |
| Error Reporting | Structured diagnostics with file/line references |
| Build Logs | JSONL structured logging with phases |
| Test Automation | Automatic test discovery and parallel execution |
| Documentation Gen | Extracts /// docblocks from ArcanisLang source |
