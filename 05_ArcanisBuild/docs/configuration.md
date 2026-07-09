# Configuration

ArcanisBuild uses `arcanis.json` or `build.yaml` for project configuration.

## Schema

### Root Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `project_name` | string | `"."` | Project name |
| `version` | string | `"0.1.0"` | Project version |
| `compiler` | string | `"arcanisc"` | Compiler command |
| `build_dir` | string | `"build"` | Output directory |
| `cache_dir` | string | `".arcanis-cache"` | Cache directory |
| `parallel_jobs` | int | `0` (auto) | Max parallel jobs |
| `verbose` | bool | `false` | Verbose logging |
| `targets` | array | `[]` | Build targets |
| `test` | object | `{}` | Test configuration |
| `docs` | object | `{}` | Documentation config |

### Target Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Target name |
| `type` | string | `"executable"` | `executable`, `library`, or `object` |
| `sources` | array | `[]` | Source file globs |
| `includes` | array | `[]` | Include directories |
| `dependencies` | array | `[]` | Dependent target names |
| `compiler_flags` | array | `[]` | Compiler flags |
| `linker_flags` | array | `[]` | Linker flags |
| `output` | string | auto | Output path |

### Test Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable test phase |
| `framework` | string | `"arcanist"` | Test framework |
| `source_dir` | string | `"tests"` | Test directory |
| `pattern` | string | `"test_*.arc"` | Test file pattern |
| `timeout` | int | `30` | Test timeout (s) |

### Docs Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable doc generation |
| `output_dir` | string | `"docs/build"` | Output directory |
| `format` | string | `"markdown"` | `markdown` or `json` |
| `source_dir` | string | `"src"` | Source directory |

## Example

```json
{
  "project_name": "my-app",
  "version": "1.0.0",
  "targets": [
    {
      "name": "server",
      "type": "executable",
      "sources": ["src/**/*.arc"],
      "dependencies": ["net-lib"],
      "compiler_flags": ["-O2"]
    }
  ],
  "test": {
    "enabled": true,
    "source_dir": "tests",
    "pattern": "test_*.arc"
  }
}
```
