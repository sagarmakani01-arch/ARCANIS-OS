# Compiler Architecture

## Overview

ArcanisCompiler follows a classic multi-stage compiler design with a modular plugin architecture. Each stage is a separate, testable component.

## Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        Source Code                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Lexer                                                  │
│  Input:  Source string                                           │
│  Output: Token[]                                                 │
│  Errors: Unexpected characters, unterminated strings             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Parser                                                 │
│  Input:  Token[]                                                 │
│  Output: AST (Program)                                           │
│  Errors: Syntax errors, unexpected tokens                        │
│  Note:   Combines parsing and AST generation in one pass        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Type Checker                                           │
│  Input:  AST (Program)                                           │
│  Output: Annotated AST (with resolved types)                     │
│  Errors: Type mismatches, undefined variables/functions          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Optimizer                                              │
│  Input:  Annotated AST                                           │
│  Output: Optimized AST                                           │
│  Passes: Constant folding, dead code elimination,                │
│          identity simplification, double negation elimination     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: Code Generator                                         │
│  Input:  Optimized AST                                           │
│  Output: Target code (e.g., JavaScript)                          │
│  Targets: js (stable), wasm, llvm, x86 (planned)                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Output Code                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Core Types (`src/types.ts`)
- Token kinds, AST node kinds, operator enums
- Type system representation (Type class)
- Source locations and ranges
- Diagnostic and severity types

### 2. Error Reporting (`src/error.ts`)
- `ErrorReporter`: Collects and formats diagnostics
- `CompilerError`: Error with stage and location information
- Friendly formatting with source line display and hints

### 3. Debug Information (`src/debug.ts`)
- `DebugInfoBuilder`: Collects line mappings, variable info, function info
- Source-to-output mapping for debugging tools

### 4. Plugin System (`src/plugin.ts`)
- `PluginManager`: Register/unregister plugins
- Hooks for every compiler stage (before/after)
- Plugin chain: output of one plugin feeds into the next
- Error isolation: plugin failures don't crash the compiler

### 5. Incremental Compilation (`src/incremental.ts`)
- `IncrementalCompiler`: SHA-256 content hashing
- Dependency tracking for cache invalidation
- Persistent cache file (`.arcanis-cache.json`)

### 6. Target System (`src/targets/target.ts`)
- `Target` interface: name, description, generate method
- Extensible: new targets implement the interface
- Registry: `listTargets()` and `getTarget(name)`

## Plugin Hook Points

| Hook                   | Description                          |
|------------------------|--------------------------------------|
| `beforeStage`          | Before any stage runs                |
| `afterStage`           | After any stage runs                 |
| `beforeLexing`         | Transform source before lexing       |
| `afterLexing`          | Transform tokens after lexing        |
| `beforeParsing`        | Transform tokens before parsing      |
| `afterParsing`         | Transform AST after parsing          |
| `beforeTypeChecking`   | Transform AST before type checking   |
| `afterTypeChecking`    | Transform AST after type checking    |
| `beforeOptimization`   | Transform AST before optimization    |
| `afterOptimization`    | Transform AST after optimization     |
| `beforeCodeGeneration` | Transform AST before codegen         |
| `afterCodeGeneration`  | Transform output after codegen       |
| `transformError`       | Transform errors before reporting    |

## Error Recovery

- **Lexer**: Reports errors and continues tokenizing
- **Parser**: Reports errors and continues parsing (panic recovery)
- **Type Checker**: Reports errors and continues checking
- The compiler always attempts to process the entire source

## Future Targets

The target system is designed for extensibility:
1. **WASM**: WebAssembly bytecode output
2. **LLVM**: LLVM IR output for native compilation
3. **x86**: Direct x86-64 assembly output

Each new target requires implementing the `Target` interface and registering it in `targets/target.ts`.
