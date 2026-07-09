# ArcanisVM Architecture

## Overview

ArcanisVM is a high-performance, stack-based virtual machine for executing Arcanis programs. It features a custom bytecode instruction set, generational garbage collection, and integrated debugging, profiling, and sandboxing subsystems.

## Architecture Layers

```
+--------------------------------------------------+
|                   User Application                 |
+--------------------------------------------------+
|              Public API (arcanis.h)                |
+--------------------------------------------------+
|   Debugger  |  Profiler  |  Sandbox  |  Plugins   |
+--------------------------------------------------+
|              Bytecode Interpreter (VM)             |
+--------------------------------------------------+
|   Compiler  |  Runtime   |  GC       |  Stack     |
+--------------------------------------------------+
|              Memory Manager / Allocator             |
+--------------------------------------------------+
|                    OS Layer                         |
+--------------------------------------------------+
```

## Component Descriptions

### Value System (`value.h/c`)
- Tagged union representation (16 value types)
- NIL, BOOL, INT, FLOAT, STRING, ARRAY, MAP, FUNCTION, NATIVE, CLOSURE, UPVALUE, BOUND_METHOD, CLASS, INSTANCE, MODULE, FOREIGN
- Hash table implementation for maps and name resolution
- String interning via hash-consing

### Bytecode Engine (`bytecode.h/c`)
- 64 opcode instruction set
- Packed instruction format: 8-bit opcode + 24-bit argument
- Disassembler for debugging and inspection
- Line number tracking for source mapping

### Stack Machine (`stack.h/c`)
- Dual-purpose stack: operand stack + call frame storage
- Configurable max depth (16K operands, 1K frames)
- Direct slot access for local variables

### Memory Manager (`memory.h/c`)
- Pluggable allocator interface (default: malloc/free/realloc)
- Object header with type tagging and GC mark bits
- Object allocation with automatic GC trigger

### Garbage Collector (`gc.h/c`)
- Mark-and-sweep collector
- Root set includes stack, global variables, and registered roots
- Gray object marking with type-specific traversal
- Automatic GC trigger when allocation exceeds threshold

### Bytecode Compiler (`compiler.h/c`)
- Recursive descent parser
- Direct bytecode emission (no intermediate AST)
- Operator precedence parsing (Pratt parser)
- Closure compilation with upvalue resolution
- Supports: functions, classes, inheritance, control flow, arrays, maps, imports/exports

### Runtime Library (`runtime.h/c`)
- Built-in native functions: print, input, len, type, toInt, toFloat, toString
- Array operations: push, pop, insert, remove, sort, slice
- Map operations: keys, values, has
- System: clock, exit, assert, error, gc

### Debugger (`debugger.h/c`)
- Breakpoint management (set, remove, list)
- Step modes: into, over, out
- Stack trace and local variable inspection
- Callback hooks for break/step/error events

### Profiler (`profiler.h/c`)
- Per-opcode execution counters
- Total instruction throughput measurement
- Configurable sampling and reporting
- JSON output format for tool integration

### Sandbox (`sandbox.h/c`)
- Instruction count limits
- Memory usage limits
- Call depth limits
- Per-opcode allow/deny rules
- Custom security check callbacks

### Plugin System (`plugin.h/c`)
- Dynamic library loading (.so/.dll)
- Module import resolution via plugins
- Lifecycle hooks: onLoad, onUnload, onImport
- Versioned plugin API

## Memory Model

Values are 16 bytes on 64-bit platforms:
- 8 bytes: type tag + padding
- 8 bytes: value union (int64, double, or pointer)

Objects are heap-allocated with headers:
- 4 bytes: type enum
- 4 bytes: GC mark bit + padding
- 8 bytes: next pointer (linked list)

## Execution Model

1. Source code is compiled to bytecode by the recursive descent parser
2. Bytecode is loaded into an ObjFunction
3. VM wraps it in an ObjClosure and pushes a call frame
4. Main dispatch loop reads opcodes and executes them
5. Function calls push new frames; returns pop them
6. GC runs automatically based on memory pressure

## Design Decisions

- **Stack-based vs Register-based**: Stack-based for simpler implementation and smaller bytecode
- **Tagged values**: Runtime type checking enables safe execution
- **Generational hint**: Simple mark-sweep with generational tuning parameters
- **Direct threading**: Not used in C for portability; switch-based dispatch
