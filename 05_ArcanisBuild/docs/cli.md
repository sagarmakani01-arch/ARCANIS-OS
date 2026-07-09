# CLI Reference

## Usage

```
arcanis-build <command> [options]
```

## Commands

### `build`

Build the project.

```
arcanis-build build [options] [targets...]
```

| Option | Description |
|--------|-------------|
| `-c, --config PATH` | Path to build config |
| `-j, --jobs N` | Number of parallel jobs |
| `-v, --verbose` | Verbose output |
| `--no-test` | Skip tests |
| `--no-docs` | Skip documentation |

### `clean`

Remove build artifacts and cache.

```
arcanis-build clean [options]
```

### `test`

Run tests.

```
arcanis-build test [options]
```

| Option | Description |
|--------|-------------|
| `--source-dir DIR` | Test source directory (default: `tests`) |
| `--pattern PAT` | Test file pattern (default: `test_*.arc`) |
| `--timeout SEC` | Test timeout (default: `30`) |
| `--serial` | Run tests sequentially |

### `docs`

Generate documentation from source comments.

```
arcanis-build docs [options]
```

| Option | Description |
|--------|-------------|
| `--source-dir DIR` | Source directory (default: `src`) |
| `--output-dir DIR` | Output directory (default: `docs/build`) |
| `--format FMT` | Output format: `markdown` or `json` |

### `init`

Initialize a new project structure.

```
arcanis-build init [options]
```

| Option | Description |
|--------|-------------|
| `-n, --name NAME` | Project name |
| `-c, --config PATH` | Config file to create |
| `--create-example` | Create example source file |

### `cache`

Manage build cache.

```
arcanis-build cache [options]
```

| Option | Description |
|--------|-------------|
| `-c, --config PATH` | Path to build config |
| `--clear` | Clear the cache |

### `--version`

Show version information.

```
arcanis-build --version
```
