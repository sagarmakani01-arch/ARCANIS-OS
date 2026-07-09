# 05 — ArcanisBuild

Build automation system for the Arcanis ecosystem.

## Purpose

A build tool that understands code dependencies at a semantic level. Supports incremental builds, cross-compilation, and integration with the package manager.

## Status

**Phase: Design** — Awaiting language and compiler stability.

## Dependencies

- 01_ArcanisLang
- 02_ArcanisCompiler
- 03_ArcanisVM
- 24_SharedLibraries
- 25_DeveloperTools
- 26_Testing

## Structure

```
05_ArcanisBuild/
├── src/           # Build system implementation
├── tests/         # Test suite
├── examples/      # Build configuration examples
├── docs/          # Build system documentation
└── README.md
```
