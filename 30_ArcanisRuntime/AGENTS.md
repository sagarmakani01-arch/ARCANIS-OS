# ArcanisRuntime Agent Guide

## Build/Test/Lint Commands
- Build: `make` (requires i686-elf-gcc cross compiler)
- Clean: `make clean`
- Run tests: `make test` or compile `tests/test_runtime.c` and link against `build/libarcanis_runtime.a`

## Code Style
- C99 freestanding (no libc)
- All public functions prefixed with `arc_`
- All public types prefixed with `arc_`
- Header guards: `#ifndef ARCANIS_MODULE_H`
- 4-space indentation, K&R brace style
- No comments unless explaining non-obvious behavior
- Error returns: NULL for pointers, negative for status codes

## Architecture
- `include/arcanis/` — Public API headers
- `src/string.c` — Freestanding string/memory utilities
- `src/pmm.c` — Physical memory manager (bitmap-based, 4KB blocks)
- `src/vmm.c` — Virtual memory manager (2-level page tables)
- `src/heap.c` — Kernel heap (first-fit, splitting, coalescing)
- `src/runtime.c` — Initialization orchestrator

## Key Conventions
- PMM allocates physical 4KB frames
- VMM maps virtual addresses to physical frames
- Heap provides malloc-like interface on top of physical pages
- String functions are pure — no system calls, no side effects
- All memory returned is aligned to at least 4 bytes
