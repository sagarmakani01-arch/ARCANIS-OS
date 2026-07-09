# ArcanisBuild

Modern build automation system for Arcanis projects.

## Features

- **Project Configuration** - JSON/YAML build specifications
- **Dependency Tracking** - Automatic graph-based dependency resolution
- **Incremental Builds** - Only rebuild changed files and their dependents
- **Parallel Compilation** - Automatic multi-threaded execution
- **Build Caching** - Content-addressable SHA-256 cache
- **Error Reporting** - Structured diagnostics with file/line references
- **Build Logs** - JSONL structured logging with phase tracking
- **Test Automation** - Automatic test discovery and parallel execution
- **Documentation Generation** - Extracts `///` docblocks from `.arc` source

## Quick Start

```bash
# Initialize a new project
arcanis-build init --create-example

# Build the project
arcanis-build build

# Run tests
arcanis-build test

# Generate documentation
arcanis-build docs

# Clean artifacts
arcanis-build clean
```

## Installation

```bash
# From source
pip install -e .

# Or via pip
pip install arcanis-build
```

## Configuration

Create `arcanis.json` or `build.yaml`:

```json
{
  "project_name": "my-app",
  "version": "1.0.0",
  "targets": [
    {
      "name": "app",
      "type": "executable",
      "sources": ["src/**/*.arc"]
    }
  ]
}
```

## Commands

| Command | Description |
|---------|-------------|
| `build` | Build the project |
| `clean` | Remove build artifacts |
| `test` | Run tests |
| `docs` | Generate documentation |
| `init` | Initialize a new project |
| `cache` | Manage build cache |

## License

MIT
