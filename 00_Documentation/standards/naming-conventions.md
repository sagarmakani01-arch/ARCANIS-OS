# Naming Conventions

**Path:** `standards/naming-conventions.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Repositories

- Format: `arcanis-<project-name>` (e.g., `arcanis-kernel`, `arcanis-shell`)
- Staging repositories (pre-release): `arcanis-<project-name>-staging`

## Projects

- Project IDs follow the format `XX-name` where `XX` is the numeric index (e.g., `20-kernel`, `40-shell`)
- Project names use lowercase with hyphens

## Source Code

### Rust

| Element | Convention | Example |
|---|---|---|
| Crates | `snake_case` | `arcanis_scheduler` |
| Modules | `snake_case` | `memory_manager` |
| Structs | `PascalCase` | `ProcessControlBlock` |
| Enums | `PascalCase` | `SchedulingPolicy` |
| Traits | `PascalCase` | `Schedulable` |
| Functions | `snake_case` | `schedule_next` |
| Methods | `snake_case` | `process.tick()` |
| Variables | `snake_case` | `next_pid` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_PRIORITY` |
| Statics | `SCREAMING_SNAKE_CASE` | `GLOBAL_SCHEDULER` |
| Type parameters | `PascalCase` short | `T`, `E`, `Pid` |
| Lifetimes | Lowercase short | `'a`, `'ctx` |

### C

| Element | Convention | Example |
|---|---|---|
| Files | `snake_case.c` / `.h` | `memory_map.c` |
| Headers | `snake_case.h` with `#pragma once` | `page_table.h` |
| Types | `snake_case_t` | `page_table_t` |
| Structs | `snake_case` with typedef | `typedef struct {...} page_table_t` |
| Functions | `arc_<module>_<verb>_<noun>()` | `arc_mem_map_page()` |
| Macros | `SCREAMING_SNAKE_CASE` | `PAGE_SIZE` |
| Enums | `snake_case_t` with `ARC_` prefix | `ARC_MEM_READ`, `ARC_MEM_WRITE` |

### Python

| Element | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `build_system.py` |
| Classes | `PascalCase` | `ProjectBuilder` |
| Functions | `snake_case` | `resolve_dependencies()` |
| Variables | `snake_case` | `build_config` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_BUILD_THREADS` |
| Private members | Leading underscore | `_internal_cache` |

### TypeScript

| Element | Convention | Example |
|---|---|---|
| Files | `kebab-case.ts` | `project-builder.ts` |
| Classes | `PascalCase` | `ProjectBuilder` |
| Interfaces | `PascalCase` with `I` prefix | `IProjectConfig` |
| Types | `PascalCase` | `BuildResult` |
| Functions | `camelCase` | `resolveDependencies()` |
| Variables | `camelCase` | `buildConfig` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_BUILD_THREADS` |

## File and Directory Structure

- All lowercase
- Hyphens for multi-word names (no underscores)
- Source files: `src/`
- Tests: `tests/` (integration) or `src/<module>/tests.rs` (unit)
- Configuration: `config/`
- Documentation: `docs/`
- Scripts: `scripts/`

## Branch Naming

- `feat/<short-description>` — New features
- `fix/<short-description>` — Bug fixes
- `docs/<short-description>` — Documentation changes
- `refactor/<short-description>` — Refactoring
- `research/<topic>` — Research branches
- `perf/<short-description>` — Performance improvements

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, `research`

---

*Names are the first form of documentation. Choose them carefully.*
