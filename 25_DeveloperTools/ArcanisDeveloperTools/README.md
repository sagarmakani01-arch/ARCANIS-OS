# Arcanis Developer Tools

A comprehensive suite of developer tools for building Arcanis software. Integrates with ArcanisIDE, ArcanisBuild, and ArcanisLang.

## Tools

| Tool | Description |
|------|-------------|
| **Debugger** | Breakpoint management, stack trace analysis, variable inspection |
| **Profiler** | CPU sampling and memory allocation profiling |
| **Code Analyzer** | Static analysis, linting, complexity metrics |
| **Doc Generator** | JSDoc parsing and markdown/HTML documentation generation |
| **Testing Tools** | Test runner, assertions, mocking framework |
| **Performance Monitor** | Real-time system metrics and alerting |

## Quick Start

```bash
npm install @arcanis/developer-tools
```

### CLI Usage

```bash
# Analyze code
arcanis-dev analyze src/

# Profile an application
arcanis-dev profile --interval 5 app.js

# Generate documentation
arcanis-dev docgen --format html --output docs/ src/

# Run tests
arcanis-dev test tests/

# Start performance monitor
arcanis-dev perfmon --interval 2000

# Launch debugger
arcanis-dev debug --port 9229 app.js
```

### Programmatic Usage

```typescript
import { ArcanisDeveloperTools } from '@arcanis/developer-tools';

const tools = new ArcanisDeveloperTools();

// Analyze source code
const result = await tools.analyzer.analyzeFile('src/index.ts', source);
console.log(`Complexity: ${result.complexity.cyclomaticComplexity}`);

// Profile performance
const profile = await tools.profiler.profile('app');
console.log(`CPU samples: ${profile.cpu.sampleCount}`);

// Generate documentation
const pages = await tools.docgen.generate(sources);
tools.docgen.render(pages);
```

## Integration

- **ArcanisIDE**: Full extension with debugger panel, profiler view, analyzer panel, and test runner UI
- **ArcanisBuild**: Pre/post-build hooks, analysis pipeline with linting, type checking, and coverage
- **ArcanisLang**: Language server features including completions, diagnostics, hover, and go-to-definition

## License

MIT
