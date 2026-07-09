# Arcanis Developer Tools Documentation

Welcome to the Arcanis Developer Tools documentation. This suite provides six integrated tools for building Arcanis software.

## Contents

- [Getting Started](getting-started.md)
- [Debugger](debugger.md)
- [Profiler](profiler.md)
- [Code Analyzer](analyzer.md)
- [Documentation Generator](docgen.md)
- [Testing Tools](testing.md)
- [Performance Monitor](perfmon.md)

## Architecture

The tools are designed as modular components under a unified `ArcanisDeveloperTools` class, with a CLI interface and integration points for ArcanisIDE, ArcanisBuild, and ArcanisLang.

```
src/
  debugger/     - Breakpoint manager, stack trace parser
  profiler/     - CPU sampling, memory allocation tracking
  analyzer/     - Linting rules, complexity analysis
  docgen/       - JSDoc parser, markdown/HTML renderer
  testing/      - Test runner, assertions, mocking
  perfmon/      - Metrics collection, alerting rules
  integration/  - IDE, Build, and Language adapters
```

## Requirements

- Node.js 18+
- TypeScript 5+
