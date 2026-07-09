# Code Analyzer

The Code Analyzer performs static analysis with linting rules and complexity metrics.

## Features

- **Linting Rules**: Built-in rules (no-console-log, no-unused-vars, max-line-length)
- **Complexity Metrics**: Cyclomatic complexity, cognitive complexity, nesting depth
- **Dependency Extraction**: Detect imports and requires
- **Custom Rules**: Define and register your own lint rules

## Usage

```typescript
import { CodeAnalyzer, defaultRules, analyzeComplexity } from '@arcanis/developer-tools';

const analyzer = new CodeAnalyzer();

// Analyze a single file
const result = await analyzer.analyzeFile('src/index.ts', sourceCode);
console.log(`Issues: ${result.issues.length}`);
console.log(`Complexity: ${result.complexity.cyclomaticComplexity}`);

// Use custom rules
const analyzer2 = new CodeAnalyzer([
  ...defaultRules,
  {
    name: 'no-var',
    severity: 'error',
    check: (source) => {
      // ...
    },
  },
]);
```

## CLI

```bash
arcanis-dev analyze src/
arcanis-dev analyze app.ts lib/
```

## Built-in Rules

| Rule | Severity | Description |
|------|----------|-------------|
| `no-console-log` | warning | Detects console.log/debug/info/warn/error |
| `no-unused-vars` | warning | Detects declared but unused variables |
| `max-line-length` | warning | Warns on lines over 120 characters |
