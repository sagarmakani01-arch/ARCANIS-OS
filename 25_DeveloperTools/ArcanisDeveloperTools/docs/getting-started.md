# Getting Started

## Installation

```bash
npm install @arcanis/developer-tools
```

## CLI Usage

The CLI provides six commands:

```bash
npx arcanis-dev <command> [options]
```

### Commands

| Command | Description |
|---------|-------------|
| `debug` | Start the debugger |
| `profile` | Profile CPU and memory |
| `analyze` | Analyze source code |
| `docgen` | Generate documentation |
| `test` | Run tests |
| `perfmon` | Monitor performance |

### Global Options

- `--help` - Display help
- `--version` - Display version

## Programmatic Usage

```typescript
import { 
  Debugger, Profiler, CodeAnalyzer, 
  DocumentationGenerator, TestingTools, PerformanceMonitor,
  ArcanisIDEIntegration, ArcanisBuildIntegration, ArcanisLangIntegration
} from '@arcanis/developer-tools';

// Or use the unified class
import { ArcanisDeveloperTools } from '@arcanis/developer-tools';
const tools = new ArcanisDeveloperTools();
```

## Configuration

Each tool accepts an optional configuration object:

```typescript
const debugger_ = new Debugger({ port: 9229, host: '127.0.0.1' });
const profiler = new Profiler({ samplingInterval: 1, maxSamples: 10000 });
const analyzer = new CodeAnalyzer({ rules: customRules });
const docgen = new DocumentationGenerator({ format: 'html', outputDir: './docs' });
const perfmon = new PerformanceMonitor({ intervalMs: 1000, alertRules: [...] });
```
