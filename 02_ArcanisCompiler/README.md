# ArcanisCompiler

A modular, extensible compiler for the **ArcanisLang** programming language, written in TypeScript.

## Features

- **6-stage pipeline**: Lexing, Parsing, AST Generation, Type Checking, Optimization, Code Generation
- **Friendly error reporting**: Clear, location-aware error messages with hints
- **Debug information**: Source maps, variable tracking, and function-level debug info
- **Plugin system**: Extend the compiler with custom hooks at every stage
- **Incremental compilation**: Skip recompilation of unchanged sources
- **Multiple targets**: JavaScript (stable), WASM/LLVM/x86 (extensible)
- **Modular architecture**: Clean separation between all compiler components

## Installation

```bash
npm install
npm run build
```

## Usage

### Command Line

```bash
# Compile an ArcanisLang file to JavaScript
node dist/cli.js examples/hello.arc

# Specify output file
node dist/cli.js examples/hello.arc -o output.js

# List available targets
node dist/cli.js --list-targets

# Enable debug information
node dist/cli.js examples/hello.arc -g

# Disable optimizations
node dist/cli.js examples/hello.arc -O0

# Only run up to type checking
node dist/cli.js examples/hello.arc --emit type_checking
```

### API

```typescript
import { Compiler } from './src/compiler';

const compiler = new Compiler();
compiler.setSource('fun main(): Int { return 42; }', 'example.arc');

const result = compiler.compile({ target: 'js' });

if (result.success) {
  console.log(result.output);
} else {
  for (const diag of result.diagnostics) {
    console.error(`[${diag.severity}] ${diag.message}`);
  }
}
```

## Language Reference

### Types

| Type   | Description    | Literal Examples   |
|--------|---------------|-------------------|
| `Int`  | 64-bit integer | `42`, `-5`, `0`   |
| `Float`| 64-bit float   | `3.14`, `-2.5`    |
| `Bool` | Boolean        | `true`, `false`   |
| `String`| UTF-8 string  | `"hello"`         |
| `Unit` | Void/unit      | `()`              |

### Variables

```arcanis
let x: Int = 10;
let y = 20;           // Type inference
let z: Float = 3.14;
```

### Functions

```arcanis
fun add(a: Int, b: Int): Int {
  return a + b;
}

fun greet(): Unit {
  println("Hello!");
}
```

### Control Flow

```arcanis
if (x > 0) {
  return 1;
} else {
  return 0;
}

while (i < 10) {
  i = i + 1;
}
```

### Built-in Functions

| Function       | Signature                  | Description          |
|---------------|---------------------------|----------------------|
| `print`       | `(String) -> Unit`        | Print without newline|
| `println`     | `(String) -> Unit`        | Print with newline   |
| `printlnInt`  | `(Int) -> Unit`           | Print integer        |
| `readInt`     | `() -> Int`               | Read integer         |
| `readString`  | `() -> String`            | Read string          |
| `intToString` | `(Int) -> String`         | Convert int to string|
| `floatToString`| `(Float) -> String`      | Convert float to string|

## Architecture

```
Source Code
    │
    ▼
┌─────────────┐
│    Lexer     │  Tokenizes source into tokens
├─────────────┤
│   Parser     │  Builds AST from tokens
├─────────────┤
│  TypeChecker │  Validates type correctness
├─────────────┤
│  Optimizer   │  Constant folding, dead code elimination
├─────────────┤
│  CodeGen     │  Generates target code (JS, WASM, LLVM)
└─────────────┘
    │
    ▼
 Target Code
```

### Plugin System

```typescript
const myPlugin: CompilerPlugin = {
  name: 'my-plugin',
  version: '1.0.0',
  hooks: {
    afterTypeChecking(ast) {
      console.log('Type checking complete');
      return ast;
    },
    beforeCodeGeneration(ast) {
      // Transform AST before code generation
      return ast;
    },
  },
};

compiler.getPluginManager().register(myPlugin);
```

## Testing

```bash
npm test
npm run test:coverage
```

## License

MIT
