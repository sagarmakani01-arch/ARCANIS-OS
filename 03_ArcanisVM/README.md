# ArcanisVM

A high-performance, secure runtime environment for executing Arcanis programs.

## Features

- **Stack-based bytecode interpreter** with 66 instructions
- **Generational garbage collection** (mark-and-sweep)
- **Recursive descent compiler** with closures and classes
- **Integrated debugger** with breakpoints and stepping
- **Built-in profiler** with opcode-level statistics
- **Sandbox** with memory, instruction, and call depth limits
- **Plugin system** for native code extensions
- **C API** for embedding in host applications

## Quick Start

### Build

Requires a C11 compiler (GCC, Clang, or MSVC):

```bash
# Linux/macOS
make

# Windows (PowerShell)
.\build.ps1
```

### Run

```bash
# Execute a file
./arcanisvm examples/hello.arc

# Evaluate inline code
./arcanisvm --eval "print('Hello, World!')"

# With profiling
./arcanisvm --profile --eval "fun f(n) { if (n<2) return n; return f(n-1)+f(n-2); } print(f(10))"

# With debugger
./arcanisvm --debug examples/oop.arc
```

### Architecture

```
src/
  vm.c/h         - Bytecode interpreter
  bytecode.c/h   - Instruction set & disassembler
  value.c/h      - Value types & hash tables
  stack.c/h      - Operand & call stack
  memory.c/h     - Memory allocator
  gc.c/h         - Garbage collector
  compiler.c/h   - Source-to-bytecode compiler
  runtime.c/h    - Built-in native functions
  debugger.c/h   - Debugger subsystem
  profiler.c/h   - Profiling subsystem
  sandbox.c/h    - Security sandbox
  plugin.c/h     - Plugin loader
  main.c         - Entry point
include/
  arcanis.h      - Public C API
docs/
  architecture.md - System architecture
  bytecode.md    - Instruction set reference
  api.md         - C API documentation
  integration.md - ArcanisOS integration guide
examples/
  hello.arc      - Hello world
  fib.arc        - Fibonacci with memoization
  oop.arc        - Classes and inheritance
  data_structures.arc - Arrays and maps
```

## Arcanis Language

Arcanis is a JavaScript-like scripting language with:

- Dynamic typing (nil, bool, int, float, string, array, map)
- First-class functions with closures
- Prototype-based OOP with single inheritance
- Block scope with lexical scoping
- Standard library (arrays, maps, string ops)

## Integration

Embed ArcanisVM in your C project:

```c
#include <arcanis.h>

ArcanisVM* vm = arcanis_create();
arcanis_execute(vm, "print('hello')", 15);
arcanis_destroy(vm);
```

See `docs/api.md` for full API documentation.

## License

Proprietary - Arcanis LAB
