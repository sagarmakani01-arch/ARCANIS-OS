# 02 — ArcanisCompiler

Compiler infrastructure for the ArcanisLang programming language.

## Purpose

Transforms ArcanisLang source code into executable bytecode for ArcanisVM. Designed with a modular architecture: lexer, parser, semantic analyzer, optimizer, and code generator.

## Status

**Phase: Design** — Awaiting ArcanisLang specification.

## Dependencies

- 01_ArcanisLang
- 24_SharedLibraries
- 25_DeveloperTools
- 26_Testing

## Structure

```
02_ArcanisCompiler/
├── src/           # Compiler implementation
├── tests/         # Test suite
├── examples/      # Compilation examples
├── docs/          # Compiler architecture docs
└── README.md
```
